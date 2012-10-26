
import os
import shutil
import time
import urlparse
import urllib
import urllib2
import re
from operator import truth
import android

cache_dir = '/mnt/sdcard/sl4a/sl4a-py-downloader-cache'
seconds   = 3

def quickAlert(msg,app): 
    app.dialogCreateAlert(msg)
    app.dialogSetPositiveButtonText('ok')
    app.dialogShow()

class  Logger:
        def __init__(self,app):
            self.__dict__['buffer'] = []
            self.__dict__['app'] = app
        def message(self,msg):
            print(msg)
            self.__dict__['app'].log(msg) # logcat
            self.__dict__['buffer'].append(msg)
            if len(self.__dict__['buffer']) > 30:
                self.dump()
        def dump(self):
                m = "\n".join(self.__dict__['buffer'])
                self.__dict__['buffer'] = []
                self.__dict__['app'].makeToast(m)

class Config:
    def __init__(self):
        pass 

class Browser:
    def __init__(self, cache_dir):
        self.__dict__['queue'] = []
        self.__dict__['cache_dir'] = cache_dir
        self.__dict__['last_fpath'] = ''
        self.__dict__['last_err'] = ''
        self.__dict__['html'] = ''
        self.__dict__['is_html'] = 0

    def push_back(self, url):
        self.__dict__['queue'].append(url)

    def shift(self):
        url = self.__dict__['queue'][0]
        self.__dict__['queue'] = self.__dict__['queue'][1:]
        return url

    def has_more_urls(self):
        return len(self.__dict__['queue']) > 0

    def get(self,url):
        logger.message(url)
        cname = self.get_cache_name(url)
        if len(cname) > 0:
            file_path = self.__dict__['cache_dir'] + '/' + cname
            self.__dict__['last_fpath'] = file_path
            try:
                r = urllib2.urlopen(url)
                if re.search("text/html", r.headers.getheader("Content-type", "text/html")):
                    self.__dict__['is_html'] = 1
                else:
                    self.__dict__['is_html'] = 0
                self.__dict__['html'] = r.read()
            except urllib2.HTTPError as err:
                self.__dict__['last_err'] = str(err)
                return 0
            return 1
        else:
            logger.message("Empty cache name for '" + url + "'")
            return 0

    def exists_at_cache(self,url):
        return os.path.exists(self.__dict__['cache_dir'] + '/' + self.get_cache_name(url))

    def is_possible_html_content(url):
        return not truth(re.search('\.(css|js|png|gif|jpg)', url))

    def get_last_error(self):
        return self.__dict__['last_err']

    def get_last_file_path(self):
        return self.__dict__['last_fpath']

    def get_html(self):
        return self.__dict__['html']

    def load(self, url):
        cname = self.get_cache_name(url)
        res = 1
        if len(cname) > 0:
            file_path = self.__dict__['cache_dir'] + '/' + cname
            basedir = re.sub("[^\/]+$", "", file_path)
            self.__dict__['last_fpath'] = file_path
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            try:
                r = urllib2.urlopen(url)
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(r,f)
            except urllib2.HTTPError as err:
                self.__dict__['last_err'] = str(err)
                res = 0
            return res
        else:
            logger.message("Empty cache name for '" + url + "'")
            return 0

    def get_cache_name(url):
        url = re.sub('^http[s]?\://', '', url)
        n = [];
        dirs = re.split('/', url)
        for i in range(len(dirs)):
            if len(dirs[i]) > 0:
                r = urllib.quote_plus(dirs[i])
                n.append(r)
            elif i == len(dirs):
                n.append('index')
        if (len(n) == 1):
            n.append('index')
        if Browser.is_possible_html_content(url):
            v = n[len(n) - 1]
            if not re.search("\.(htm|html|shtml|phtml)$", v):
                n[len(n) - 1] = v + '.html'
        return "/".join(n)

    def get_absolute_url(url, page):
        if truth(re.search('^http[s]?\:\/\/', url)):
            return url
        return urlparse.urljoin(page,url)
    is_possible_html_content=staticmethod(is_possible_html_content)
    get_cache_name=staticmethod(get_cache_name)
    get_absolute_url=staticmethod(get_absolute_url)

class Parser:
    def get_urls(html):
        result = []
        urls = re.findall('<[^>]+\x20(src|href)\s*\=\s*["\']{0,1}([^\"\'\x20>]+)["\']{0,1}[^>]*>', html, re.I)
        for link in urls:
            result.append(link[1])
        return result
    get_urls = staticmethod(get_urls)
    
