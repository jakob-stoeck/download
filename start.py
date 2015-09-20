# coding: utf-8

from routes import Mapper
import gevent.monkey ; gevent.monkey.patch_all()
import gevent.pool
from download import URLWatcher

# start with
# uwsgi --wsgi-file start.py --http :9091 --gevent 10

def application(env, start_response):
	m = map.match(environ=env)
	fn = m.pop('action')
	return getattr(u, fn)(env, start_response, **m)

map = Mapper()
map.connect(None, '/add/{url:.+?}', action="add")
map.connect(None, '/diff/{url:.+?}', action="diff")
map.connect(None, '/save', action="saveState")
map.connect(None, '/load', action="loadState")

def repeater(fn, minWait=1, minWaitPerUrl=5):
	while 1:
		gevent.sleep(minWait)
		try:
			fn()
			gevent.sleep(minWaitPerUrl)
		except:
			pass

u = URLWatcher()
poolsize = 5
pool = gevent.pool.Pool(poolsize)
for x in range(poolsize):
	pool.spawn(repeater, u.saveNext)
