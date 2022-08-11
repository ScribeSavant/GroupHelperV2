import threading
from pymodm import MongoModel
from pymodm.fields import CharField, BooleanField, BigIntegerField


class ReportingUserSettings(MongoModel):
    user_id = BigIntegerField()
    should_report = BooleanField(default=True)

    class Meta:
        final = True
        collection_name = 'user_report_settings'


class ReportingChatSettings(MongoModel):
    chat_id = CharField(max_length=14)
    should_report = BooleanField(default=True)

    class Meta:
        final = True
        collection_name = 'chat_report_settings'


CHAT_LOCK = threading.RLock()
USER_LOCK = threading.RLock()


def chat_should_report(chat_id) -> bool:
    chat_setting = ReportingChatSettings.objects.get({'chat_id': str(chat_id)})
    if chat_setting:
        return chat_setting.should_report
    return True


def user_should_report(user_id: int) -> bool:
    user_setting = ReportingUserSettings.objects.get({'user_id': int(user_id)})
    if user_setting:
        return user_setting.should_report
    return True

def set_chat_setting(chat_id, setting: bool):
    with CHAT_LOCK:
        chat_setting = ReportingChatSettings.objects.get({'chat_id': str(chat_id)})
        if not chat_setting:
            ReportingChatSettings(chat_id, setting).save()


def set_user_setting(user_id: int, setting: bool):
    with CHAT_LOCK:
        user_setting = ReportingUserSettings.objects.get({'user_id': int(user_id)})
        if not user_setting:
            ReportingUserSettings(user_id, setting).save()

def migrate_chat(old_chat_id, new_chat_id):
    with CHAT_LOCK:
        chat_notes = ReportingChatSettings.objects.raw({'chat_id': str(old_chat_id)})
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
            note.save()
