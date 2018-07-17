import socketio
from sanic import Sanic

sio = socketio.AsyncServer()

# Only if you want to use a custom server; here I want to us Sanic
app = Sanic()
sio.attach(app)


@sio.on('data_event')
def message(sid, data):
    print("EOG: ", data)


if __name__ == '__main__':
    app.run(host='localhost', port=8001)
