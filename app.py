# -*- coding: utf-8 -*-

import os
from flask import Flask, request, render_template, url_for, redirect, session
import user
import store
import rss as _rss
import subs
import urllib2
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your key'

@app.route('/')
def home():
    if user.logged_in():
        try:
            db = store.get_db()
            rss = db.exists('subrss/user/%s/rss' % session['username'])
            return render_template('home_logged.html',  rss = rss,
                                                        uname = session['username'],
                                                        logged_in = user.logged_in())
        except Exception, e:
            return redirect(url_for('home'))
    else:
        return render_template('landing.html', logged_in = user.logged_in())
        
@app.route('/retrieve_subs', methods=['GET'])
def retrieve_subs():
    is_cache = False
    db = store.get_db()
    try:
        rss = db.exists('subrss/user/%s/rss' % session['username'])
        if rss:
            if db.exists('subrss/users/%s/json_cache_time' % session['username']):
                last_time = int(db.get('subrss/users/%s/json_cache_time' % session['username']))
                if last_time + 3600 >= _rss.to_unix_timestamp(datetime.now()):
                    rss_items = json.loads(db.get('subrss/users/%s/json_cache' % session['username']))
                    is_cache = True
                    rss_lastcheck = datetime.now()
                    rss_error = False
            if not is_cache:
                (rss_url, rss_lastcheck, rss_items) = _rss.get_rss(session['username'])
                rss_error = True if not rss_url and not rss_lastcheck and not rss_items else False
        else:
            (rss_url, rss_lastcheck, rss_items) = (None, False, [])
            rss_error = True
    except Exception, e:
        return str(e)
        rss_error = True
        rss_lastcheck = None
        rss_items = None
    try:
        if rss_items and not is_cache:
            db = store.get_db()
            db.set('subrss/users/%s/json_cache' % session['username'], json.dumps(rss_items))
            db.set('subrss/users/%s/json_cache_time' % session['username'], _rss.to_unix_timestamp(datetime.now()))
    except:
        pass
    return render_template('subs_list.html',    rss_last = rss_lastcheck,
                                                rss_items = rss_items,
                                                rss_error = rss_error,
                                                logged_in = user.logged_in())
                                                
@app.route('/download_sub', methods=['POST'])
def download_single():
    try:
        srt_file = subs.get_sub(request.form['file'], urllib2.urlopen(request.form['sub']).read(), request.form['sub'], True if "720p" in request.form['title'] else False)
        return subs.download_sub(srt_file, request.form['file'])
    except:
        return '<script type="text/javascript">alert("Ha ocurrido un error mientras se descargaba el subtítulo.");</script>'
        
@app.route('/download_all', methods=['POST'])
def download_all():
    try:
        db = store.get_db()
        rss_items = json.loads(db.get('subrss/users/%s/json_cache' % session['username']))
        if rss_items:
            items = []
            for i in range(0, 10):
                item = rss_items[i]
                _item = {}
                _item['filename'] = item['filename']
                _item['content'] = subs.get_sub(item['filename'], urllib2.urlopen(item['sub_url']).read(), item['sub_url'], True if "720p" in item['title'] else False)
                items.append(_item)
            return subs.get_all_subs(items)
    except Exception, e:
        return '<script type="text/javascript">alert("Ha ocurrido un error mientras se descargaban los subtítulos.");</script>' % str(e)
    
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if user.logged_in():
        return redirect(url_for('home'))
    if request.method == 'GET':
        return user.signup_form()
    else:
        return user.signup()
    
@app.route("/login", methods=['POST', 'GET'])
def login(error = False):
    if user.logged_in():
        return redirect(url_for('home'))
    if request.method == 'GET' or error:
        return render_template('login.html',    error = error,
                                                logged_in = user.logged_in())
    else:
        try:
            if not user.is_valid_login():
                return login(False)
            session['username'] = request.form['username']
            return redirect(url_for('home'))
        except Exception, e:
            return login(True)
    
@app.route("/logout", methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))
    
@app.route("/set_rss", methods=['POST'])
def set_rss():
    if not user.logged_in():
        return redirect(url_for('home'))
    name = session['username']
    db = store.get_db()
    db.set()
    
@app.route("/settings", methods=['GET', 'POST'])
def settings():
    try:
        if not user.logged_in():
            return redirect(url_for('login'))
        _user = store.get_user(session['username'])
        db = store.get_db()
        errors = []
        feed_rss = db.get('subrss/user/%s/rss' % session['username']) if db.exists('subrss/user/%s/rss' % session['username']) else ""
        if request.method == 'GET':
            return render_template('settings_form.html',    success = False,
                                                            username = _user['username'],
                                                            email = _user['mail'],
                                                            feed_rss = feed_rss,
                                                            errors = errors,
                                                            logged_in = user.logged_in())
        else:
            if user.validate_email(request.form['mail']) and not request.form['mail'] in db.smembers('subrss/emails'):
                db.srem('subrss/mails', _user['mail'])
                db.sadd('subrss/mails', request.form['mail'])
                db.set('subrss/user/%s/mail' % session['username'], request.form['mail'])
            else:
                errors.append("El email introducido no es válido o ya está en uso.")
            if request.form['password']:
                if len(request.form['password']) >= 8 and _user['password'] == store.crypt_password(request.form['password_repeat']):
                    db.set('subrss/user/%s/password' % session['username'], store.crypt_password(request.form['password']))
                else:
                    errors.append("La clave introducida no es correcta.")
            if request.form['feed']:
                db.set('subrss/user/%s/rss' % session['username'], request.form['feed'])
            return render_template('settings_form.html',    success = True if not errors else False,
                                                            username = _user['username'],
                                                            email = _user['mail'],
                                                            feed_rss = feed_rss,
                                                            errors = errors,
                                                            logged_in = user.logged_in())
    except Exception, e:
        return redirect(url_for('home'))
    
@app.route('/contact')
def contact():
    return render_template('contact.html', logged_in = user.logged_in())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
