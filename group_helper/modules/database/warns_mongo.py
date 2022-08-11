import threading
from pymodm import MongoModel
from pymodm.fields import CharField, BigIntegerField, IntegerField, ListField, BooleanField


class Warns(MongoModel):
    user_id = BigIntegerField()
    chat_id = CharField(max_length=14)
    num_warns = IntegerField(default=0)
    reasons = ListField(CharField(), default=[], blank=True)

    class Meta:
        final = True
        collection_name = 'warns'


class WarnFilters(MongoModel):
    chat_id = CharField(max_length=14)
    keyword = CharField()
    reply = CharField()

    class Meta:
        final = True
        collection_name = 'warn_filters'


class WarnSettings(MongoModel):
    chat_id = CharField(max_length=14)
    warn_limit = IntegerField(default=3)
    soft_warn = BooleanField(default=False)

    class Meta:
        final = True
        collection_name = 'warn_settings'

WARN_INSERTION_LOCK = threading.RLock()
WARN_FILTER_INSERTION_LOCK = threading.RLock()
WARN_SETTINGS_LOCK = threading.RLock()

WARN_FILTERS = {}


def warn_user(user_id, chat_id, reason=None):
    with WARN_INSERTION_LOCK:
        warned_user = Warns.objects.get({'user_id': int(user_id), 'chat_id': str(chat_id)})
        if not warned_user:
            warned_user = Warns(int(user_id), str(chat_id))

        warned_user.num_warns += 1

        if reason == "":
            reason = "No reason given."

        if reason:
            if warned_user.reasons is None:
                warned_user.reasons = [reason]
            else:
                warned_user.reasons = warned_user.reasons + [reason]  

        reasons = warned_user.reasons
        num = warned_user.num_warns

        warned_user.save()
        return num, reasons

def remove_warn(user_id, chat_id):
    with WARN_INSERTION_LOCK:
        removed = False
        warned_user = Warns.objects.get({'user_id': int(user_id), 'chat_id': str(chat_id)})
        if warned_user and warned_user.num_warns > 0:
            warned_user.num_warns -= 1
            if warned_user and warned_user.reasons is not None:
                for reason in warned_user.reasons:
                    warned_user.reasons.remove(reason)
            warned_user.save()
            removed = True
        return removed


def reset_warns(user_id, chat_id):
    with WARN_INSERTION_LOCK:
        warned_user = Warns.objects.get({'user_id': int(user_id), 'chat_id': str(chat_id)})
        if warned_user:
            warned_user.num_warns = 0
            warned_user.reasons = []

            warned_user.save()


def get_warns(user_id, chat_id):
    user = Warns.objects.get({'user_id': int(user_id), 'chat_id': str(chat_id)})
    if not user:
        return None
    reasons = user.reasons
    num = user.num_warns
    return num, reasons


def add_warn_filter(chat_id, keyword, reply):
    with WARN_FILTER_INSERTION_LOCK:
        WarnFilters(str(chat_id), keyword, reply).save()

        if keyword not in WARN_FILTERS.get(str(chat_id), []):
            WARN_FILTERS[str(chat_id)] = sorted(
                WARN_FILTERS.get(str(chat_id), []) + [keyword],
                key=lambda x: (-len(x), x))


def remove_warn_filter(chat_id, keyword):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = WarnFilters.objects.get({'chat_id': str(chat_id), 'keyword': keyword})
        if warn_filt:
            if keyword in WARN_FILTERS.get(str(chat_id), []):  # sanity check
                WARN_FILTERS.get(str(chat_id), []).remove(keyword)

            warn_filt.delete()
            return True
        return False

def get_chat_warn_triggers(chat_id):
    return WARN_FILTERS.get(str(chat_id), set())

def get_chat_warn_filters(chat_id):
    return WarnFilters.objects.raw({'chat_id': str(chat_id)})

def get_warn_filter(chat_id, keyword):
    return WarnFilters.objects.get({'chat_id': str(chat_id), 'keyword': keyword})
   
def set_warn_limit(chat_id, warn_limit):
    with WARN_SETTINGS_LOCK:
        curr_setting = WarnSettings.objects.get({'chat_id': str(chat_id)})
        if not curr_setting:
            curr_setting = WarnSettings(chat_id)

        curr_setting.warn_limit = warn_limit
        curr_setting.save()

def set_warn_strength(chat_id, soft_warn):
    with WARN_SETTINGS_LOCK:
        curr_setting = WarnSettings.objects.get({'chat_id': str(chat_id)})
        if not curr_setting:
            curr_setting = WarnSettings(chat_id)

        curr_setting.soft_warn = soft_warn
        curr_setting.save()


def get_warn_setting(chat_id):
    setting = WarnSettings.objects.get({'chat_id': str(chat_id)})
    if setting:
        return setting.warn_limit, setting.soft_warn
    else:
        return 3, False

def get_soft_warn(chat_id):
    setting = WarnSettings.objects.get({'chat_id': str(chat_id)})
    if setting:
        return setting.soft_warn
    else:
        return False

def num_warns():
    return Warns.objects.count() or 0

def num_warn_chats():
    return Warns.objects.count()

def num_warn_filters():
    return WarnFilters.objects.count()
  
def num_warn_chat_filters(chat_id):
    return WarnFilters.objects.raw({'chat_id': str(chat_id)}).count()


def num_warn_filter_chats():
    return WarnFilters.objects.count()
 

def __load_chat_warn_filters():
    global WARN_FILTERS
    chats = [filter.chat_id for filter in WarnFilters.objects.all()]
    for chat_id in chats:  # remove tuple by ( ,)
        WARN_FILTERS[str(chat_id)] = []

    all_filters = WarnFilters.objects.all()
    for x in all_filters:
        WARN_FILTERS[str(x.chat_id)] += [x.keyword]
    WARN_FILTERS = {
        x: sorted(set(y), key=lambda i: (-len(i), i))
        for x, y in WARN_FILTERS.items()
    }


def migrate_chat(old_chat_id, new_chat_id):
    with WARN_INSERTION_LOCK:
        chat_notes = Warns.objects.raw({'chat_id': str(old_chat_id)})
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
            note.save()

    with WARN_FILTER_INSERTION_LOCK:
        chat_filters = WarnFilters.objects.raw({'chat_id': str(old_chat_id)})
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
            filt.save()
        
        WARN_FILTERS[str(new_chat_id)] = WARN_FILTERS[str(old_chat_id)]
        del WARN_FILTERS[str(old_chat_id)]

    with WARN_SETTINGS_LOCK:
        chat_settings = WarnSettings.objects.raw({'chat_id': str(old_chat_id)})
        for setting in chat_settings:
            setting.chat_id = str(new_chat_id)
            setting.save()


__load_chat_warn_filters()