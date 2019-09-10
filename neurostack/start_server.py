from server.p300_server import P300Service


# Run neurostack server on localhost:8001
service = P300Service()
service.initialize_handlers()

service.app.run(host='localhost', port=8001)
