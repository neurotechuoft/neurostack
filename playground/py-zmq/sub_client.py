import sys
import zmq

# Subscribers are created with ZMQ.SUB socket types. You should 
# notice that a zmq subscriber can connect to many publishers.

port = "5556"
if len(sys.argv) > 1:
    port =  sys.argv[1]
    int(port)
    
if len(sys.argv) > 2:
    port1 =  sys.argv[2]
    int(port1)

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

print("Collecting updates from weather server...")
socket.connect ("tcp://localhost:%s" % port)

if len(sys.argv) > 2:
    socket.connect ("tcp://localhost:%s" % port1)

#The current version of zmq supports filtering of messages based on topics
# at subscriber side. This is usually set via socketoption.

# Subscribe to zipcode, default is NYC, 10001
topicfilter = "10001"
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

# Process 5 updates
total_value = 0
for update_nbr in range (5):
    string = socket.recv()
    topic, messagedata = string.split()
    total_value += int(messagedata)
    print(topic, messagedata)

print("Average messagedata value for topic '%s' was %dF" % (topicfilter, total_value / update_nbr))
      

'''
Pub/Sub communication is asynchronous. If a “publish” service has been started
already and then when you start “subscribe” service,
it would not receive a number of message that was published already by the
 pub services. Starting “publisher” and “subscriber” is independent of each other.

A subscriber can in fact connect to more than one publisher, using one ‘connect’ 
call each time. Data will then arrive and be interleaved so that no single publisher 
drowns out the others.:

'''

'''
Other things to note:

- A publisher has no connected subscribers, then it will simply drop all messages.
- If you’re using TCP, and a subscriber is slow, messages will queue up on the publisher.
- In the current versions of ØMQ, filtering happens at the subscriber side, not the publisher side.

'''



