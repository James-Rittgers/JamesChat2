import threading
import socketserver
import socket
import time
import queue
import subprocess

connect_dict = {}

class ListeningThread():
    def __init__(self, connection, send_queue, disconnect_flag):
        self.connection = connection
        self.send_queue = send_queue
        self.disconnect_flag = disconnect_flag

    def mainloop(self):
        '''Constantly listen for data from a client'''
        while not self.disconnect_flag.is_set():
            msg = self.connection.recv(1024)
            self.handle_message(msg)

    def send_to_client(self, msg):
        '''Send a message to the connected client'''
        self.send_queue.put(msg)

    def send_to_all(self, msg):
        '''Send a message to all connected clients'''
        for connection in connect_dict.keys():
            connect_dict[connection].put(msg)

    def handle_message(self, msg):
        '''Decode and respond to a client message'''
        msg_parse = msg.decode().split('|')
        msg_type, msg_body = msg_parse

        if msg_type == 'CHAT_MSG':
            self.send_to_all(msg)


class SendingThread():
    def __init__(self, connection, send_queue, disconnect_flag):
        self.connection = connection
        self.send_queue = send_queue
        self.disconnect_flag = disconnect_flag

    def mainloop(self):
        '''Constantly wait to send something'''
        while not self.disconnect_flag.is_set():

            queue_len = self.send_queue.qsize()

            if queue_len > 0:
                for i in range(0, queue_len):
                    msg = self.send_queue.get()
                    self.send_msg(msg)
                    self.send_queue.task_done()

    def send_msg(self, msg):
        '''Send a message to the client'''
        self.connection.send(msg)

class ThreadedRequestHandler(socketserver.BaseRequestHandler):                    

    def handle(self):
        '''Handle and keep open a client connection'''
        send_queue = queue.Queue()
        disconnect_flag = threading.Event()
        
        send_obj = SendingThread(connection=self.request, send_queue=send_queue,
                                 disconnect_flag=disconnect_flag)
        send_thread = threading.Thread(target=send_obj.mainloop)
        
        listen_obj = ListeningThread(connection=self.request, send_queue=send_queue,
                                     disconnect_flag=disconnect_flag)
        listen_thread = threading.Thread(target=listen_obj.mainloop)

        send_thread.start()
        listen_thread.start()

        connect_dict[self.client_address] = send_queue
        print(connect_dict)

        send_thread.join()
        listen_thread.join()
        
        send_queue.shutdown()
        #connect_dict.remove(f'{self.client_address}')

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# Configure server hosting
ip = socket.gethostbyname(socket.gethostname())
port = 6767
address = (ip, port)
server = ThreadedServer(address, ThreadedRequestHandler)

# Run server thread
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = False # don't hang on exit
server_thread.start()
print(f'Hosting server on {ip}:{port}')

# Keep the window open for debug messages
while True:
    time.sleep(1)
