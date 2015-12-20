from gevent import monkey
monkey.patch_all()
from gevent.wsgi import WSGIServer
from mach2 import app

http_server = WSGIServer(('', 5000), app)
http_server.serve_forever()
