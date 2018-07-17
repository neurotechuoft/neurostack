from socketIO_client import SocketIO

if __name__ == '__main__':
    socket_client = SocketIO("localhost", 8001)
    socket_client.connect()

    while True:
        socket_client.emit("data_event", "hello")
