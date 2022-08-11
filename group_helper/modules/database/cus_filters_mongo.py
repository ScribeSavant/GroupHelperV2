import threading
from pymodm import MongoModel
from pymodm.fields import BigIntegerField, BooleanField, CharField
from pymongo import ASCENDING


class CustomFilters(MongoModel):
    chat_id = CharField(max_length=14)
    keyword = CharField()
    reply = CharField()
    is_sticker = BooleanField(default=False)
    is_document = BooleanField(default=False)
    is_image = BooleanField(default=False)
    is_audio = BooleanField(default=False)
    is_voice = BooleanField(default=False)
    is_video = BooleanField(default=False)
    has_buttons = BooleanField(default=False)
    has_markdown = BooleanField(default=True)
  
    class Meta:
        final = True
        collection_name = 'cust_filters'


class Buttons(MongoModel):
    chat_id = CharField(max_length=14)
    keyword = CharField()
    name = CharField()
    url = CharField()
    same_line = BooleanField(default=False)
  
    class Meta:
        final = True
        collection_name = 'cust_filter_urls'


CUST_FILT_LOCK = threading.RLock()
BUTTON_LOCK = threading.RLock()
CHAT_FILTERS = {}

def get_all_filters():
    return CustomFilters.objects.all()


def add_filter(chat_id, keyword, reply, is_sticker=False, is_document=False, is_image=False, is_audio=False, is_voice=False, is_video=False, buttons=None):
    global CHAT_FILTERS
    if buttons is None:
        buttons = []

    with CUST_FILT_LOCK:
        prev = CustomFilters.objects.get({'chat_id': str(chat_id), 'keyword': keyword})
        if prev:    
            with BUTTON_LOCK:
                prev_buttons = Buttons.objects.raw({'chat_id': str(chat_id), 'keyword': keyword})
                if prev_buttons:
                    for btn in prev_buttons:
                        btn.delete()
            prev.delete()

        CustomFilters(str(chat_id), keyword, reply, is_sticker,
                             is_document, is_image, is_audio, is_voice,
                             is_video, bool(buttons)).save()

        if keyword not in CHAT_FILTERS.get(str(chat_id), []):
            CHAT_FILTERS[str(chat_id)] = sorted(
                CHAT_FILTERS.get(str(chat_id), []) + [keyword],
                key=lambda x: (-len(x), x))

    for b_name, url, same_line in buttons:
        add_note_button_to_db(str(chat_id), keyword, b_name, url, same_line)


def remove_filter(chat_id, keyword):
    global CHAT_FILTERS
    with CUST_FILT_LOCK:
        filt = CustomFilters.objects.get({'chat_id': str(chat_id), 'keyword': keyword})
        if filt:
            if keyword in CHAT_FILTERS.get(str(chat_id), []):  # Sanity check
                CHAT_FILTERS.get(str(chat_id), []).remove(keyword)

            with BUTTON_LOCK:
                prev_buttons = Buttons.objects.raw({'chat_id': str(chat_id), 'keyword': keyword})
                if prev_buttons:
                    for btn in prev_buttons:
                        btn.delete()
            filt.delete()
            return True
        return False


def get_chat_triggers(chat_id):
    return CHAT_FILTERS.get(str(chat_id), set())

def get_filter(chat_id, keyword):
    return CustomFilters.objects.get({'chat_id': str(chat_id), 'keyword': keyword})

def add_note_button_to_db(chat_id, keyword, b_name, url, same_line):
    with BUTTON_LOCK:
        Buttons(chat_id, keyword, b_name, url, same_line).save()

def get_buttons(chat_id, keyword):
    return Buttons.objects.raw({'chat_id': str(chat_id), 'keyword': keyword})

def num_filters():
    return CustomFilters.objects.count()

def num_chats():
    return CustomFilters.objecst.order_by([('chat_id', ASCENDING)]).count()

def __load_chat_filters():
    global CHAT_FILTERS
    flts = CustomFilters.objects.all()
    for filt in flts: 
        CHAT_FILTERS[str(filt.chat_id)] = []
    all_filters = CustomFilters.objects.all()
    for x in all_filters:
        CHAT_FILTERS[str(x.chat_id)] += [x.keyword]
    CHAT_FILTERS = {
        x: sorted(set(y), key=lambda i: (-len(i), i))
        for x, y in CHAT_FILTERS.items()
    }


def migrate_chat(old_chat_id, new_chat_id):
    with CUST_FILT_LOCK:
        chat_filters = CustomFilters.objects.raw({'chat_id': str(old_chat_id)})
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
            filt.save()
        CHAT_FILTERS[str(new_chat_id)] = CHAT_FILTERS[str(old_chat_id)]
        del CHAT_FILTERS[str(old_chat_id)]
    
    with BUTTON_LOCK:
        chat_buttons = Buttons.objects.raw({'chat_id': str(old_chat_id)})
        for btn in chat_buttons:
            btn.chat_id = str(new_chat_id)
            btn.save()

__load_chat_filters()