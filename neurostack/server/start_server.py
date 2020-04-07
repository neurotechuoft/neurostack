from server.server import NeurostackServer


# Run neurostack server on localhost:8001
service = NeurostackServer()
service.initialize_handlers()

service.app.run(host='localhost', port=8001)