class Filter:
    def filter(absolute_url, page):
            if not Browser.is_possible_html_content(absolute_url):
                return 0
            host = re.search('^http[s]?\://([^/]+)', absolute_url)
            if host == None:
                #logger.message("unknown host at url: " + absolute_url)
                #logger.message("filtered: " + absolute_url + ' from page: ' + page)
                return 1
            host = host.group(1)
            host = re.sub('^www\.', '', host)
            page_host = re.search('^http[s]?\://([^/]+)', page)
            page_host = page_host.group(1)
            page_host = re.sub('^www\.', '', page_host)
            if page_host == host:
                dirs      = re.split('/', Browser.get_cache_name(absolute_url))
                page_dirs = re.split('/', Browser.get_cache_name(page))
                if len(dirs) > len(page_dirs):
                    return 0
                elif len(dirs) == len(page_dirs):
                    if '/'.join(dirs[:-1]) == '/'.join(page_dirs[:-1]):
                        return 0
            #logger.message("filtered: " + absolute_url + ' from page: ' + page)
            return 1
    filter = staticmethod(filter)
    
class Formatter:
    def encode_cache_url(relative_url):
        dirs = re.split('/', relative_url)
        r = []
        for d in dirs:
            r.append(urllib.quote_plus(d))
        return "/".join(r)
        
    def get_cache_url(absolute_url, page):
        page_cname = Browser.get_cache_name(page)
        page_cname_rel = re.sub('[^/]+/', '../', page_cname)
        page_cname_rel = re.sub('/[^/]+$', '', page_cname_rel)
        page_host  = re.search('^http[s]?\://([^/]+)', page)
        page_host  = page_host.group(1)
        page_host  = re.sub('^www\.', '', page_host)
        host = re.search('^http[s]?\:\/\/([^/]+)', absolute_url)
        if host == None:
            #logger.message("unknown host at url: " + absolute_url)
            return None
        host = host.group(1)
        host = re.sub('^www\.', '', host)
        if host != page_host:
            cname = Browser.get_cache_name(absolute_url)
            cname = Formatter.encode_cache_url(cname)
            relative_url = page_cname_rel + '/' + cname
        else:
            cname = Browser.get_cache_name(absolute_url)
            cname = Formatter.encode_cache_url(cname)
            relative_url = page_cname_rel + '/' + cname
        return relative_url
        
    def format(html, urls_as_is, page):

        for url in urls_as_is:
            absolute_url = Browser.get_absolute_url(url, page)
            relative_url = Formatter.get_cache_url(absolute_url, page)
            if relative_url != None:
                html = html.replace('"' + url + '"', '"' + relative_url + '"')
                html = html.replace("'" + url + "'", "'" + relative_url + "'")
                html = html.replace('=' + url + '>', '=' + relative_url + '>')
                html = html.replace('=' + url + ' ', '=' + relative_url + ' ')
        return html
    format=staticmethod(format)
    get_cache_url=staticmethod(get_cache_url)
    encode_cache_url=staticmethod(encode_cache_url)


app = android.Android()

start_url = app.dialogGetInput("Start Url", "Type please start URL here", "http://example.com").result
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

logger = Logger(app)

browser = Browser(cache_dir)
browser.push_back(start_url)

while browser.has_more_urls():
    url = browser.shift()
    if not browser.exists_at_cache(url):
        if browser.is_possible_html_content(url):
            if browser.get(url):
                if browser.is_html:
                    html = browser.get_html()
                    urls_as_is = Parser.get_urls(html)
                    for found_url in urls_as_is:
                        abs_url = browser.get_absolute_url(found_url,url)
                        if not Filter.filter(abs_url, url):
                            browser.push_back(abs_url);
                    
                    formatted = Formatter.format(html,urls_as_is,url)
                    file_path = cache_dir + '/' + Browser.get_cache_name(url)
                    basedir = re.sub("[^\/]+$", "", file_path)
                    if not os.path.exists(basedir):
                        os.makedirs(basedir)
                    f = open(file_path, 'w')
                    f.write(formatted)
                    f.close()
                    time.sleep(seconds)
                else:
                    if browser.load(url):
                        logger.message(url)
                    else:
                        logger.message("can't get url: " + url)
                        logger.message(browser.get_last_error())
            else:
                logger.message("can't get url: " + url)
                logger.message(browser.get_last_error())
        elif browser.load(url):
            logger.message(url)
            # don't sleep for load resources 
        else:
            logger.message("can't load url: " + url)
            logger.message(browser.get_last_error())
    else:
        logger.message("url " + url + " already exists")
logger.dump()
app.vibrate()
quickAlert("download from start URL: " + start_url + " completed", app)
