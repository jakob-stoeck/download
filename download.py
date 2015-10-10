# coding: utf-8

from collections import defaultdict
from difflib import HtmlDiff
import cPickle as pickle
import gevent.queue
import gzip
import urllib2
from bs4 import BeautifulSoup
import datetime

class URLWatcher:
	def __init__(self):
		self.storage = defaultdict(list)
		self.queue = gevent.queue.Queue()
		self.storageLocation = 'storage.pkl'
		self.stopList = []

	def addAction(self, env, start_response, url):
		self.add(url)
		start_response('200 OK', [('Content-Type','text/html; charset=utf-8')])
		return [str('will save %s forever' % (url,))]

	def stopAction(self, env, start_response, url):
		self.stop(url)
		start_response('200 OK', [('Content-Type','text/html; charset=utf-8')])
		return [str('stopped %s' % (url,))]

	def diffAction(self, env, start_response, url, versionLeft='0', versionRight='-1'):
		left = self.storage[url][int(versionLeft)]['body']
		right = self.storage[url][int(versionRight)]['body']
		diff = htmlDiff(left, right)
		versions = [v['date'] for v in self.storage[url]]
		start_response('200 OK', [('Content-Type','text/html; charset=utf-8')])
		return [diff, htmlList(versions, url)]

	def saveStateAction(self, env, start_response):
		saveObject(self.storage, self.storageLocation)
		start_response('200 OK', [('Content-Type','text/plain; charset=utf-8')])
		return ['State saved']

	def loadStateAction(self, env, start_response):
		self.loadState()
		start_response('200 OK', [('Content-Type','text/plain; charset=utf-8')])
		return ['State loaded']

	def save(self, url):
		try:
			resp = urllib2.urlopen(url)
		except urllib2.URLError, e:
			print e
		text = resp.read()
		if len(self.storage[url]) == 0 or text != self.storage[url][-1]['body']:
			version = {
				'body': text,
				'date': datetime.datetime.now().isoformat()
			}
			self.storage[url].append(version)
			print 'saved %s' % (url,)
		else:
			print 'no change %s' % (url,)
		self.queue.put(url)

	def saveNext(self):
		url = self.queue.get(timeout=0)
		if url in self.stopList:
			stopList.remove(url)
		else:
			self.save(url)

	def stop(self, url):
		self.stopList.append(url)

	def add(self, url):
		if url not in self.storage:
			self.storage[url] = []
		self.queue.put(url)

	def loadState(self):
		print 'loading state ...'
		self.storage = loadObject(self.storageLocation)
		for url in self.storage:
			self.queue.put(url)
		print '... finished'


def htmlList(list, url):
	items = ''
	for k,v in enumerate(list):
		items += '<li><a href="/diff/%s/%s/%s">%s</a></li>' % (max(k-1, 0),k,url,v)
	return str('<ul>' + items + '</ul>')

def htmlBeautify(html):
	return BeautifulSoup(html, 'html.parser').prettify(formatter=None).encode('utf-8').split('\n')

def htmlDiff(left, right):
	h = HtmlDiff(wrapcolumn=80)
	return h.make_file(htmlBeautify(left), htmlBeautify(right), context=True)

def saveObject(obj, filename):
	with gzip.open(filename, 'wb') as output:
		pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def loadObject(filename):
	with gzip.open(filename, 'rb') as input:
		return pickle.load(input)
