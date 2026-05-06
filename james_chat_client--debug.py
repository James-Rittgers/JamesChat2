import socket
import threading
import time
import queue
import sys
import dearpygui.dearpygui as dpg


class ListeningThread:
    """A class to listen for and handle server messages"""

    def __init__(self):
        """Initialize a ListeningThread object"""
        self.disconnected_event = threading.Event()
        self.server_port = 6767
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.disconnected_event.set()

    def is_connected(self):
        """Return the connection status"""
        if self.disconnected_event.is_set():
            return False
        return True

    def get_connection(self):
        """Return the listener's socket object"""
        return self.connection

    def connect(self):
        """Atempt to connect to the server"""
        try:
            print("\nConnecting to server...")
            if not self.is_connected():
                ip = socket.gethostbyname("HASSLGCP1VW3")

                self.connection.connect((ip, self.server_port))
                self.disconnected_event.clear()
                print("Connection success")

        except ConnectionError:
            print("Connection failed")

    def handle_msg(self, msg):
        """Parse and respond to a message from the server"""
        msg_str = msg.decode()
        msg_type, msg_body = msg_str.split("|")

        if msg_type == "CHAT_MSG":
            disp_txt_msg(msg_body)

        elif msg_type == "CHAT_IMG":
            raise NotImplementedError

        elif msg_type == "CHAT_LOG":
            raise NotImplementedError

    def mainloop(self):
        """Lisen to the server and respond to messages"""
        print("\nListen thread start")
        while should_run():
            if self.is_connected():

                try:
                    msg = self.connection.recv(1024)

                    if msg is not None:
                        print(f"\nReceived {msg}")
                        self.handle_msg(msg)

                except ConnectionResetError:
                    print("\nDisconnected from server")
                    self.disconnected_event.set()
                    self.connection.close()
                    self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                except ConnectionAbortedError:
                    break

            else:
                self.connect()

            time.sleep(1)

        print("Listen thread close")


def send_msg(msg_type, msg_body):
    """Adds a message to the SendingThread's sending queue"""
    msg_str = f"{msg_type}|{msg_body}"
    send_queue.put(msg_str)


def send_mainloop():
    """Mainloop for the sending thread"""
    connection = listen_obj.get_connection()
    print("\nSend thread start")
    while should_run():

        if listen_obj.is_connected() and not send_queue.empty():
            msg = send_queue.get()
            print(f"Sending '{msg}'")
            connection.send(msg.encode())
            send_queue.task_done()

        time.sleep(1)

    print("Send thread close")


def should_run():
    """Check for the termination event, return True if the event is not set"""
    if terminate_event.is_set():
        print("shouldnt run")
        return False
    return True


def send_msg_field():
    """Get the message from the GUI field and add it to the send queue"""
    msg_body = dpg.get_value("message_field")
    send_msg(msg_type="CHAT_MSG", msg_body=msg_body)
    dpg.set_value("message_field", "")


def disp_txt_msg(msg):
    """Outputs a chat text message to the gui window"""
    dpg.add_text(msg, parent="message_history")


send_queue = queue.Queue()
listen_obj = ListeningThread()
send_thread = threading.Thread(target=send_mainloop, daemon=True)
listen_thread = threading.Thread(target=listen_obj.mainloop, daemon=True)
terminate_event = threading.Event()

send_thread.start()
listen_thread.start()

dpg.create_context()
dpg.create_viewport(title="JamesChat")
dpg.setup_dearpygui()

# The main window, with sending and receiving
with dpg.window(label="main_window", tag="primary", show=True):

    with dpg.group(tag="chatroom_interface"):

        with dpg.child_window(tag="message_history", border=True, height=625):
            dpg.add_text("===Begin Message History===")

        dpg.add_separator()

        with dpg.group(horizontal=True):
            dpg.add_input_text(
                label="",
                hint="Type message here",
                tag="message_field",
                on_enter=True,
                callback=send_msg_field,
            )
            dpg.add_button(label="Send", callback=send_msg_field)

dpg.set_primary_window("primary", True)

# GUI shutdown
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

terminate_event.set()
print(terminate_event.is_set())
listen_obj.connection.close()
send_thread.join()
listen_thread.join()
print("Shutdown cleanly")

sys.exit()
