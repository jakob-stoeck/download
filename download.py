# coding: utf-8

from collections import defaultdict
from difflib import HtmlDiff
import cPickle as pickle
import gevent.queue
import gzip
import urllib2
from bs4 import BeautifulSoup

class URLWatcher:
	def __init__(self):
		self.storage = defaultdict(list)
		self.queue = gevent.queue.Queue()
		self.storageLocation = 'storage.pkl'

	def save(self, url):
		try:
			resp = urllib2.urlopen(url)
		except urllib2.URLError, e:
			print e
		text = resp.read()
		if len(self.storage[url]) == 0 or text != self.storage[url][-1]:
			self.storage[url].append(text)
			print 'saved %s' % (url,)
		else:
			print 'no change %s' % (url,)
		self.queue.put(url)

	def saveNext(self):
		url = self.queue.get(timeout=0)
		self.save(url)

	def add(self, env, start_response, url):
		if url not in self.storage:
			self.storage[url] = []
		self.queue.put(url)
		start_response('200 OK', [('Content-Type','text/html; charset=utf-8')])
		return [str('will save %s forever' % (url,))]

	def diff(self, env, start_response, url):
		left = self.storage[url][0]
		right = self.storage[url][-1]
		diff = htmlDiff(left, right)
		start_response('200 OK', [('Content-Type','text/html; charset=utf-8')])
		return [diff]

	def saveState(self, env, start_response):
		saveObject(self.storage, self.storageLocation)
		start_response('200 OK', [('Content-Type','text/plain; charset=utf-8')])
		return ['State saved']

	def loadState(self, env, start_response):
		self.storage = loadObject(self.storageLocation)
		for url in self.storage:
			self.queue.put(url)
		start_response('200 OK', [('Content-Type','text/plain; charset=utf-8')])
		return ['State loaded']

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
