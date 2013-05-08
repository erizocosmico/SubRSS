# -*- coding: utf-8 -*-

import redis as Redis
import os
import hashlib

def get_db():
    redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
    redis = Redis.from_url(redis_url)
    return redis
    
def crypt_password(password):
    h = hashlib.new('sha512')
    h.update(password)
    return h.hexdigest()
    
def store_user(name, mail, password):
    redis = get_db()
    redis.set("subrss/user/%s/password" % name, crypt_password(password))
    redis.set("subrss/user/%s/mail" % name, mail)
    redis.sadd("subrss/users", name)
    redis.sadd("subrss/emails", mail)
    
def get_user(name):
    redis = get_db()
    if not name in redis.smembers("subrss/users"):
        return None
    user = {}
    user['username'] = name
    user['mail'] = redis.get("subrss/user/%s/mail" % name)
    user['password'] = redis.get("subrss/user/%s/password" % name)
    return user