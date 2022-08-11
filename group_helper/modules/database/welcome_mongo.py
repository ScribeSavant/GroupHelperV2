import threading
from pymodm import MongoModel
from pymodm.fields import CharField, BigIntegerField, IntegerField, ListField, BooleanField
from group_helper.modules.helper_funcs.msg_types import Types

DEFAULT_WELCOME = "Hey {first}, how are you?"
DEFAULT_GOODBYE = "Nice knowing ya!"


class Welcome(MongoModel):
    chat_id = CharField(max_length=14)
    should_welcome = BooleanField(default=True)
    should_goodbye = BooleanField(default=True)

    custom_content = CharField(default=None)
    custom_welcome = CharField(default=DEFAULT_WELCOME)
    welcome_type = IntegerField(default=Types.TEXT.value)

    custom_content_leave = CharField(default=None)
    custom_leave = CharField(default=DEFAULT_GOODBYE)
    leave_type = IntegerField(default=Types.TEXT.value)

    clean_welcome = BigIntegerField()


    class Meta:
        final = True
        collection_name = 'welcome_pref'



class WelcomeButtons(MongoModel):
    chat_id = CharField(max_length=14)
    name = CharField()
    url = CharField()
    same_line = BooleanField(default=False)
 
    class Meta:
        final = True
        collection_name = 'welcome_urls'


class GoodbyeButtons(MongoModel):
    chat_id = CharField(max_length=14)
    name = CharField()
    url = CharField()
    same_line = BooleanField(default=False)
 
    class Meta:
        final = True
        collection_name = 'leave_urls'


class CleanServiceSetting(MongoModel):
    chat_id = CharField(max_length=14)
    clean_service = BooleanField(default=True)
 
    class Meta:
        final = True
        collection_name = 'clean_service'


class WelcomeSecurity(MongoModel):
    chat_id = CharField(max_length=14)
    security = BooleanField(default=False)
    mute_time = CharField(default="0")
    custom_text = CharField(default="Klik disini untuk mensuarakan")
 
    class Meta:
        final = True
        collection_name = 'welcome_security'


class UserRestirect(MongoModel):
    chat_id = CharField(max_length=14)
    user_id = BigIntegerField()
 
    class Meta:
        final = True
        collection_name = 'welcome_restirectlist'



INSERTION_LOCK = threading.RLock()
WELC_BTN_LOCK = threading.RLock()
LEAVE_BTN_LOCK = threading.RLock()
CS_LOCK = threading.RLock()
WS_LOCK = threading.RLock()
UR_LOCK = threading.RLock()

CHAT_USERRESTIRECT = {}


def add_to_userlist(chat_id, user_id):
    with UR_LOCK:
        UserRestirect(str(chat_id), int(user_id)).save()
        global CHAT_USERRESTIRECT
        if CHAT_USERRESTIRECT.get(str(chat_id), set()) == set():
            CHAT_USERRESTIRECT[str(chat_id)] = {int(user_id)}
        else:
            CHAT_USERRESTIRECT.get(str(chat_id), set()).add(int(user_id))

def rm_from_userlist(chat_id, user_id):
    with UR_LOCK:
        user_filt = UserRestirect.objects.get({'chat_id': str(chat_id), 'user_id': int(user_id)})
        if user_filt:
            if user_id in CHAT_USERRESTIRECT.get(str(chat_id),
                                                 set()):  # sanity check
                CHAT_USERRESTIRECT.get(str(chat_id), set()).remove(user_id)

            user_filt.delete()
            return True
        return False

def get_chat_userlist(chat_id):
    return CHAT_USERRESTIRECT.get(str(chat_id), set())


def welcome_security(chat_id):
    security = WelcomeSecurity.objects.get({'chat_id': str(chat_id)})
    if security:
        return security.security, security.mute_time, security.custom_text
    else:
        return False, "0", "Click here to prove you're human"



def set_welcome_security(chat_id, security, mute_time, custom_text):
    with WS_LOCK:
        curr_setting = WelcomeSecurity.objects.get({'chat_id': str(chat_id)})
        if not curr_setting:
            curr_setting = WelcomeSecurity(chat_id, security=security, mute_time=mute_time, custom_text=custom_text)
        curr_setting.security = bool(security)
        curr_setting.mute_time = str(mute_time)
        curr_setting.custom_text = str(custom_text)
        curr_setting.save()

def clean_service(chat_id) -> bool:
    chat_setting = CleanServiceSetting.objects.get({'chat_id': str(chat_id)})
    if chat_setting:
        return chat_setting.clean_service
    return False

def set_clean_service(chat_id , setting: bool):
    with CS_LOCK:
        chat_setting = CleanServiceSetting.objects.get({'chat_id': str(chat_id)})
        if not chat_setting:
            chat_setting = CleanServiceSetting(str(chat_id))

        chat_setting.clean_service = setting
        chat_setting.save()

def get_welc_pref(chat_id):
    welc = Welcome.objects.get({'chat_id': str(chat_id)})
    if welc:
        return welc.should_welcome, welc.custom_welcome, welc.custom_content, welc.welcome_type
    else:
        # Welcome by default.
        return True, DEFAULT_WELCOME, None, Types.TEXT

def get_gdbye_pref(chat_id):
    welc = Welcome.objects.get({'chat_id': str(chat_id)})
    if welc:
        return welc.should_goodbye, welc.custom_leave, welc.custom_content_leave, welc.leave_type
    else:
        # Welcome by default.
        return True, DEFAULT_GOODBYE, None, Types.TEXT


