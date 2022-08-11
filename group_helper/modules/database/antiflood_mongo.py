import threading
from pymodm import MongoModel
from pymodm.fields import CharField, IntegerField, BigIntegerField



DEF_COUNT = 0
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)


class FloodControl(MongoModel):
    chat_id = CharField(max_length=14)
    user_id = BigIntegerField(default=0)
    count = IntegerField(default=DEF_COUNT)
    limit = IntegerField(default=DEF_LIMIT)

    class Meta:
        collection_name = 'antiflood'
        final = True


NOT_FOUND = FloodControl.DoesNotExist
INSERTION_LOCK = threading.RLock()
CHAT_FLOOD = {}

def set_flood(chat_id, amount):
    with INSERTION_LOCK:
        flood = FloodControl.objects.get({'chat_id': str(chat_id)})
        if not flood:
            flood = FloodControl(chat_id=str(chat_id), limit=amount).save()
        flood.limit = amount
        flood.user_id = 0
        flood.save()
        CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)


def update_flood(chat_id: str, user_id) -> bool:
    if str(chat_id) in CHAT_FLOOD:
        curr_user_id, count, limit = CHAT_FLOOD.get(str(chat_id), DEF_OBJ)

        if limit == 0:  # no antiflood
            return False

        if user_id != curr_user_id or user_id is None:  # other user
            CHAT_FLOOD[str(chat_id)] = (user_id, DEF_COUNT + 1, limit)
            return False

        count += 1
        if count > limit:  # too many msgs, kick
            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, limit)
            return True

        # default -> update
        CHAT_FLOOD[str(chat_id)] = (user_id, count, limit)
        return False

def get_flood_limit(chat_id):
    return CHAT_FLOOD.get(str(chat_id), DEF_OBJ)[2]


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        flood = FloodControl.objects.get({'chat_id': str(old_chat_id)})
        if flood:
            flood.chat_id = str(new_chat_id)
            flood.save()
            CHAT_FLOOD[str(new_chat_id)] = CHAT_FLOOD.get(str(old_chat_id), DEF_OBJ)
    

def __load_flood_settings():
    global CHAT_FLOOD
    all_chats = FloodControl.objects.all()
    CHAT_FLOOD = {
        str(chat.chat_id): (None, DEF_COUNT, chat.limit)
        for chat in all_chats
    }

__load_flood_settings()