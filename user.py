# -*- coding: utf-8 -*-

from flask import render_template, url_for, request, session
from store import get_db, crypt_password, get_user, store_user
import hashlib
import re

def validate_email(email):
	if len(email) > 7:
		if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
			return True
	return False
    
def signup_form(error = False):
    return render_template('signup_form.html',  error = error,
                                                logged_in = logged_in())
    
def logged_in():
    try:
        if session['username'] and session['username'] in get_db().smembers("subrss/users"):
            return True
    except:
        return False
    return False
    
def is_valid_login():
    try:
        h = hashlib.new('sha512')
        h.update(request.form['password'])
        user = get_user(request.form['username'])
        return True if user['password'] == h.hexdigest() else False
    except KeyError:
        return False
    
def is_signup_data_valid():
    if request.form['username'] not in get_db().smembers("subrss/users"):
        if len(request.form['username']) in xrange(3, 30):
            if request.form['mail'] not in get_db().smembers("subrss/emails"):
                if len(request.form['password']) >= 8 and validate_email(request.form['mail']):
                    return True
    return False
    
def signup():
    try:
        if not is_signup_data_valid():
            return signup_form(True)
    except KeyError:
        return signup_form(request, True)
    store_user(request.form['username'], request.form['mail'], request.form['password'])
    return render_template('signup.html', logged_in = logged_in())