import threading
from pymodm import MongoModel
from pymodm.fields import BigIntegerField, BooleanField, CharField, IntegerField


class ChatAccessConnectionSettings(MongoModel):
    chat_id = CharField(max_length=14)
    allow_connect_to_chat = BooleanField(default=True)
  
    class Meta:
        final = True
        collection_name = 'access_connection'


class Connection(MongoModel):
    user_id = BigIntegerField()
    chat_id = CharField(max_length=14)

    class Meta:
        final = True
        collection_name = 'connection'


class ConnectionHistory(MongoModel):
    user_id = BigIntegerField()
    chat_id1 = CharField(max_length=14)
    chat_id2 = CharField(max_length=14)
    chat_id3 = CharField(max_length=14)
    updated = IntegerField()

    class Meta:
        final = True
        collection_name = 'connection_history'


CHAT_ACCESS_LOCK = threading.RLock()
CONNECTION_INSERTION_LOCK = threading.RLock()
HISTORY_LOCK = threading.RLock()
NOT_FOUND = ChatAccessConnectionSettings.DoesNotExist

def add_history(user_id, chat_id1, chat_id2, chat_id3, updated):
    with HISTORY_LOCK:
        prev = ConnectionHistory.objects.get({'user_id': int(user_id)})
        if prev:  
            prev.delete()
        ConnectionHistory(user_id, chat_id1, chat_id2, chat_id3, updated).save()

def get_history(user_id):
    return ConnectionHistory.objects.get({'user_id': int(user_id)})


def allow_connect_to_chat(chat_id) -> bool:
    chat_setting = ChatAccessConnectionSettings.objects.get({'chat_id': str(chat_id)})
    if chat_setting:
        return chat_setting.allow_connect_to_chat
    return False

def set_allow_connect_to_chat(chat_id, setting: bool):
    with CHAT_ACCESS_LOCK:
        chat_setting = ChatAccessConnectionSettings.objects.get({'chat_id': str(chat_id)})
        if not chat_setting:
            chat_setting = ChatAccessConnectionSettings(str(chat_id)).save()
        chat_setting.allow_connect_to_chat = setting
        chat_setting.save()

def connect(user_id, chat_id):
    with CONNECTION_INSERTION_LOCK:
        prev = Connection.objects.get({'user_id': int(user_id)})
        if prev:
            prev.chat_id = str(chat_id)
            prev.save()
        else:
            Connection(user_id, str(chat_id)).save()
        return True

def get_connected_chat(user_id):
    return Connection.objects.get({'user_id': int(user_id)})

def curr_connection(chat_id):
    return Connection.objects.get({'chat_id': str(chat_id)})

def disconnect(user_id):
    with CONNECTION_INSERTION_LOCK:
        disconnect = Connection.objects.get({'user_id': int(user_id)})
        if disconnect:
            disconnect.delete()
            return True
        return False