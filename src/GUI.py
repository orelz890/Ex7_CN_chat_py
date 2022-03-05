import errno
import sys
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog, LEFT
from Client import Client

HOST = '127.0.0.1'
PORT = 55000
FORMAT = "utf-8"
HEADER_LEN = 10


class GUI:
    def __init__(self, flag: bool = True):
        self.nickname = "avi"
        if flag:
            self.win = tkinter.Tk()
            # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.sock.connect((HOST, PORT))
            msg = tkinter.Tk()
            msg.withdraw()
            self.nickname = simpledialog.askstring("Nickname", "please choose a nickname", parent=msg)
        self.client = Client(self.nickname)
        self.gui_done = False
        self.running = True
        self.connected = False
        self.action = "!NA"
        self.p = "for_all"
        # Constructing the GUI and Receive Threads. The first deals with requested actions and the other with the result
        if flag:
            self.gui_thread = threading.Thread(target=self.gui_loop)
        self.receive_thread = threading.Thread(target=self.receive)
        if flag:
            self.gui_thread.start()
        self.receive_thread.start()

    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.configure(bg="lightgray")
        self.win.geometry("700x650")

        self.chat_label = tkinter.Label(self.win, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.place(x=300, y=10)

        self.text_area = tkinter.scrolledtext.ScrolledText(self.win)
        self.text_area.config(state='disabled')
        self.text_area.place(x=10, y=40)

        self.msg_label = tkinter.Label(self.win, text="Message:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.place(x=293, y=470)

        self.TO = tkinter.Label(self.win, text="TO:", bg="lightgray")
        self.TO.config(font=("Arial", 12))
        self.TO.place(x=0, y=445)

        self.input_area = tkinter.Text(self.win, height=2)
        self.input_area.place(x=10, y=495)

        self.send_button = tkinter.Button(self.win, text="Send", command=self.write)
        self.send_button.config(font=("Ariel", 12))
        self.send_button.place(x=300, y=535)

        # connect button
        self.connect = tkinter.Button(self.win, text="connect", command=self.con)
        self.connect.config(font=("Ariel", 12))
        self.connect.place(x=0.0, y=0.0)

        # disconect button
        self.disconnect = tkinter.Button(self.win, text="disconnect", command=self.disconnect)
        self.disconnect.config(font=("Ariel", 12))
        self.disconnect.place(x=70.0, y=0.0)

        # private_chat button
        self.private_chat = tkinter.Button(self.win, text="private_chat", command=self.private_chat)
        self.private_chat.config(font=("Ariel", 12))
        self.private_chat.place(x=125.0, y=441.0)

        self.private_area = tkinter.Text(self.win, borderwidth=0, highlightthickness=0, width=10, height=1)
        self.private_area.config(font=("Ariel", 19))
        self.private_area.place(x=230.0, y=442)

        # public_chat button
        self.public_chat = tkinter.Button(self.win, text="public_chat", command=self.public_chat)
        self.public_chat.config(font=("Ariel", 12))
        self.public_chat.place(x=30.0, y=442.0)

        # recive_name button
        self.recive_name = tkinter.Button(self.win, text="recive_name", command=self.receive_name)
        self.recive_name.config(font=("Ariel", 12))
        self.recive_name.place(x=490.0, y=0.0)

        # files_list button
        self.files_list = tkinter.Button(self.win, text="files_list", command=self.files_list)
        self.files_list.config(font=("Ariel", 12))
        self.files_list.place(x=595.0, y=0.0)

        # download_file button
        self.download_file = tkinter.Button(self.win, text="download_file", command=self.download_file)
        self.download_file.config(font=("Ariel", 12))
        self.download_file.place(x=0.0, y=600.0)

        self.file_text = tkinter.Text(self.win, borderwidth=0, highlightthickness=0, width=10, height=1)
        self.file_text.config(font=("Arial", 19))
        self.file_text.place(x=112.0, y=601.0)

        self.clear = tkinter.Button(self.win, text="clear", command=self.clear_text)
        self.clear.config(font=("Ariel", 12))
        self.clear.place(x=600.0, y=442.0)

        self.gui_done = True
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.mainloop()

    # Function connected to the connect button
    def con(self):
        msg = f"connected \n"
        self.client.connection(msg)
        self.connected = True

    # Function connected to the disconnect button
    def disconnect(self):
        msg = f"{self.nickname} disconnected!\n"
        self.client.send_data("!DI", msg, "")
        self.connected = False

    # Function connected to the clear button
    def clear_text(self):
        self.text_area.config(state='normal')
        self.text_area.delete('1.0', 'end')
        self.text_area.config(state='disabled')

    # Function connected to the private button
    def private_chat(self):
        self.action = "!NP"
        person = self.private_area.get('1.0', 'end')
        person = person[:len(person) - 1]
        self.p = person
        self.private_area.delete('1.0', 'end')

    # Function connected to the public button
    def public_chat(self):
        self.action = "!NA"
        self.p = "for_all"

    # Function connected to the name list button
    def receive_name(self):
        self.action = "!CL"
        self.client.send_data("!CL", "", "")
        # self.client.receive_list()

    # Function connected to the file list button
    def files_list(self):
        self.action = "!FL"
        self.client.send_data("!FL", "", "")

    # Function connected to the Download file button
    def download_file(self):
        self.action = "!SF"
        message = f"{self.file_text.get('1.0', 'end')}"
        self.file_text.delete('1.0', 'end')
        print(f"The file we want is {message[:-1]} and is size is {len(message)}")
        self.client.download_file(message[:-1])

    # Function connected to the send button
    def write(self):
        message = f"{self.input_area.get('1.0', 'end')}"
        if message:
            if self.p == "for_all":
                self.input_area.delete('1.0', 'end')
                self.client.send_data("!NA", message, "")
            else:
                self.input_area.delete('1.0', 'end')
                self.client.send_data("!NP", message, self.p)

    def stop(self):
        self.running = False
        self.win.destroy()
        exit(0)

    # Thread runs on this function indefinitely until shutting the program down, waiting for the next commend.
    def receive(self):
        # If there is a new message from user
        while True:
            try:
                if self.connected is True:
                    # Commend - sending a txt msg
                    if self.action == "!NA" or self.action == "!NP":
                        packet = self.client.receive_message()
                        self.construct_msg(packet[0] + ">" + packet[1])
                    # Commend - receiving a list
                    elif self.action == "!CL" or self.action == "!FL":
                        packet = self.client.receive_list()
                        if packet:
                            self.construct_msg(packet)
                            self.action = "!NA"
                    # Commend - receiving a file
                    elif self.action == "!SF":
                        received = self.client.receive_file()
                        if received == 0:
                            self.construct_msg("File do not exist!\n")
                            self.action = "!NA"
                        if received == 1:
                            self.construct_msg("Timeout: Connection closed unexpectedly\n")
                            self.action = "!NA"

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error', str(e))
                    sys.exit()

            except Exception as e:
                print('General error', str(e))
                sys.exit()

    def construct_msg(self, packet):
        if packet:
            self.text_area.config(state='normal')
            self.text_area.insert('end', packet)
            self.text_area.yview('end')
            self.text_area.config(state='disabled')


GUI(True)
