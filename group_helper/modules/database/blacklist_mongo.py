import threading
from pymodm import MongoModel
from pymodm.fields import CharField


class BlackListFilters(MongoModel):
    chat_id = CharField(max_length=14)
    trigger = CharField()
  
    class Meta:
        final = True
        collection_name = 'blacklist'



BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()
CHAT_BLACKLISTS = {}


def add_to_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        BlackListFilters(str(chat_id), trigger).save()
        CHAT_BLACKLISTS.setdefault(str(chat_id), set()).add(trigger)

def rm_from_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = BlackListFilters.objects.get({'chat_id': str(chat_id), 'trigger': trigger})
        if blacklist_filt:
            if trigger in CHAT_BLACKLISTS.get(str(chat_id),
                                              set()):  # sanity check
                CHAT_BLACKLISTS.get(str(chat_id), set()).remove(trigger)
            blacklist_filt.delete()
            return True
        return False

def get_chat_blacklist(chat_id):
    return CHAT_BLACKLISTS.get(str(chat_id), set())

def num_blacklist_filters():
    return BlackListFilters.objects.count()
  
def num_blacklist_chat_filters(chat_id):
    return BlackListFilters.objects.raw({'chat_id': str(chat_id)}).count()
    
def num_blacklist_filter_chats():
    return BlackListFilters.objects.all()

def __load_chat_blacklists():
    global CHAT_BLACKLISTS
    bls = BlackListFilters.objects.all()
    for bl in bls:
        CHAT_BLACKLISTS[str(bl.chat_id)] = []
    filters = BlackListFilters.objects.all()
    for x in filters:
        CHAT_BLACKLISTS[str(x.chat_id)] += [x.trigger]

    CHAT_BLACKLISTS = {x: set(y) for x, y in CHAT_BLACKLISTS.items()}


def migrate_chat(old_chat_id, new_chat_id):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        chat_filters = BlackListFilters.objects.raw({'chat_id': str(old_chat_id)})
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
            filt.save()


__load_chat_blacklists()
