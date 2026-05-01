import threading
import socketserver
import socket
import time
import queue
import subprocess

send_all_lock = threading.RLock()
send_queue = queue.Queue()

class ThreadedEchoRequestHandler(socketserver.BaseRequestHandler):
            
    def listen(self):
        '''Listen to the client connected to this thread'''
        print(f'\nListening to client {self.request} on thread {threading.current_thread()}')
        while True:
            try:
                # Print whatever we receive from the client
                data = self.request.recv(1024)
                print(f'\nReceived "{data}" from {self.request}')
                self.send_to_all(data)
                
            except ConnectionResetError:
                # If the client disconnects unexpectedly, terminate this thread.
                # The sending thread will remain active then terminate next time
                # someone sends a message.
                print(f'\nClient {self.request} disconnected -- listening thread close')
                break
            
    def send_to_client(self, txt):
        '''Send to the client connected to this thread'''
        print(f'\nSending {txt} to client {self.request}')

        try:
            self.request.send(txt)
            
        except Exception as e:
            print(f'\nSending to client {self.request} failed with exception {e}')
            # Return the fact that we failed, and the thread will terminate in its mainloop
            return 1
        
        return 0

    def get_sending_threads(self):
        '''Return the number of open sending threads'''
        threads = 0
        
        for thread in threading.enumerate():
            if 'process_request_thread' in thread.name:
                threads += 1
                
        return threads
        

    def send_to_all(self, txt):
        '''Send a message to all clients by telling
        every open sending thread to pass on the message'''
        
        # Lock all sending threads
        send_all_lock.acquire(blocking=True)
        print(f'\nSending {txt} to all clients')

        # Get the number of active clients by finding the number
        # of active sending threads. Some clients may not be up still,
        # but the sending threads account for this and will terminate
        # if they are unable to send a messages
        num_clients = self.get_sending_threads()
        
        for client in range(0, num_clients):
            # Add the message once for every client connection. Every
            # sending thread will grab the first item it sees, then remove it
            # from the queue, then wait to be unlocked.
            send_queue.put(txt)

        # Wait for the queue to clear
        send_queue.join()

        # Release the sending threads
        send_all_lock.release()
        print(f'\nMessage {txt} sent to all clients')
                

    def handle(self):
        '''Handle and keep open a client connection'''
        print(f'\nConnected to client {self.request} on thread {threading.current_thread()}')
        listening_thread = threading.Thread(target=self.listen)
        listening_thread.start()
        sent = False

        # Keep client connection open
        while True:

            # If there is a new message to send and I haven't already sent it
            if send_all_lock.locked() and sent == False:
                print(f'\nLocked {threading.current_thread()}')
                
                # Get the new message
                msg = send_queue.get()
                
                # Send the new message
                send_status = self.send_to_client(msg)
                
                # Record that I have sent it, then remove it from the
                # task list
                send_queue.task_done()
                sent = True

                # If some kind of exception occurs while sending the message,
                # exit this loop
                if send_status == 1:
                    print(f'\nError sending to client {self.request}, sending thread close')
                    break
                
            # If there is no new message but I have sent the last one
            elif not send_all_lock.locked() and sent == True:
                
                # Reset for next time
                sent = False
                print('\nUnlocked {threading.current_thread()}')

            time.sleep(0.1)
            
        # Once this loop is done, terminate this thread
        return

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
