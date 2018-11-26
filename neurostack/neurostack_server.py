import socketio
from sanic import Sanic


class NeurostackServer:

    def __init__(self):
        self.sio = socketio.AsyncServer()

        # Only if you want to use a custom server; here I want to us Sanic
        self.app = Sanic()
        self.sio.attach(self.app)

    def run(self):
        self.app.run(host='localhost', port=8001)
