
class Logger:
	def __init__(self):
		pass
	def message(msg):
		pass

class Config:
	def __init__(self):
		pass 

class Browser:
	def __init__(self):
		pass 
	def push_back(url):
		pass 
	def pop():
		pass 
    def has_more_urls():
		pass
	def get(url):
		pass
	def is_possible_html_content(url):
		pass
	def get_last_error():
		pass
	def get_last_file_path():
		pass
	def is_html():
		pass
	def get_html():
		pass
	def load(url):
		pass 
	def get_host_and_proto(url):
		pass 
	def get_cache_name(url):
		pass 
	def get_absolute_url(url, page):
		pass 

class Parser:
	def __init__(self):
		pass
	def get_urls(html):
		pass 
	
class Filter:
	def __init__(self):
		pass 
	def filter(absolute_url):
		pass

class Formatter:
	def __init__(self):
		pass 
	def format(html, urls_as_is, host_and_proto):
		pass 


start_url = 'http://google.ru'

browser = Browser()
browser.push_back(start_url)

parser = Parser()
logger = Logger()

while browser.has_more_urls():
	url = browser.pop()
	if browser.is_possible_html_content(url):
		if browser.get(url):
			if browser.is_html():
				html = browser.get_html()
				urls_as_is = parser.get_urls(html)
				
			else:
				logger.message("#1 loaded url: " + url + " to " + browser.get_last_file_path())
# sleep
		else:
			logger.message("can't get url: " + url)
			logger.message(browser.get_last_error())
	elif browser.load(url):
		logger.message("#2 loaded url: " + url + " to " + browser.get_last_file_path())
# sleep
	else:
		logger.message("can't load url: " + url)
		logger.message(browser.get_last_error())
		