def set_clean_welcome(chat_id, clean_welcome):
    with INSERTION_LOCK:
        curr = Welcome.objects.get({'chat_id': str(chat_id)})
        if not curr:
            curr = Welcome(str(chat_id))

        curr.clean_welcome = int(clean_welcome)
        curr.save()

def get_clean_pref(chat_id):
    welc = Welcome.objects.get({'chat_id': str(chat_id)})
    if welc:
        return welc.clean_welcome

    return False

def set_welc_preference(chat_id, should_welcome):
    with INSERTION_LOCK:
        curr = Welcome.objects.get({'chat_id': str(chat_id)})
        if not curr:
            curr = Welcome(str(chat_id), should_welcome=should_welcome)
        else:
            curr.should_welcome = should_welcome

        curr.save()


def set_gdbye_preference(chat_id, should_goodbye):
    with INSERTION_LOCK:
        curr = Welcome.objects.get({'chat_id': str(chat_id)})
        if not curr:
            curr = Welcome(str(chat_id), should_goodbye=should_goodbye)
        else:
            curr.should_goodbye = should_goodbye

        curr.save()

def set_custom_welcome(chat_id,
                       custom_content,
                       custom_welcome,
                       welcome_type,
                       buttons=None):
    if buttons is None:
        buttons = []

    with INSERTION_LOCK:
        welcome_settings = Welcome.objects.get({'chat_id': str(chat_id)})
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id))

        if custom_welcome or custom_content:
            welcome_settings.custom_content = str(custom_content)
            welcome_settings.custom_welcome = str(custom_welcome)
            welcome_settings.welcome_type = int(welcome_type.value)

        else:
            welcome_settings.custom_welcome = str(DEFAULT_WELCOME)
            welcome_settings.welcome_type = int(Types.TEXT.value)

        welcome_settings.save()

        with WELC_BTN_LOCK:
            prev_buttons = WelcomeButtons.objects.raw({'chat_id': str(chat_id)})
            for btn in prev_buttons:
                btn.delete()

            for b_name, url, same_line in buttons:
                button = WelcomeButtons(chat_id, b_name, url, same_line)
                button.save()



def get_custom_welcome(chat_id):
    welcome_settings = Welcome.objects.get({'chat_id': str(chat_id)})
    ret = DEFAULT_WELCOME
    if welcome_settings and welcome_settings.custom_welcome:
        ret = welcome_settings.custom_welcome
    return ret


def set_custom_gdbye(chat_id,
                     custom_content_leave,
                     custom_goodbye,
                     goodbye_type,
                     buttons=None):
    if buttons is None:
        buttons = []

    with INSERTION_LOCK:
        goodbye_settings = Welcome.objects.get({'chat_id': str(chat_id)})
        if not goodbye_settings:
            goodbye_settings = Welcome(str(chat_id))

        if custom_goodbye or custom_content_leave:
            goodbye_settings.custom_content_leave = str(custom_content_leave)
            goodbye_settings.custom_leave = str(custom_goodbye)
            goodbye_settings.leave_type = int(goodbye_type.value)

        else:
            goodbye_settings.custom_leave = str(DEFAULT_GOODBYE)
            goodbye_settings.leave_type = int(Types.TEXT.value)

        goodbye_settings.save()

        with LEAVE_BTN_LOCK:
            prev_buttons = WelcomeButtons.objects.raw({'chat_id': str(chat_id)})
            for btn in prev_buttons:
                btn.delete()

            for b_name, url, same_line in buttons:
                button = GoodbyeButtons(chat_id, b_name, url, same_line)
                button.save()


def get_custom_gdbye(chat_id):
    goodbye_settings = Welcome.objects.get({'chat_id': str(chat_id)})
    ret = DEFAULT_GOODBYE
    if goodbye_settings and goodbye_settings.custom_leave:
        ret = goodbye_settings.custom_leave
    return ret

def get_welc_buttons(chat_id):
    return WelcomeButtons.objects.raw({'chat_id': str(chat_id)})


def get_gdbye_buttons(chat_id):
    return GoodbyeButtons.objects.raw({'chat_id': str(chat_id)})

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = Welcome.objects.get({'chat_id': str(old_chat_id)})
        if chat:
            chat.chat_id = str(new_chat_id)
            chat.save()

        with WELC_BTN_LOCK:
            chat_buttons = WelcomeButtons.objects.raw({'chat_id': str(old_chat_id)})
            for btn in chat_buttons:
                btn.chat_id = str(new_chat_id)
                btn.save()

        with LEAVE_BTN_LOCK:
            chat_buttons = GoodbyeButtons.objects.raw({'chat_id': str(old_chat_id)})
            for btn in chat_buttons:
                btn.chat_id = str(new_chat_id)
                btn.save()


def __load_chat_userrestirect():
    global CHAT_USERRESTIRECT
    chats = UserRestirect.objects.all()
    for chat in chats:  # remove tuple by ( ,)
        CHAT_USERRESTIRECT[str(chat.chat_id)] = []

    all_filters = UserRestirect.objects.all()
    for x in all_filters:
        CHAT_USERRESTIRECT[str(x.chat_id)] += [int(x.user_id)]

    CHAT_USERRESTIRECT = {x: set(y) for x, y in CHAT_USERRESTIRECT.items()}


__load_chat_userrestirect()