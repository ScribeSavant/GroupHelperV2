import threading
from pymodm import MongoModel
from pymodm.fields import BigIntegerField, CharField
from pymongo import ASCENDING

class Disable(MongoModel):
    chat_id = CharField(max_length=14)
    command = CharField()
  
    class Meta:
        final = True
        collection_name = 'disabled_commands'


DISABLE_INSERTION_LOCK = threading.RLock()
DISABLED = {}

def disable_command(chat_id, disable):
    with DISABLE_INSERTION_LOCK:
        disabled = Disable.objects.get({'chat_id': str(chat_id), 'command': disable})
        if not disabled:
            DISABLED.setdefault(str(chat_id), set()).add(disable)
            Disable(str(chat_id), disable).save()
            return True
        return False

def enable_command(chat_id, enable):
    with DISABLE_INSERTION_LOCK:
        disabled = Disable.objects.get({'chat_id': str(chat_id), 'command': enable})

        if disabled:
            if enable in DISABLED.get(str(chat_id)):  # sanity check
                DISABLED.setdefault(str(chat_id), set()).remove(enable)
            disabled.delete()
            return True
        return False

def is_command_disabled(chat_id, cmd):
    return cmd in DISABLED.get(str(chat_id), set())


def get_all_disabled(chat_id):
    return DISABLED.get(str(chat_id), set())

def num_chats():
    return Disable.objects.order_by([('chat_id', ASCENDING)]).count()
  
def num_disabled():
    return Disable.objects.all()

def migrate_chat(old_chat_id, new_chat_id):
    with DISABLE_INSERTION_LOCK:
        chat_filters = Disable.objects.raw({'chat_id': str(old_chat_id)})
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)

        if str(old_chat_id) in DISABLED:
            DISABLED[str(new_chat_id)] = DISABLED.get(str(old_chat_id), set())

def __load_disabled_commands():
    global DISABLED
    all_chats = Disable.objects.all()
    for chat in all_chats:
        DISABLED.setdefault(str(chat.chat_id), set()).add(chat.command)


__load_disabled_commands()