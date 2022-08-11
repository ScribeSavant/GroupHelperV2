import threading
from pymodm import MongoModel
from pymodm.fields import CharField



class GroupLogs(MongoModel):
    chat_id = CharField(max_length=14)
    log_channel = CharField(max_length=14)

    class Meta:
        final = True
        collection_name = 'log_channels'



LOGS_INSERTION_LOCK = threading.RLock()
CHANNELS = {}

def set_chat_log_channel(chat_id, log_channel):
    with LOGS_INSERTION_LOCK:
        res = GroupLogs.objects.get({'chat_id': str(chat_id)})
        if res:
            res.log_channel = log_channel
        else:
            res = GroupLogs(chat_id, log_channel).save()

        CHANNELS[str(chat_id)] = log_channel

def get_chat_log_channel(chat_id):
    return CHANNELS.get(str(chat_id))


def stop_chat_logging(chat_id):
    with LOGS_INSERTION_LOCK:
        res = GroupLogs.objects.get({'chat_id': str(chat_id)})
        if res:
            if str(chat_id) in CHANNELS:
                del CHANNELS[str(chat_id)]

            log_channel = res.log_channel
            res.delete()
            return log_channel

def num_logchannels():
    return GroupLogs.objects.count()


def migrate_chat(old_chat_id, new_chat_id):
    with LOGS_INSERTION_LOCK:
        chat = GroupLogs.objects.get({'chat_id': str(old_chat_id)})
        if chat:
            chat.chat_id = str(new_chat_id)
            chat.save()

        if str(old_chat_id) in CHANNELS:
                CHANNELS[str(new_chat_id)] = CHANNELS.get(str(old_chat_id))


def __load_log_channels():
    global CHANNELS
    all_chats = GroupLogs.objects.all()
    CHANNELS = {chat.chat_id: chat.log_channel for chat in all_chats}

__load_log_channels()