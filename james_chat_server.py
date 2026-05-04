import threading
import socketserver
import socket
import time
import queue
import subprocess

send_all_lock = threading.RLock()
send_queue = queue.Queue()

class ListeningThread():
    
    def __init__(self, connection, connect_status, send_queue, send_lock):
        self.connection = connection
        self.connect_status = connect_status
        self.send_queue = send_queue
        self.send_lock = send_lock

    def mainloop(self):
        '''Constantly listen for data from a client'''
        raise NotImplementedError

    def send_to_client(self):
        '''Send a message to the connected client'''
        raise NotImplementedError

    def send_to_all(self):
        '''Send a message to all connected clients'''
        raise NotImplementedError

    def handle_message(self, data):
        '''Decode and respond to a client message'''
        raise NotImplementedError

    def close(self):
        '''Cleanup and terminate'''
        raise NotImplementedError
        

class SendingThread():
    def __init__(self, connection, send_queue, send_lock):
        self.connection = connection
        self.is_active = True
        self.send_queue = send_queue
        self.send_lock = send_lock

    def mainloop(self):
        '''Constantly wait to send something'''
        raise NotImplementedError

    def send_msg(self, type, body):
        '''Send a message to the client'''
        raise NotImplementedError

    def close(self):
        '''Cleanup and terminate'''
        raise NotImplementedError

class ThreadedRequestHandler(socketserver.BaseRequestHandler):                    

    def handle(self):
        '''Handle and keep open a client connection'''
        print(f'\nConnected to client {self.request} on thread {threading.current_thread()}')
        client_queue = queue.Queue()
        client_lock = threading.RLock()
        
        send_obj = SendingThread(connection=self.request, send_queue=client_queue, send_lock=client_lock)
        sending_thread = threading.Thread(target=send_obj.mainloop)
        
        listen_obj = ListeningThread(connection=self.request, sending_thread=sending_thread, sending_obj=send_obj, send_queue=client_queue, send_lock=client_lock)
        listen_thread = threading.Thread(target=listen_obj.mainloop)

        sending_thread.join()
        listening_thread.join()

class ThreadedEchoServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# Configure server hosting
ip = socket.gethostbyname(socket.gethostname())
port = 6767
address = (ip, port)
server = ThreadedEchoServer(address, ThreadedEchoRequestHandler)

# Run server thread
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = False # don't hang on exit
server_thread.start()
print(f'Hosting server on {ip}:{port}')
print(f'Server loop running in thread {server_thread.name}')

# Keep the window open for debug messages
while True:
    time.sleep(1)
