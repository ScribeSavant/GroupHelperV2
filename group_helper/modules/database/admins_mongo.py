
import threading
from typing import Union
from pymodm import MongoModel
from pymodm.fields import CharField, BooleanField, BigIntegerField



DEF_ID_FOR_SETTING = 123456


class CommandReactionChatSettings(MongoModel):
    chat_id = CharField(max_length=14, verbose_name='chat_id', mongo_name='chat_id')
    comm_reaction = BooleanField(default=True, verbose_name='comm_reaction', mongo_name='comm_reaction')

    class Meta:
        collection_name = 'comm_react_setting'
        final = True


class ChatLimits(MongoModel):
    def_id = BigIntegerField(default=DEF_ID_FOR_SETTING)
    chat_limit = BigIntegerField()

    class Meta:
        collection_name = 'admin_chat_limits'
        final = True


NOT_FOUND = CommandReactionChatSettings.DoesNotExist
CHAT_LOCK = threading.RLock()



def get_chat_limit():
    setting = ChatLimits.objects.get({'def_id': DEF_ID_FOR_SETTING})
    if not setting:
        setting = ChatLimits(DEF_ID_FOR_SETTING, 2)
    setting.save()
    return setting.chat_limit

def set_chat_limit(limit):
    setting = ChatLimits.objects.get({'def_id': DEF_ID_FOR_SETTING})
    if not setting:
        setting = ChatLimits(DEF_ID_FOR_SETTING)
    setting.chat_limit = int(limit)
    setting.save()
    return True


def command_reaction(chat_id) -> bool:
    chat_setting = CommandReactionChatSettings.objects.get({'chat_id': str(chat_id)})
    if chat_setting:
        return chat_setting.comm_reaction
    return False


def set_command_reaction(chat_id: Union[int, str], setting: bool):
    with CHAT_LOCK:
        chat_setting = CommandReactionChatSettings.objects.get({'chat_id': str(chat_id)})
        if not chat_setting:
           chat_setting= CommandReactionChatSettings(str(chat_id), setting).save()
        chat_setting.command_reaction = setting
        chat_setting.save()
        

def migrate_chat(old_chat_id, new_chat_id):
    with CHAT_LOCK:
        chat_notes: CommandReactionChatSettings.objects.all()
        for note in chat_notes:
            if note.chat_id == str(old_chat_id):
                note.chat_id = str(new_chat_id)
                note.save()
