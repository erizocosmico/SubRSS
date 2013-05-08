# -*- coding: utf-8 -*-

import store
from xml.dom import minidom
from datetime import datetime
from dateutil import parser as dateparser
import urllib2
import subs
import time
import threading

def to_unix_timestamp(date):
    return int(date.strftime('%s'))
        
def since(date):
    self_date = to_unix_timestamp(date)
    current_time = to_unix_timestamp(datetime.now())
    time_since = current_time - self_date
    if time_since < 60: # Seconds
        return str(time_since) + " segundo%s" % ("" if time_since == 1 else "s")
    elif time_since < 3600: # Minutes
        return str(time_since / 60) + " minuto%s" % ("" if (time_since / 60) == 1 else "s")
    elif time_since < 86400: # Hours
        return str(time_since / 3600) + " hora%s" % ("" if (time_since / 3600) == 1 else "s")
    else: # Days
        return str(time_since / 86400) + " dia%s" % ("" if (time_since / 86400) == 1 else "s")
        
def fetch_torrent(i, url, result):
    torrent_url = urllib2.urlopen(url).geturl()
    result.append((str(i), torrent_url.split('/')[-1].replace('.torrent', '.srt')))
    
def run_parallel(args_list):
    result = []
    threads = [threading.Thread(target=fetch_torrent, args=(i, arg, result)) for i, arg in args_list]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result

def get_rss(name):
    try:
        db = store.get_db()
        rss = db.get('subrss/user/%s/rss' % name)
        if db.exists('subrss/user/%s/rss_lastcheck' % name):
            rss_lastcheck = dateparser.parse(db.get('subrss/user/%s/rss_lastcheck' % name))
        else:
            rss_lastcheck = None
        content = urllib2.urlopen(rss).read()
        p = minidom.parseString(content)
        rss_elements = []
        torrent_urls = []
        i = 0
        for elem in p.getElementsByTagName('rss')[0].getElementsByTagName('channel')[0].getElementsByTagName('item'):
            elem_time = dateparser.parse(elem.getElementsByTagName('pubDate')[0].firstChild.nodeValue)
            if rss_lastcheck != None and rss_lastcheck > elem_time:
                break
            rss_elem = {}
            rss_elem['title'] = elem.getElementsByTagName('title')[0].firstChild.nodeValue
            torrent_urls.append((str(i), elem.getElementsByTagName('enclosure')[0].attributes['url'].value))
            rss_elem['time'] = unicode(since(elem_time))
            rss_elem['sub_url'] = subs.get_sub_url(rss_elem['title'])
            rss_elements.append(rss_elem)
            i += 1
        torrents = run_parallel(torrent_urls)
        for i, torrent in torrents:
            rss_elements[int(i)]['filename'] = torrent
        return rss, rss_lastcheck, rss_elements
    except Exception, e:
        print str(e)
        return False, False, False