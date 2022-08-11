import threading
from pymodm import MongoModel
from pymodm.fields import CharField


class Locales(MongoModel):
    chat_id = CharField(max_length=14)
    locale_name = CharField()
    class Meta:
        final = True
        collection_name = 'locales'


LOCALES_INSERTION_LOCK = threading.RLock()

def switch_to_locale(chat_id, locale_name):
    with LOCALES_INSERTION_LOCK:
        prev = Locales.objects.get({'chat_id': str(chat_id)})
        if prev:
            prev.delete()
        Locales(str(chat_id), locale_name).save()

def prev_locale(chat_id):
    return Locales.objects.get({'chat_id': str(chat_id)})