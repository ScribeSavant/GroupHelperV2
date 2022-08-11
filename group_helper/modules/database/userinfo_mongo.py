import threading
from pymodm import MongoModel
from pymodm.fields import CharField, BigIntegerField


class UserInfo(MongoModel):
    user_id = BigIntegerField()
    info = CharField()

    class Meta:
        final = True
        collection_name = 'userinfo'


class UserBio(MongoModel):
    user_id = BigIntegerField()
    bio = CharField()

    class Meta:
        final = True
        collection_name = 'userbio'

INSERTION_LOCK = threading.RLock()


def get_user_me_info(user_id):
    userinfo = UserInfo.objects.get({'user_id': int(user_id)})
    if userinfo:
        return userinfo.info
    return None

def set_user_me_info(user_id, info):
    with INSERTION_LOCK:
        userinfo = UserInfo.objects.get({'user_id': int(user_id)})
        if userinfo:
            userinfo.info = info
            userinfo.save()
        else:
            UserInfo(user_id, info).save()



def get_user_bio(user_id):
    userbio = UserBio.objects.get({'user_id': int(user_id)})
    if userbio:
        return userbio.bio
    return None

def set_user_bio(user_id, bio):
    with INSERTION_LOCK:
        userbio = UserBio.objects.get({'user_id': int(user_id)})
        if userbio:
            userbio.bio = bio
            userbio.save()
        else:
            UserBio(user_id, bio).save()

def clear_user_info(user_id):
    with INSERTION_LOCK:
        curr = UserInfo.objects.get({'user_id': int(user_id)})
        if curr:
            curr.delete()
            return True
    return False


def clear_user_bio(user_id):
    with INSERTION_LOCK:
        curr = UserBio.objects.get({'user_id': int(user_id)})
        if curr:
            curr.delete()
            return True
    return False