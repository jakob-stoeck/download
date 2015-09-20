# coding: utf-8

import gevent.monkey
gevent.monkey.patch_all()
import urllib2
from collections import defaultdict
from routes import Mapper
from difflib import HtmlDiff
# import gevent.sleep
import gevent.pool
import gevent.queue
# start with
# uwsgi --wsgi-file download.py --http :9091 --gevent 10


class URLWatcher:
	def __init__(self):
		self.storage = defaultdict(list)

	def save(self, url):
		# download
		try:
			resp = urllib2.urlopen(url)
		except urllib2.URLError, e:
			print e
		text = resp.readlines()
		# save text in storage
		if len(self.storage[url]) == 0 or text != self.storage[url][-1]:
			self.storage[url].append(text)
			print 'saved %s' % (url,)
		else:
			print 'nochange %s' % (url,)
		# register for updates
		queue.put(url)

	def htmlDiff(self, left, right):
		h = HtmlDiff(wrapcolumn=80)
		return h.make_file(left, right, context=True)

	def add(self, env, start_response, url):
		if url not in self.storage:
			self.storage[url] = []
		queue.put(url)
		start_response('200 OK', [('Content-Type','text/html')])
		return [str('will save %s forever' % (url,))]

	def diff(self, env, start_response, url, version=-1):
		diff = self.htmlDiff(self.storage[url][0], self.storage[url][-1])
		start_response('200 OK', [('Content-Type','text/html')])
		return [diff]

def downloader():
	while 1:
		gevent.sleep(1)
		try:
			url = queue.get(timeout=0)
			u.save(url)
			gevent.sleep(5)
		except gevent.queue.Empty:
			pass

def application(env, start_response):
	m = map.match(environ=env)
	fn = m.pop('action')
	return getattr(u, fn)(env, start_response, **m)

map = Mapper()
map.connect(None, '/add/{url:.+?}', action="add")
map.connect(None, '/diff/{url:.+?}', action="diff")
map.connect(None, '/diff/{url:.+?}/{version:.+?}', action="diff")

u = URLWatcher()
poolsize = 5
queue = gevent.queue.Queue()
pool = gevent.pool.Pool(poolsize)
for x in range(poolsize):
	pool.spawn(downloader)
