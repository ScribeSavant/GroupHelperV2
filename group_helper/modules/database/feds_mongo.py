import threading
from pymodm import MongoModel
from pymodm.fields import CharField, DictField, BooleanField
from pymongo import ASCENDING


class Federations(MongoModel):
    owner_id = CharField(max_length=14)
    fed_name = CharField()
    fed_id = CharField()
    fed_rules = CharField()
    fed_users = DictField()
  
    class Meta:
        final = True
        collection_name = 'feds'


class ChatF(MongoModel):
    chat_id = CharField(max_length=14)
    fed_id = CharField()
  
    class Meta:
        final = True
        collection_name = 'chat_feds'


class BansF(MongoModel):
    fed_id = CharField()
    user_id = CharField(max_length=14)
    first_name = CharField(blank=True)
    last_name = CharField(blank=True)
    user_name = CharField(blank=True)
    reason = CharField()
  
    class Meta:
        final = True
        collection_name = 'bans_feds'


class FedsUserSettings(MongoModel):
    user_id = CharField(max_length=14)
    should_report = BooleanField(default=True)
  
    class Meta:
        final = True
        collection_name = 'feds_settings'

FEDS_LOCK = threading.RLock()
CHAT_FEDS_LOCK = threading.RLock()
FEDS_SETTINGS_LOCK = threading.RLock()

FEDERATION_BYNAME = {}
FEDERATION_BYOWNER = {}
FEDERATION_BYFEDID = {}

FEDERATION_CHATS = {}
FEDERATION_CHATS_BYID = {}

FEDERATION_BANNED_FULL = {}
FEDERATION_BANNED_USERID = {}

FEDERATION_NOTIFICATION = {}


def get_fed_info(fed_id):
    get = FEDERATION_BYFEDID.get(str(fed_id))
    if get == None:
        return False
    return get

def get_fed_id(chat_id):
    get = FEDERATION_CHATS.get(str(chat_id))
    if get == None:
        return False
    else:
        return get['fid']


