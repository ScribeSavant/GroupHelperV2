from email.policy import default
import threading
from pymodm import MongoModel
from pymodm.fields import CharField, BigIntegerField, ListField, BooleanField


class AntispamSettings(MongoModel):
    chat_id = CharField(max_length=14)
    setting = BooleanField(default=True)

    class Meta:
        collection_name = 'antispam_settings'
        final = True

class AntispamChats(MongoModel):
    user_id = BigIntegerField()
    limited = BooleanField(default=False)
    joined_chats = ListField(CharField(), default=[], blank=True)

    class Meta:
        collection_name = 'antispam_chats'
        final = True

GBANSTAT_LIST = set()
ASPAM_SETTING_LOCK = threading.RLock()
ANTISPAMSETTING = set()

def enable_antispam(chat_id):
    with ASPAM_SETTING_LOCK:
        chat = AntispamSettings.objects.get({'chat_id': str(chat_id)})
        if not chat:
            chat = AntispamSettings(str(chat_id)).save()
        chat.setting = True
        chat.save()

        if str(chat_id) in GBANSTAT_LIST:
            GBANSTAT_LIST.remove(str(chat_id))

def disable_antispam(chat_id):
    with ASPAM_SETTING_LOCK:
        chat = AntispamSettings.objects.get({'chat_id': str(chat_id)})
        if not chat:
            chat = AntispamSettings(str(chat_id)).save()
        chat.setting = False
        chat.save()
        
        if str(chat_id) in GBANSTAT_LIST:
            GBANSTAT_LIST.remove(str(chat_id))

def does_chat_gban(chat_id):
    return str(chat_id) not in GBANSTAT_LIST



def limit_the_user(user_id):
    user = AntispamChats.objects.get({'user_id': int(user_id)})
    user.limited = True
    user.save()

def is_user_limited(user_id):
    user = AntispamChats.objects.get({'user_id': int(user_id)})
    return user.limited

def get_user_joined_chats(user_id):
    user = AntispamChats.objects.get({'user_id': int(user_id)})
    if user:
        return user.joined_chats
    return False
    

def add_chat_to_user(user_id, chat_id):
    user = AntispamChats.objects.get({'user_id': int(user_id)})
    if not user:
        user = AntispamChats(int(user_id))
    user.joined_chats.append(str(chat_id))
    user.save()

def remove_chat_to_user(user_id, chat_id):
    user = AntispamChats.objects.get({'user_id': int(user_id)})
    if not user:
        return True
    user.joined_chats.remove(str(chat_id))
    user.save()
    return True

def user_chats_count(user_id):
    user = AntispamChats.objects.get({'user_id': int(user_id)})
    if user:
        return len(user.joined_chats)
    return 0


def __load_gban_stat_list():
    global GBANSTAT_LIST
    GBANSTAT_LIST = {
            x.chat_id
            for x in AntispamSettings.objects.all() if not x.setting
        }

def migrate_chat(old_chat_id, new_chat_id):
    with ASPAM_SETTING_LOCK:
        gban = AntispamSettings.objects.get({'chat_id': str(old_chat_id)})
        if gban:
            gban.chat_id = str(new_chat_id)
            gban.save()

# Create in memory userid to avoid disk access
__load_gban_stat_list()