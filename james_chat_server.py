import threading
import socketserver
import socket
import time
import queue


class Client:
    """Represents a connected client"""

    def __init__(self, connection, addr, uname):
        """Initialize a Client object"""
        self.addr = addr
        self.hostname = socket.gethostbyaddr(addr[0])
        self.connection = connection
        self.send_queue = queue.Queue()
        self.disconnect_flag = threading.Event()
        self.uname = uname

    def is_connected(self):
        """Return True if the client is not disconnected"""
        if self.disconnect_flag.is_set():
            return False

        return True

    def get_hostname(self):
        """Return the client's hostname"""
        return self.hostname

    def get_queue(self):
        """Return the client's outgoing message queue"""
        return self.send_queue

    def get_addr(self):
        """Return the client's connection address"""
        return self.addr

    def get_connection(self):
        """Return the request socket for this client"""
        return self.connection

    def get_uname(self):
        """Return the client's username"""
        return self.uname

    def disconnect(self):
        """Set the disconnection flag of this client to True"""
        self.disconnect_flag.set()
        self.send_queue.shutdown()


class ListeningThread:
    """Class to handle listening for client messages"""

    def __init__(self, client_obj):
        """Initialize ListeningThread object"""
        self.client = client_obj
        self.connection = client_obj.get_connection()
        self.send_queue = client_obj.get_queue()
        self.client_addr = client_obj.get_addr()
        self.uname = client_obj.get_uname()

    def mainloop(self):
        """Constantly listen for data from a client"""
        while self.client.is_connected():

            try:
                msg = self.connection.recv(1024)
                print(f"\nReceived {msg} from {self.client_addr}")
                self.handle_message(msg)

            except ConnectionError as e:
                print(f"\nConnection to {self.client_addr} lost with error\
\n\n{e}\nlistening thread close")
                self.client.disconnect()

            time.sleep(1)

    def send_to_client(self, msg):
        """Send a message to the connected client"""
        print(f"\nAdding {msg} to {self.client_addr} queue")
        self.send_queue.put(msg)

    def handle_message(self, msg):
        """Decode and respond to a client message"""
        msg_parse = msg.decode().split("|")
        msg_type, msg_body = msg_parse

        if msg_type == "CHAT_MSG" or msg_type == "CHAT_IMG":
            send_to_all(msg_type, self.uname, msg_body)

        elif msg_type == "CHAT_LOG":
            raise NotImplementedError


class SendingThread:
    """Class to handle sending messages to a client"""

    def __init__(self, client_obj):
        """Initialize SendingThread object"""
        self.client_obj = client_obj
        self.connection = client_obj.get_connection()
        self.send_queue = client_obj.get_queue()
        self.client_addr = client_obj.get_addr()
        self.client_uname = client_obj.get_uname()

    def mainloop(self):
        """Constantly wait to send something"""
        while self.client_obj.is_connected():

            queue_len = self.send_queue.qsize()

            if queue_len > 0:
                for item in range(0, queue_len):
                    msg = self.send_queue.get()
                    self.send_msg(msg)
                    self.send_queue.task_done()
            time.sleep(1)

        print(f"\nConnection to {self.client_addr} lost, sending thread close")

    def send_msg(self, msg):
        """Send a message to the client"""
        print(f"\nSending {msg} to {self.client_addr}")
        self.connection.send(msg)


class ThreadedRequestHandler(socketserver.BaseRequestHandler):
    """Handles a client connection"""

    def handle(self):
        """Handle and keep open a client connection"""
        
        uname = known_hosts[socket.gethostbyaddr(self.client_address[0])[0]]
            
        self.client_obj = Client(self.request, self.client_address, uname)

        self.send_obj = SendingThread(self.client_obj)
        self.send_thread = threading.Thread(target=self.send_obj.mainloop)

        self.listen_obj = ListeningThread(self.client_obj)
        self.listen_thread = threading.Thread(target=self.listen_obj.mainloop)

        print(f"\nConnected to {self.client_obj.get_hostname()}")
        

        clients.append(self.client_obj)

        self.send_thread.start()
        self.listen_thread.start()
        send_to_all('CHAT_MSG', 'SERVER', f'{uname} has joined the chat')
        # Wait until client connection closes
        self.send_thread.join()
        self.listen_thread.join()
        send_to_all('CHAT_MSG', 'SERVER', f'{uname} has left the chat')

        print(f"\nConnection to {self.client_obj.get_hostname()} shutdown")

        clients.remove(self.client_obj)



class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Socketserver boilerplate"""


def send_to_all(msg_type, origin, msg_body):
        """Send a message to all connected clients"""
        msg = f'{msg_type}|{origin}|{msg_body}'.encode()
 
        for connection in clients:
            
            conn_queue = connection.get_queue()
            print(f"\nAdding {msg} to {connection} queue")
            try: 
                conn_queue.put(msg)
            except queue.ShutDown:
                print('Attempted to send to a disconnected client')
            
clients = []

known_hosts = {'HASSLGCP1VW3.acs.local': 'jam'}

# Configure server hosting
ip = socket.gethostbyname(socket.gethostname())
PORT = 6767
address = (ip, PORT)
server = ThreadedServer(address, ThreadedRequestHandler)

# Run server thread
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()
print(f"Hosting server on {ip}:{PORT}")

# Keep the window open for debug messages
while True:
    time.sleep(1)
