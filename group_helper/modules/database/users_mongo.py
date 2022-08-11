import threading
from group_helper import CONFIG
from pymodm import MongoModel
from pymodm.fields import CharField, BigIntegerField


class Users(MongoModel):
    user_id = BigIntegerField()
    username = CharField()

    class Meta:
        final = True
        collection_name = 'users'


class Chats(MongoModel):
    chat_id = CharField(max_length=14)
    chat_name = CharField()

    class Meta:
        final = True
        collection_name = 'chats'


class ChatMembers(MongoModel):
    priv_chat_id = BigIntegerField()
    chat = CharField(max_length=14)
    user = BigIntegerField()

    class Meta:
        final = True
        collection_name = 'chat_members'

INSERTION_LOCK = threading.RLock()


def ensure_bot_in_db():
    with INSERTION_LOCK:
        bot_user = Users.objects.get({'user_id': CONFIG.dispatcher.bot.id, 'username':  CONFIG.dispatcher.bot.username})
        if not bot_user:
            Users(CONFIG.dispatcher.bot.id, CONFIG.dispatcher.bot.username).save()


def update_user(user_id, username, chat_id=None, chat_name=None):
    with INSERTION_LOCK:
        user = Users.objects.get({'user_id': int(user_id)})
        if not user:
            user = Users(user_id, username).save()
        else:
            user.username = username

        if not chat_id or not chat_name:
            return

        chat = Chats.objects.get({'chat_id': str(chat_id)})
        if not chat:
           chat = Chats(str(chat_id), chat_name).save()
        else:
            chat.chat_name = chat_name

        member = ChatMembers.objects.get({'chat': str(chat.chat_id), 'user': int(user.user_id)})
        if not member:
            ChatMembers(chat=str(chat.chat_id), user=int(user.user_id)).save()


def get_userid_by_name(username):
    user = Users.objects.get({'username': username})
    if user:
        return user.user_id
    return False
 
def get_name_by_userid(user_id):
    user = Users.objects.get({'user_id': int(user_id)})
    if user:
        return user.username
    return False


def get_all_chats():
    return Chats.objects.all()

def get_user_num_chats(user_id):
    return ChatMembers.objects.raw({'user': int(user_id)}).count()

def num_chats():
    return Chats.objects.count()

def num_users():
    return Users.objects.count()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = Chats.objects.get({'chat_id': str(old_chat_id)})
        if chat:
            chat.chat_id = str(new_chat_id)
            chat.save()


        chat_members = ChatMembers.objects.raw({'chat': str(old_chat_id)})
        for member in chat_members:
            member.chat = str(new_chat_id)
            member.save()

ensure_bot_in_db()

def del_user(user_id):
    with INSERTION_LOCK:
        curr = Users.objects.get({'user_id': int(user_id)})
        if curr:
            curr.delete()
            chat_mem = ChatMembers.objects.get({'user': int(user_id)})
            if chat_mem:
                chat_mem.delete()
            return True
        return False