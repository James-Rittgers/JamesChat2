import threading
import socketserver
import socket
import time
import queue
import subprocess

send_all_lock = threading.RLock()
send_queue = queue.Queue()

class ListeningThread():
    
    def __init__(self, connection, sending_thread, sending_obj):
        self.connection = connection
        self.sending_thread = sending_thread
        self.sending_obj = sending_obj
        

class SendingThread():
    def __init(self, connection):
        self.connection = connection
        self.is_active = True

class ThreadedRequestHandler(socketserver.BaseRequestHandler):                    

    def handle(self):
        '''Handle and keep open a client connection'''
        print(f'\nConnected to client {self.request} on thread {threading.current_thread()}')
        send_obj = SendingThread(connection=self.request)
        sending_thread = threading.Thread(target=send_obj.mainloop)
        listen_obj = ListeningThread(connection=self.request, sending_thread=sending_thread, sending_obj=send_obj)

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
