import zmq
context = zmq.Context()
socket = context.socket(zmq.PAIR)

address = "tcp://127.0.0.1:5000"

def client(address):
    socket.connect(address)

def server(address):
    socket.bind(address)

def send(data):
    socket.send_string(data)

def recv():
    try:
        return socket.recv(flags=zmq.NOBLOCK)
    except zmq.Again as e:
        return None
#        print("No message received yet")