def new_fed(owner_id, fed_name, fed_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        fed = Federations(
            str(owner_id), 
            fed_name, 
            str(fed_id), 
            'Rules is not set in this federation.',
            {'owner': str(owner_id),'members': []}).save()

        FEDERATION_BYOWNER[str(owner_id)] = ({
            'fid': str(fed_id),
            'fname': fed_name,
            'frules': 'Rules is not set in this federation.',
            'fusers':{
                'owner': str(owner_id),
                'members': []}
        })
        FEDERATION_BYFEDID[str(fed_id)] = ({
            'owner': str(owner_id),
            'fname': fed_name,
            'frules':'Rules is not set in this federation.',
            'fusers':{
                'owner': str(owner_id),
                'members': []
            }
        })
        FEDERATION_BYNAME[fed_name] = ({
            'fid':str(fed_id),
            'owner':str(owner_id),
            'frules':'Rules is not set in this federation.',
            'fusers':{
                'owner': str(owner_id),
                'members': []
            }
        })
        return fed

def del_fed(fed_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME, FEDERATION_CHATS, FEDERATION_CHATS_BYID, FEDERATION_BANNED_USERID, FEDERATION_BANNED_FULL
        getcache = FEDERATION_BYFEDID.get(fed_id)
        if getcache == None:
            return False
        # Variables
        getfed = FEDERATION_BYFEDID.get(fed_id)
        owner_id = getfed['owner']
        fed_name = getfed['fname']
        # Delete from cache
        FEDERATION_BYOWNER.pop(owner_id)
        FEDERATION_BYFEDID.pop(fed_id)
        FEDERATION_BYNAME.pop(fed_name)
        if FEDERATION_CHATS_BYID.get(fed_id):
            for x in FEDERATION_CHATS_BYID[fed_id]:
                delchats = ChatF.objects.get({'chat_id': str(x)})
                if delchats:
                    delchats.delete()
                FEDERATION_CHATS.pop(x)
            FEDERATION_CHATS_BYID.pop(fed_id)
        # Delete fedban users
        getall = FEDERATION_BANNED_USERID.get(fed_id)
        if getall:
            for x in getall:
                banlist =  BansF.objects.get({'fed_id': fed_id, 'user_id': str(x)})  
                if banlist:
                    banlist.delete()
            FEDERATION_BANNED_USERID.pop(fed_id)
            FEDERATION_BANNED_FULL.pop(fed_id)
        # Delete from database
        curr = Federations.objects.get({'fed_id': fed_id})
        if curr:
            curr.delete()
        return True

def chat_join_fed(fed_id, chat_id):
    with FEDS_LOCK:
        global FEDERATION_CHATS, FEDERATION_CHATS_BYID
        r = ChatF(chat_id, fed_id).save()
        FEDERATION_CHATS[str(chat_id)] = {'fid': fed_id}
        checkid = FEDERATION_CHATS_BYID.get(fed_id)
        if checkid == None:
            FEDERATION_CHATS_BYID[fed_id] = []
        FEDERATION_CHATS_BYID[fed_id].append(str(chat_id))
        return r


def search_fed_by_name(fed_name):
    allfed = FEDERATION_BYNAME.get(fed_name)
    if allfed == None:
        return False
    return allfed


def search_user_in_fed(fed_id, user_id):
    getfed = FEDERATION_BYFEDID.get(fed_id)
    if getfed == None:
        return False
    getfed = getfed['fusers']['members']
    if user_id in getfed:
        return True
    else:
        return False


def user_demote_fed(fed_id, user_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed['owner']
        fed_name = getfed['fname']
        fed_rules = getfed['frules']
        # Temp set
        try:
            members = getfed['fusers']['members']
        except ValueError:
            return False
        members.remove(user_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]['fusers'] = {
            'owner':str(owner_id),
            'members':members
        }
        FEDERATION_BYFEDID[str(fed_id)]['fusers'] = {
            'owner': str(owner_id),
            'members': members
        }
        FEDERATION_BYNAME[fed_name]['fusers'] = {
            'owner': str(owner_id),
            'members': members
        }
        # Set on database
        Federations.objects.get({'fed_id': fed_id}).delete()
        Federations(
            str(owner_id), fed_name, str(fed_id), fed_rules,
            {
                'owner': str(owner_id),
                'members': members
            }).save()
        __load_all_feds()
        return True

def user_join_fed(fed_id, user_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed['owner']
        fed_name = getfed['fname']
        fed_rules = getfed['frules']
        # Temp set
        members = getfed['fusers']['members']
        members.append(user_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]['fusers'] = {
            'owner':str(owner_id),
            'members': members
        }
        FEDERATION_BYFEDID[str(fed_id)]['fusers'] = {
            'owner': str(owner_id),
            'members': members
        }
        FEDERATION_BYNAME[fed_name]['fusers'] = {
            'owner': str(owner_id),
            'members': members
        }
        # Set on database
        Federations.objects.get({'fed_id': fed_id}).delete()
        Federations(
            str(owner_id), fed_name, str(fed_id), fed_rules,
            {
                'owner': str(owner_id),
                'members': members
            }).save()
        
        __load_all_feds_chats()
        return True

def chat_leave_fed(chat_id):
    with FEDS_LOCK:
        global FEDERATION_CHATS, FEDERATION_CHATS_BYID
        # Set variables
        fed_info = FEDERATION_CHATS.get(str(chat_id))
        if fed_info == None:
            return False
        fed_id = fed_info['fid']
        # Delete from cache
        FEDERATION_CHATS.pop(str(chat_id))
        FEDERATION_CHATS_BYID[str(fed_id)].remove(str(chat_id))
        # Delete from db
        curr = ChatF.objects.all()
        for U in curr:
            if str(U.chat_id) == str(chat_id):
                U.delete()
        return True

def all_fed_chats(fed_id):
    with FEDS_LOCK:
        getfed = FEDERATION_CHATS_BYID.get(fed_id)
        if getfed == None:
            return []
        else:
            return getfed

def all_fed_users(fed_id):
    with FEDS_LOCK:
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        if getfed == None:
            return False
        fed_admins = getfed['fusers']['members']
        return fed_admins

def get_fed_owner(fed_id):
    with FEDS_LOCK:
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        if getfed == None:
            return False
        fed_owner = getfed['fusers']['owner']
        return fed_owner


def all_fed_members(fed_id):
    with FEDS_LOCK:
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        fed_admins = getfed['fusers']['members']
        return fed_admins

def set_frules(fed_id, rules):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed['owner']
        fed_name = getfed['fname']
        fed_members = getfed['fusers']
        fed_rules = str(rules)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]['frules'] = fed_rules
        FEDERATION_BYFEDID[str(fed_id)]['frules'] = fed_rules
        FEDERATION_BYNAME[fed_name]['frules'] = fed_rules
        # Set on database
        Federations.objects.get({'fed_id': fed_id}).delete()
        Federations(str(owner_id), fed_name, str(fed_id), fed_rules, fed_members).save()
        return True

def get_frules(fed_id):
    with FEDS_LOCK:
        rules = FEDERATION_BYFEDID[str(fed_id)]['frules']
        return rules


def fban_user(fed_id, user_id, first_name, last_name, user_name, reason):
    with FEDS_LOCK:
        r = BansF.objects.all()
        for I in r:
            if I.fed_id == fed_id:
                if str(I.user_id) == str(user_id):
                    I.delete()

        BansF(str(fed_id), str(user_id), first_name, last_name or "", user_name, reason).save()
        __load_all_feds_banned()
        return r


def un_fban_user(fed_id, user_id):
    with FEDS_LOCK:
        r = BansF.objects.all()
        for I in r:
            if I.fed_id == fed_id:
                if str(I.user_id) == str(user_id):
                    I.delete()

        __load_all_feds_banned()
        return I

def get_fban_user(fed_id, user_id):
    list_fbanned = FEDERATION_BANNED_USERID.get(fed_id)
    if list_fbanned == None:
        FEDERATION_BANNED_USERID[fed_id] = []
    if user_id in FEDERATION_BANNED_USERID[fed_id]:
        r = BansF.objects.all()
        reason = None
        for I in r:
            if I.fed_id == fed_id:
                if int(I.user_id) == int(user_id):
                    reason = I.reason
        return True, reason
    else:
        return False, None

def get_all_fban_users(fed_id):
    list_fbanned = FEDERATION_BANNED_USERID.get(fed_id)
    if list_fbanned == None:
        FEDERATION_BANNED_USERID[fed_id] = []
    return FEDERATION_BANNED_USERID[fed_id]

def get_all_fban_users_target(fed_id, user_id):
    list_fbanned = FEDERATION_BANNED_FULL.get(fed_id)
    if list_fbanned == None:
        FEDERATION_BANNED_FULL[fed_id] = []
        return False
    getuser = list_fbanned[str(user_id)]
    return getuser


def get_all_fban_users_global():
    total = []
    for x in list(FEDERATION_BANNED_USERID):
        for y in FEDERATION_BANNED_USERID[x]:
            total.append(y)
    return total


def get_all_feds_users_global():
    total = []
    for x in list(FEDERATION_BYFEDID):
        total.append(FEDERATION_BYFEDID[x])
    return total


def search_fed_by_id(fed_id):
    get = FEDERATION_BYFEDID.get(fed_id)
    if get == None:
        return False
    else:
        return get


def user_feds_report(user_id: str) -> bool:
    user_setting = FEDERATION_NOTIFICATION.get(str(user_id))
    if user_setting == None:
        user_setting = True
    return user_setting


def set_feds_setting(user_id: str, setting: bool):
    with FEDS_SETTINGS_LOCK:
        global FEDERATION_NOTIFICATION
        user_setting = FedsUserSettings.objects.get({'user_id': int(user_id)})
        if not user_setting:
            user_setting = FedsUserSettings(user_id).save()

        user_setting.should_report = setting
        user_setting.save()
        FEDERATION_NOTIFICATION[str(user_id)] = setting


def __load_all_feds():
    global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
    feds = Federations.objects.all()
    for x in feds:  # remove tuple by ( ,)
        # Fed by Owner
        check = FEDERATION_BYOWNER.get(x.owner_id)
        if check == None:
            FEDERATION_BYOWNER[x.owner_id] = []
        FEDERATION_BYOWNER[str(x.owner_id)] = {
            'fid': str(x.fed_id),
            'fname': x.fed_name,
            'frules': x.fed_rules,
            'fusers': x.fed_users
        }
        # Fed By FedId
        check = FEDERATION_BYFEDID.get(x.fed_id)
        if check == None:
            FEDERATION_BYFEDID[x.fed_id] = []
        FEDERATION_BYFEDID[str(x.fed_id)] = {
            'owner': str(x.owner_id),
            'fname': x.fed_name,
            'frules': x.fed_rules,
            'fusers': x.fed_users
        }
        # Fed By Name
        check = FEDERATION_BYNAME.get(x.fed_name)
        if check == None:
            FEDERATION_BYNAME[x.fed_name] = []
        FEDERATION_BYNAME[x.fed_name] = {
            'fid': str(x.fed_id),
            'owner': str(x.owner_id),
            'frules': x.fed_rules,
            'fusers': x.fed_users
        }


def __load_all_feds_chats():
    global FEDERATION_CHATS, FEDERATION_CHATS_BYID
    qall = ChatF.objects.all()
    FEDERATION_CHATS = {}
    FEDERATION_CHATS_BYID = {}
    for x in qall:
        # Federation Chats
        check = FEDERATION_CHATS.get(x.chat_id)
        if check == None:
            FEDERATION_CHATS[x.chat_id] = {}
        FEDERATION_CHATS[x.chat_id] = {'fid': x.fed_id}
        # Federation Chats By ID
        check = FEDERATION_CHATS_BYID.get(x.fed_id)
        if check == None:
            FEDERATION_CHATS_BYID[x.fed_id] = []
        FEDERATION_CHATS_BYID[x.fed_id].append(x.chat_id)


def __load_all_feds_banned():
    global FEDERATION_BANNED_USERID, FEDERATION_BANNED_FULL
    FEDERATION_BANNED_USERID = {}
    FEDERATION_BANNED_FULL = {}
    qall = BansF.objects.all()
    for x in qall:
        check = FEDERATION_BANNED_USERID.get(x.fed_id)
        if check == None:
            FEDERATION_BANNED_USERID[x.fed_id] = []
        if int(x.user_id) not in FEDERATION_BANNED_USERID[x.fed_id]:
            FEDERATION_BANNED_USERID[x.fed_id].append(int(x.user_id))
        check = FEDERATION_BANNED_FULL.get(x.fed_id)
        if check == None:
            FEDERATION_BANNED_FULL[x.fed_id] = {}
        FEDERATION_BANNED_FULL[x.fed_id][int(x.user_id)] = {
            'first_name': x.first_name,
            'last_name': x.last_name,
            'user_name': x.user_name,
            'reason': x.reason
        }

def __load_all_feds_settings():
    global FEDERATION_NOTIFICATION
    getuser = FedsUserSettings.objects.all()
    for x in getuser:
        FEDERATION_NOTIFICATION[str(x.user_id)] = x.should_report

__load_all_feds()
__load_all_feds_chats()
__load_all_feds_banned()
__load_all_feds_settings()
