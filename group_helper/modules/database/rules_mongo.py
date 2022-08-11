import threading
from pymodm import MongoModel
from pymodm.fields import CharField


class Rules(MongoModel):
    chat_id = CharField(max_length=14)
    rules = CharField(blank=True)

    class Meta:
        final = True
        collection_name = 'rules'


INSERTION_LOCK = threading.RLock()


def set_rules(chat_id, rules_text):
    with INSERTION_LOCK:
        rules = Rules.objects.get({'chat_id': str(chat_id)})
        if not rules:
            rules = Rules(str(chat_id))
        
        rules.rules = rules_text
        rules.save()
        

def get_rules(chat_id):
    rules = Rules.objects.get({'chat_id': str(chat_id)})
    ret = ""
    if rules:
        ret = rules.rules
    return ret

def num_chats():
    return Rules.objects.count()
 

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = Rules.objects.get({'chat_id': str(old_chat_id)})
        if chat:
            chat.chat_id = str(new_chat_id)
            chat.save()
