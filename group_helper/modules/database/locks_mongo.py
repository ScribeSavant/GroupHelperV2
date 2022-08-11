import threading
from pymodm import MongoModel
from pymodm.fields import BooleanField, CharField


class Permissions(MongoModel):
    chat_id = CharField(max_length=14)
    audio = BooleanField(default=False)
    voice = BooleanField(default=False)
    contact = BooleanField(default=False)
    video = BooleanField(default=False)
    videonote = BooleanField(default=False)
    document = BooleanField(default=False)
    photo = BooleanField(default=False)
    sticker = BooleanField(default=False)
    gif = BooleanField(default=False)
    url = BooleanField(default=False)
    bots = BooleanField(default=False)
    forward = BooleanField(default=False)
    game = BooleanField(default=False)
    location = BooleanField(default=False)
    
    class Meta:
        final = True
        collection_name = 'permissions'


class Restrictions(MongoModel):
    chat_id = CharField(max_length=14)
    messages = BooleanField(default=False)
    media = BooleanField(default=False)
    other = BooleanField(default=False)
    preview = BooleanField(default=False)

    class Meta:
        final = True
        collection_name = 'restrictions'

PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()



def init_permissions(chat_id, reset=False):
    curr_perm = Permissions.objects.get({'chat_id': str(chat_id)})
    if reset:
        curr_perm.delete()
    cur = Permissions(str(chat_id)).save()
    return cur

def init_restrictions(chat_id, reset=False):
    curr_restr = Restrictions.objects.get({'chat_id': str(chat_id)})
    if reset:
        curr_restr.delete()
    restr = Restrictions(str(chat_id)).save()
    return restr


def update_lock(chat_id, lock_type, locked):
    with PERM_LOCK:
        curr_perm = Permissions.objects.get({'chat_id': str(chat_id)})
        if not curr_perm:
            curr_perm = init_permissions(chat_id)

        if lock_type == "audio":
            curr_perm.audio = locked
        elif lock_type == "voice":
            curr_perm.voice = locked
        elif lock_type == "contact":
            curr_perm.contact = locked
        elif lock_type == "video":
            curr_perm.video = locked
        elif lock_type == "videonote":
            curr_perm.videonote = locked
        elif lock_type == "document":
            curr_perm.document = locked
        elif lock_type == "photo":
            curr_perm.photo = locked
        elif lock_type == "sticker":
            curr_perm.sticker = locked
        elif lock_type == "gif":
            curr_perm.gif = locked
        elif lock_type == 'url':
            curr_perm.url = locked
        elif lock_type == 'bots':
            curr_perm.bots = locked
        elif lock_type == 'forward':
            curr_perm.forward = locked
        elif lock_type == 'game':
            curr_perm.game = locked
        elif lock_type == 'location':
            curr_perm.location = locked
        curr_perm.save()

def update_restriction(chat_id, restr_type, locked):
    with RESTR_LOCK:
        curr_restr = Restrictions.objects.get({'chat_id': str(chat_id)})
        if not curr_restr:
            curr_restr = init_restrictions(chat_id)

        if restr_type == "messages":
            curr_restr.messages = locked
        elif restr_type == "media":
            curr_restr.media = locked
        elif restr_type == "other":
            curr_restr.other = locked
        elif restr_type == "previews":
            curr_restr.preview = locked
        elif restr_type == "all":
            curr_restr.messages = locked
            curr_restr.media = locked
            curr_restr.other = locked
            curr_restr.preview = locked
        curr_restr.save()


def is_locked(chat_id, lock_type):
    curr_perm = Permissions.objects.get({'chat_id': str(chat_id)})
    if not curr_perm:
        return False

    elif lock_type == "sticker":
        return curr_perm.sticker
    elif lock_type == "photo":
        return curr_perm.photo
    elif lock_type == "audio":
        return curr_perm.audio
    elif lock_type == "voice":
        return curr_perm.voice
    elif lock_type == "contact":
        return curr_perm.contact
    elif lock_type == "video":
        return curr_perm.video
    elif lock_type == "videonote":
        return curr_perm.videonote
    elif lock_type == "document":
        return curr_perm.document
    elif lock_type == "gif":
        return curr_perm.gif
    elif lock_type == "url":
        return curr_perm.url
    elif lock_type == "bots":
        return curr_perm.bots
    elif lock_type == "forward":
        return curr_perm.forward
    elif lock_type == "game":
        return curr_perm.game
    elif lock_type == "location":
        return curr_perm.location


def is_restr_locked(chat_id, lock_type):
    curr_restr = Restrictions.objects.get({'chat_id': str(chat_id)})

    if not curr_restr:
        return False

    if lock_type == "messages":
        return curr_restr.messages
    elif lock_type == "media":
        return curr_restr.media
    elif lock_type == "other":
        return curr_restr.other
    elif lock_type == "previews":
        return curr_restr.preview
    elif lock_type == "all":
        return curr_restr.messages and curr_restr.media and curr_restr.other and curr_restr.preview

def get_locks(chat_id):
    return Permissions.objects.get({'chat_id': str(chat_id)})
 
def get_restr(chat_id):
    return Restrictions.objects.get({'chat_id': str(chat_id)})

def migrate_chat(old_chat_id, new_chat_id):
    with PERM_LOCK:
        perms = Permissions.objects.get({'chat_id': str(old_chat_id)})
        if perms:
            perms.chat_id = str(new_chat_id)
        perms.save()

    with RESTR_LOCK:
        rest = Restrictions.objects.get({'chat_id': str(old_chat_id)})
        if rest:
            rest.chat_id = str(new_chat_id)
        rest.save()