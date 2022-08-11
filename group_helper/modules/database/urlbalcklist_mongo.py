import threading
from pymodm import MongoModel
from pymodm.fields import CharField, BooleanField


class URLBlackListFilters(MongoModel):
    chat_id = CharField(max_length=14)
    domain = CharField()

    class Meta:
        final = True
        collection_name = 'url_blacklist'


class URLBlackListFiltersAll(MongoModel):
    chat_id = CharField(max_length=14)
    delete_all = BooleanField(default=True)

    class Meta:
        final = True
        collection_name = 'url_blacklist_all'


URL_BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()
URL_BLACKLIST_ALL_FILTER_INSERTION_LOCK = threading.RLock()

CHAT_URL_BLACKLISTS = {}


def blacklist_url(chat_id, domain):
    with URL_BLACKLIST_FILTER_INSERTION_LOCK:
        URLBlackListFilters(str(chat_id), domain).save()
        CHAT_URL_BLACKLISTS.setdefault(str(chat_id), set()).add(domain)


def is_delete_all(chat_id):
    with URL_BLACKLIST_ALL_FILTER_INSERTION_LOCK:
        curr = URLBlackListFiltersAll.objects.get({'chat_id': str(chat_id)})
        if curr:
            print(curr.delete_all)
            return curr.delete_all
        return False


def enable_delete_all(chat_id):
    with URL_BLACKLIST_ALL_FILTER_INSERTION_LOCK:
        curr = URLBlackListFiltersAll.objects.get({'chat_id': str(chat_id)})
        if not curr:
            curr = URLBlackListFiltersAll(chat_id=str(chat_id))
        curr.delete_all = True
        curr.save()
        return True

def disable_delete_all(chat_id):
    with URL_BLACKLIST_ALL_FILTER_INSERTION_LOCK:
        curr = URLBlackListFiltersAll.objects.get({'chat_id': str(chat_id)})
        if not curr:
            curr = URLBlackListFiltersAll(chat_id=str(chat_id))
        curr.delete_all = False
        curr.save()
        return True
        

def rm_url_from_blacklist(chat_id, domain):
    with URL_BLACKLIST_FILTER_INSERTION_LOCK:
        domain_filt = URLBlackListFilters.objects.get({'chat_id': str(chat_id), 'domain': domain})
        if domain_filt:
            if domain in CHAT_URL_BLACKLISTS.get(str(chat_id), set()):
                CHAT_URL_BLACKLISTS.get(str(chat_id), set()).remove(domain)
            domain_filt.delete()
            return True
        return False

def get_blacklisted_urls(chat_id):
    return CHAT_URL_BLACKLISTS.get(str(chat_id), set())


def _load_chat_blacklist():
    global CHAT_URL_BLACKLISTS
    blacklists = URLBlackListFilters.objects.all()
    for bc in blacklists:
        CHAT_URL_BLACKLISTS[str(bc.chat_id)] = []
    all_urls = URLBlackListFilters.objects.all()
    for url in all_urls:
        CHAT_URL_BLACKLISTS[url.chat_id] += [url.domain]
    CHAT_URL_BLACKLISTS = {
        k: set(v)
        for k, v in CHAT_URL_BLACKLISTS.items()
    }

_load_chat_blacklist()