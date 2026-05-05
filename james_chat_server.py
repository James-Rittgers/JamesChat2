import threading
import socketserver
import socket
import time
import queue
import subprocess
# test commit
class ListeningThread():
    def __init__(self, connection, send_queue, disconnect_flag, client_addr):
        self.connection = connection
        self.send_queue = send_queue
        self.disconnect_flag = disconnect_flag
        self.client_addr = client_addr

    def mainloop(self):
        '''Constantly listen for data from a client'''
        while not self.disconnect_flag.is_set():
            
            try:
                msg = self.connection.recv(1024)
                print(f'\nReceived {msg} from {self.client_addr}')
                self.handle_message(msg)
                
            except Exception as e:
                print(f'\nConnection to {self.client_addr} lost with error\
\n\n{e}\nlistening thread close')
                self.disconnect_flag.set()

            time.sleep(1)

    def send_to_client(self, msg):
        '''Send a message to the connected client'''
        print(f'\nAdding {msg} to {self.client_addr} queue')
        self.send_queue.put(msg)

    def send_to_all(self, msg):
        '''Send a message to all connected clients'''
        for connection in connect_dict.keys():
            conn_queue = connect_dict[connection]
            print(f'\nAdding {msg} to {connection} queue')
            conn_queue.put(msg)

    def handle_message(self, msg):
        '''Decode and respond to a client message'''
        msg_parse = msg.decode().split('|')
        msg_type, msg_body = msg_parse

        if msg_type == 'CHAT_MSG':
            self.send_to_all(msg)


class SendingThread():
    def __init__(self, connection, send_queue, disconnect_flag, client_addr):
        self.connection = connection
        self.send_queue = send_queue
        self.disconnect_flag = disconnect_flag
        self.client_addr = client_addr

    def mainloop(self):
        '''Constantly wait to send something'''
        while not self.disconnect_flag.is_set():

            queue_len = self.send_queue.qsize()

            if queue_len > 0:
                
                for i in range(0, queue_len):
                    msg = self.send_queue.get()
                    self.send_msg(msg)
                    self.send_queue.task_done()
            time.sleep(1)
            
        print(f'\nConnection to {self.client_addr} lost, sending thread close')

    def send_msg(self, msg):
        '''Send a message to the client'''
        print(f'\nSending {msg} to {self.client_addr}')
        self.connection.send(msg)

class ThreadedRequestHandler(socketserver.BaseRequestHandler):                    

    def handle(self):
        '''Handle and keep open a client connection'''
        send_queue = queue.Queue()
        disconnect_flag = threading.Event()
        
        client = self.client_address
        
        send_obj = SendingThread(connection=self.request, send_queue=send_queue,
                                 disconnect_flag=disconnect_flag, client_addr=client)
        send_thread = threading.Thread(target=send_obj.mainloop)
        
        listen_obj = ListeningThread(connection=self.request, send_queue=send_queue,
                                     disconnect_flag=disconnect_flag, client_addr=client)
        listen_thread = threading.Thread(target=listen_obj.mainloop)

        send_thread.start()
        listen_thread.start()

        connect_dict[client] = send_queue
        
        print(f'\nConnected to {client}')

        send_thread.join()
        listen_thread.join()
        
        print(f'\nConnection to {self.client_address} shutdown')
        
        send_queue.shutdown()
        del connect_dict[client]

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

connect_dict = {}

# Configure server hosting
ip = socket.gethostbyname(socket.gethostname())
port = 6767
address = (ip, port)
server = ThreadedServer(address, ThreadedRequestHandler)

# Run server thread
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()
print(f'Hosting server on {ip}:{port}')

# Keep the window open for debug messages
while True:
    time.sleep(1)
