import threading
from pymodm import MongoModel
from pymodm.fields import CharField, BooleanField, IntegerField
from group_helper.modules.helper_funcs.msg_types import Types


class Notes(MongoModel):
    chat_id = CharField(max_length=14)
    name = CharField()
    value = CharField()
    files = CharField()
    is_reply = BooleanField(default=False)
    has_buttons = BooleanField(default=False)
    msgtype = IntegerField(default=Types.BUTTON_TEXT.value)

    class Meta:
        final = True
        collection_name = 'notes'


class Buttons(MongoModel):
    chat_id = CharField(max_length=14)
    note_name = CharField()
    name = CharField()
    url = CharField()
    same_line = BooleanField(default=False)

    class Meta:
        final = True
        collection_name = 'note_urls'


NOTES_INSERTION_LOCK = threading.RLock()
BUTTONS_INSERTION_LOCK = threading.RLock()

def add_note_to_db(chat_id,
                   note_name,
                   note_data,
                   msgtype,
                   buttons=None,
                   files=None):
    if not buttons:
        buttons = []

    with NOTES_INSERTION_LOCK:
        prev = Notes.objects.get({'chat_id': str(chat_id), 'name': note_name})
        if prev:
            with BUTTONS_INSERTION_LOCK:
                prev_buttons = Buttons.objects.raw({'chat_id': str(chat_id), 'note_name': note_name})
                for btn in prev_buttons:
                    btn.delete()
            prev.delete()
        Notes(chat_id=str(chat_id), name=str(note_name), value=str(note_data) or "", msgtype=msgtype.value, files=str(files)).save()

    for b_name, url, same_line in buttons:
        add_note_button_to_db(chat_id, note_name, b_name, url, same_line)
    return

def get_note(chat_id, note_name):
    return Notes.objects.get({'chat_id': str(chat_id), 'name': note_name})

def rm_note(chat_id, note_name):
    with NOTES_INSERTION_LOCK:
        note = Notes.objects.get({'chat_id': str(chat_id), 'name': note_name})
        if note:
            with BUTTONS_INSERTION_LOCK:
                buttons = Buttons.objects.raw({'chat_id': str(chat_id), 'note_name': note_name})
                for btn in buttons:
                    btn.delete()
            note.delete()
            return True
        else:
            return False

def get_all_chat_notes(chat_id):
    return [note.name for note in Notes.objects.raw({'chat_id': str(chat_id)})]


def add_note_button_to_db(chat_id, note_name, b_name, url, same_line):
    with BUTTONS_INSERTION_LOCK:
        Buttons(chat_id, note_name, b_name, url, same_line).save()
        print('Button added')
        return

def get_buttons(chat_id, note_name):
    return Buttons.objects.raw({'chat_id': str(chat_id), 'note_name': note_name})
 

def num_notes():
    return Notes.objects.count()

def num_chats():
    return Notes.objects.count()


def migrate_chat(old_chat_id, new_chat_id):
    with NOTES_INSERTION_LOCK:
        chat_notes = Notes.objects.raw({'chat_id': str(old_chat_id)})
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
            note.save()

        with BUTTONS_INSERTION_LOCK:
            chat_buttons = Buttons.objects.raw({'chat_id': str(old_chat_id)})
            for btn in chat_buttons:
                btn.chat_id = str(new_chat_id)
                btn.save()
