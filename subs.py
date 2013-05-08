# -*- coding: utf-8 -*-

from __future__ import with_statement
from zipfile import ZipFile, ZIP_DEFLATED
from flask import make_response
from cStringIO import StringIO
import urllib2, re, sys
import socket

def get_sub_url(title):
    search = "(?P<show_name>.+)S(?P<season>[0-9]+)E(?P<chapter>[0-9]+)"
    reg = re.search(search, title)
    try:
        show = reg.group(1)
        season = reg.group(2)
        chapter = reg.group(3)
        return "http://www.subtitulos.es/%s/%dx%s" % (show.strip().lower().replace(' ', '-'), int(season), chapter)
    except:
        return False

def get_sub(filename, source, url, hd = False):
    search = "http://www.subtitulos.es/updated/5/(?P<code>[0-9]+)/0"
    search_alt = "http://www.subtitulos.es/updated/4/(?P<code>[0-9]+)/0"
    group_no = 1
    found = False
    if hd:
        search = "<div id=\"version\"(?P<w1>.+)<p class=\"title-sub\"(?P<w2>.+)720p(?P<w3>.+)http://www.subtitulos.es/updated/5/(?P<code>[0-9]+)/0"
        search_alt = search = "<div id=\"version\"(?P<w1>.+)<p class=\"title-sub\"(?P<w2>.+)720p(?P<w3>.+)http://www.subtitulos.es/updated/4/(?P<code>[0-9]+)/0"
        group_no = 4
    try:
        code = re.search(search, source).group(group_no)
        found = 5
    except:
        try:
            code = re.search(search_alt, source).group(group_no)
            found = 4
        except:
            pass
    try:
        if found:
            request = urllib2.Request("http://www.subtitulos.es/updated/%d/%s/0" % (found, code), headers={"Referer" : url})
        else:
            return None
        return urllib2.urlopen(request).read()
    except:
        return None
        
def download_sub(source, filename):
    file = StringIO()
    file.write(source)
    resp = make_response(file.getvalue())
    resp.headers['Content-Type'] = 'text/plain'
    resp.headers['Content-Disposition'] = 'attachment; filename=%s' % filename
    resp.headers['Content-Length'] = str(len(source))
    file.close()
    return resp
        
def get_all_subs(subs):
    timeout = 3600
    socket.setdefaulttimeout(timeout)
    file = StringIO()
    with ZipFile(file, mode='w', compression=ZIP_DEFLATED) as z:
        for sub in subs:
            if sub['content'] != None:
                z.writestr(sub['filename'], sub['content'])
    resp = make_response(file.getvalue())
    resp.headers['Content-Type'] = 'application/zip'
    resp.headers['Content-Disposition'] = 'attachment; filename=subtitles.zip'
    resp.headers['Content-Length'] = len(file.getvalue())
    file.close()
    return resp