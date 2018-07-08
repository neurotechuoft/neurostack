index.js from https://github.com/OpenBCI/OpenBCI_NodeJS_Cyton/tree/master/examples/python
server.js from https://github.com/theturtle32/WebSocket-Node

At the beginning of index.js, I added a require for a WebSocketClient, followed
by a connection to our test server. When a sample is received, sampleFunc in 
index.js is called, so I added a line for sending the sample (converted to
String) to our server.
