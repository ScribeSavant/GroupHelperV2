import threading

from sqlalchemy import Column, String, UnicodeText, Boolean

from group_helper.modules.sql import BASE, SESSION


class URLBlackListFilters(BASE):
    __tablename__ = "url_blacklist"
    chat_id = Column(String(14), primary_key=True)
    domain = Column(UnicodeText, primary_key=True, nullable=False)
    delete_all = Column(Boolean, default=True)

    def __init__(self, chat_id, domain, delete_all=True):
        self.chat_id = str(chat_id)
        self.domain = str(domain)
        self.delete_all = bool(delete_all)


URLBlackListFilters.__table__.create(checkfirst=True)

URL_BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()

CHAT_URL_BLACKLISTS = {}


def blacklist_url(chat_id, domain):
    with URL_BLACKLIST_FILTER_INSERTION_LOCK:
        domain_filt = URLBlackListFilters(str(chat_id), domain)

        SESSION.merge(domain_filt)
        SESSION.commit()
        CHAT_URL_BLACKLISTS.setdefault(str(chat_id), set()).add(domain)


def is_delete_all(chat_id):
    a = SESSION.query(URLBlackListFilters).filter(
        URLBlackListFilters.chat_id == str(chat_id)).first()
    if a:
        return True
    else:
        return False


def rm_url_from_blacklist(chat_id, domain):
    with URL_BLACKLIST_FILTER_INSERTION_LOCK:
        domain_filt = SESSION.query(URLBlackListFilters).get(
            (str(chat_id), domain))
        if domain_filt:
            if domain in CHAT_URL_BLACKLISTS.get(str(chat_id), set()):
                CHAT_URL_BLACKLISTS.get(str(chat_id), set()).remove(domain)
            SESSION.delete(domain_filt)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def get_blacklisted_urls(chat_id):
    return CHAT_URL_BLACKLISTS.get(str(chat_id), set())


def _load_chat_blacklist():
    global CHAT_URL_BLACKLISTS
    try:
        chats = SESSION.query(URLBlackListFilters.chat_id).distinct().all()
        for (chat_id, ) in chats:
            CHAT_URL_BLACKLISTS[chat_id] = []

        all_urls = SESSION.query(URLBlackListFilters).all()
        for url in all_urls:
            CHAT_URL_BLACKLISTS[url.chat_id] += [url.domain]
        CHAT_URL_BLACKLISTS = {
            k: set(v)
            for k, v in CHAT_URL_BLACKLISTS.items()
        }
    finally:
        SESSION.close()


_load_chat_blacklist()
