import dearpygui.dearpygui as dpg
import socket
import threading
import time
import subprocess
# This is an edit

# Initialize the GUI
dpg.create_context()
dpg.create_viewport(title="JamesChat", height=500, width=500)
dpg.setup_dearpygui()
print('GUI_EVENT: DPG setup success')

username = None
connected = False

def send_msg(txt):
    '''Send a message to the server'''
    global connected
    print(f'Connection Status: {connected}')
    if connected == True:
        txt = f"{username}: {txt}"
        client.send(txt.encode())
        print(f'BACKEND_EVENT: sending message {txt} to server')

def recv_msg():
    '''Listen for messages from the server'''
    global connected
    print('BACKEND_EVENT: Listening thread start')
    print(f'Connection Status: {connected}')
    while True:
        if connected == True:
            try:
                print('BACKEND_EVENT: listening for server...')
                response = client.recv(1024).decode()

                if response != None:
                    add_msg(response)
                    print(f'BACKEND_EVENT: received message {response}')

                time.sleep(0.5)
            except ConnectionResetError:
                print('BACKEND_EVENT: disconnected from server')
                dpg.configure_item("disconnected_notice", show=True)
                connected = False
                continue

        else:
            break
    
            
def enter_msg():
    '''Get the message field's current value'''
    message = dpg.get_value("message_field")
    if message != "":
        print(f'GUI_EVENT: message set to "{message}"')
        dpg.set_value("message_field", "")
        send_msg(message)
        message = ""

def connect_to_server():
    '''Attempt to connect to the server'''
    global connected, client
    print(f'Connection Status: {connected}')
    try:
        if connected == False:
            # Get the server address
            ip = socket.gethostbyname("HASSLGCP1VW3")
            print(f'BACKEND_EVENT: server IP {ip}')
            port = 6767
            print(f'BACKEND_EVENT: server Port {port}')

            # Attempt connection
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))

            # Begin listening for server messages
            print('BACKEND_EVENT: attempt to listen')
            listening_thread = threading.Thread(target=recv_msg)
            listening_thread.daemon = True # don't hang on exit
            listening_thread.start()

            # Hide the disconnection dialog
            dpg.configure_item("disconnected_notice", show=False)
            print(f'BACKEND_EVENT: connected to server')
            connected = True
            print(f'Connection Status: {connected}')

            send_msg('joined the server')
            
    # Some kind of error has come up with connection
    except Exception as e:
        # Log error to console
        print(f'BACKEND_EVENT: connection attempt failed with exception {e}')

        # Show the disconnection dialog
        dpg.configure_item("disconnected_notice", show=True)
        connected = False
        print(f'Connection Status: {connected}')

def add_msg(text):
    '''Adds a message to the message history on the GUI'''
    dpg.add_text(text, parent="message_history")
    print(f'GUI_EVENT: added line "{text}" to message_history')

def set_username():
    '''Sets the username and attempts connection'''
    global username
    username = dpg.get_value("username")
    
    if username != "":
        print(f'GUI_EVENT: username set to "{username}"')
        
        # Get rid of the user_auth window and show the main window
        dpg.configure_item('user_auth', show=False)
        dpg.configure_item('primary', show=True)

        # Attempt connection
        connect_to_server()
        

# User credentials window
with dpg.window(label="User Credentials", tag='user_auth'):

    dpg.add_text("Please enter your credentials")
                          
    with dpg.group(horizontal=False, width=200, height=25):
        dpg.add_input_text(label="Username", tag="username", on_enter=True, callback=set_username)
        dpg.add_button(label="Submit", callback=set_username)
   
    print('GUI_EVENT: user_auth setup success')

# Disconnection dialog
with dpg.window(label="Disconnected", tag='disconnected_notice', show=False):
    dpg.add_text('You have disconnected from the server.')
    dpg.add_button(label='Reconnect', callback=connect_to_server)

# The main window, with sending and receiving
with dpg.window(label="main_window", tag="primary", show=False):

    with dpg.group(tag="chatroom_interface"):
    
        with dpg.child_window(tag="message_history", border=True, height=400):
                dpg.add_text("===Begin Message History===")
                print('GUI_EVENT: message_histoy window setup success')

        dpg.add_separator()

        with dpg.group(horizontal=True):
            dpg.add_input_text(label="", hint="Type message here", tag="message_field", on_enter=True, callback=enter_msg)
            dpg.add_button(label="Send", callback=enter_msg)

    print('GUI_EVENT: chatroom_interface setup success')

dpg.set_primary_window("primary", True)

# GUI shutdown
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

# Ensure backend is closed
print('connection should close')
connected = False
client.close()
sys.exit()

