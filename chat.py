import tornado.ioloop
import tornado.web
import tornado.websocket
import logging
import signal
from tornado.options import options
import redis
import uuid

is_closing=False
redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)
logger=logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def signal_handler(signum, frame):
    global is_closing
    logging.info('exiting...')
    is_closing=True

def try_exit():
    global is_closing
    if is_closing:
        keys=redis_db.keys()
        for k in keys:
            redis_db.delete(k)
        tornado.ioloop.IOLoop.instance().stop()
        logging.info('exit success')



class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/index.html")

class SimpleWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    def open(self):
        self.connections.add(self)
        keys=redis_db.keys()
        for k in keys:
            logger.info("DB:{}".format(redis_db.get(k)))
            self.write_message(redis_db.get(k))

    def on_message(self, message):
        random_id=uuid.uuid4()
        redis_db.set(random_id, message)
        [client.write_message(message) for client in self.connections]

    def on_close(self):
        self.connections.remove(self)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", SimpleWebSocket)
    ])

def startTornado(port):
    logging.info("the server run on port {}".format(port))
    app=make_app()
    app.listen(port)
    tornado.ioloop.PeriodicCallback(try_exit, 100).start()
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    signal.signal(signal.SIGINT, signal_handler)
    #logging.basicConfig(level=)
    startTornado(8888)
