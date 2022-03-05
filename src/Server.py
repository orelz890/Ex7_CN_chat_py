import PacketCreator
import socket
import pickle
import threading
import select  # Way to manage many connections. Gives us operating system IO capabilities and adjusts to any computer

# operating system.

HEADER_LEN = 10
SERVER_IP = "10.0.0.9"
PORT = 55000
UDP_PORT = 55001
FORMAT = 'utf-8'
# Setting buffer length
BUFFER_LEN = 500
TIMEOUT = 5

DISCONNECT_REQUEST = "!DI"
CLIENTS_LIST_REQUEST = "!CL"
FILES_LIST_REQUEST = "!FL"
NOTIFY_ALL = "!NA"
NOTIFY_PERSON = "!NP"
SPECIFIC_FILE = "!SF"
server_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_udp_socket.settimeout(TIMEOUT)


class Server:
    def __init__(self):
        # Creating a socket -> ipv4 , tcp
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Let us reconnect                                                       ????????????
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, PORT))
        # Creat a list and dict for the connecting sockets
        self.sockets_list = [self.server_socket]
        # Added a dict so we can get more information other then IP, PORT easily
        self.clients = {}
        # self.address = {}
        self.names = {'server': self.server_socket}
        self.files = ["Hello_World.txt"]
        self.timer = None
        self.min_port_value = 55000
        self.port_list = [i for i in range(1, 7)]
        self.port_dict = {}
        self.handler()

    # Func that receives a message from the client
    def receive_message(self, client_socket):
        try:
            message_header = client_socket.recv(HEADER_LEN)
            # If we got noting
            if not len(message_header):
                return False
            # else:
            user_name_len = int(message_header.decode(FORMAT).strip())
            user_name = client_socket.recv(user_name_len).decode(FORMAT)
            # print(user_name_len, user_name)
            # Now we are at the start of the action header
            action_header = client_socket.recv(HEADER_LEN)
            action_len = int(action_header.decode(FORMAT).strip())
            action = client_socket.recv(action_len).decode(FORMAT)
            action = action if action_len != 0 else "!NA"
            # print(action_len, action)
            # Now we are at the start of the message header. Get it as well
            message_header = client_socket.recv(HEADER_LEN)
            message_len = int(message_header.decode(FORMAT).strip())
            message = client_socket.recv(message_len).decode(FORMAT)
            # print(message_len, message)
            # Now we are at the start of the additional header. Get it as well
            additional_header = client_socket.recv(HEADER_LEN)
            additional_len = int(additional_header.decode(FORMAT).strip())
            additional = client_socket.recv(additional_len).decode(FORMAT)
            return {'name': user_name, 'action': action, 'msg': message, 'additional': additional}

        except:
            return False

    def handler(self):
        self.server_socket.listen(6)
        while True:
            # using the select -> select(from where to read info, where to write to, where can be errors)
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            for notified_socket in read_sockets:
                # If someone made a new connection:
                if notified_socket == self.server_socket:
                    if self.port_list:
                        client_socket, client_address = self.server_socket.accept()
                        new_port = self.min_port_value + self.port_list.pop()
                        client_socket.send(f"{new_port}".encode(FORMAT))
                        user_message = self.receive_message(client_socket)
                        # If he disconnected:
                        if user_message is False:
                            break
                        # else add him to the list & dict
                        self.port_dict[user_message['name']] = new_port
                        self.sockets_list.append(client_socket)
                        self.clients[client_socket] = user_message
                        self.names[user_message['name']] = client_socket
                        # self.address[client_socket] = client_address
                        print(f"Accepted new connection from {client_address[0]}:{client_address[1]}"
                              f" user_name:{user_message['name']}")
                        self.current_action(client_socket)
                    else:
                        print("Sorry, the chat is full please try again later!\n")
                else:
                    user_message = self.receive_message(notified_socket)
                    # If from some reason there was a problem receiving the client message delete him from the list\dict
                    if user_message is False:
                        print(f"Closed connection with {self.clients[notified_socket]['name']}")
                        self.sockets_list.remove(notified_socket)
                        del self.clients[notified_socket]
                        del self.names[self.clients[notified_socket]['name']]
                        # del self.address[notified_socket]
                        continue
                    # else get the user info from the dict
                    self.clients[notified_socket] = user_message
                    self.current_action(notified_socket)

            # remove all from the exception_sockets & clients        ???? necessary????
            for notified_socket in exception_sockets:
                self.sockets_list.remove(notified_socket)
                del self.clients[notified_socket]

    def current_action(self, notified_socket):
        user_message = self.clients[notified_socket]
        action = user_message['action']
        # print(f"received message from {user_message['name']}")
        if action == DISCONNECT_REQUEST:
            self.notify_all(notified_socket)
            self.disconnect(notified_socket)

        elif action == NOTIFY_PERSON:
            self.notify_person(user_message)

        elif action == CLIENTS_LIST_REQUEST:
            self.send_list(notified_socket, self.names)

        elif action == FILES_LIST_REQUEST:
            self.send_files_list(notified_socket, self.files)

        elif action == SPECIFIC_FILE:
            self.send_file(user_message['name'], user_message['additional'].strip())
        else:
            self.notify_all(notified_socket)

    def disconnect(self, notified_socket):
        name = self.clients[notified_socket]['name']
        print(f"Closed connection with {name}")
        self.port_list.append(self.port_dict[name] - self.min_port_value)
        self.notify_all(notified_socket)
        del self.port_dict[name]
        self.sockets_list.remove(notified_socket)
        del self.clients[notified_socket]
        del self.names[name]
        notified_socket.close()

    def notify_person(self, my_message):
        receiver_socket = self.names.get(my_message['additional'])
        if receiver_socket is not None:
            name = my_message['name'].encode(FORMAT)
            msg = my_message['msg'].encode(FORMAT)
            data = f"{len(name):<{HEADER_LEN}}".encode(FORMAT) + name + f"{len(msg):<{HEADER_LEN}}".encode(FORMAT) + msg
            receiver_socket.send(data)
            self.names[my_message['name']].send(data)

    def notify_all(self, notified_socket):
        user_message = self.clients[notified_socket]
        print(f"{user_message['msg']}")
        for client_socket in self.clients:
            # if client_socket != notified_socket:
            name = user_message['name'].encode(FORMAT)
            msg = user_message['msg'].encode(FORMAT)
            client_socket.send(f"{len(name):<{HEADER_LEN}}".encode(FORMAT) + name +
                               f"{len(msg):<{HEADER_LEN}}".encode(FORMAT) + msg)

    def send_list(self, person_socket, data: dict):
        full_msg = ""
        i = 1
        for client_name in data.keys():
            full_msg += str(i) + "> " + client_name + " "
            i += 1
        person_socket.send(f"{len(full_msg):<{HEADER_LEN}}".encode(FORMAT) + full_msg.encode(FORMAT))

    def send_files_list(self, person_socket, data: list):
        full_msg = ""
        i = 1
        for client_name in data:
            full_msg += str(i) + "> " + client_name + " "
            i += 1
        person_socket.send(f"{len(full_msg):<{HEADER_LEN}}".encode(FORMAT) + full_msg.encode(FORMAT))

    # ==================================
    #         FILE TRANSFER
    # ==================================
    def send_file(self, name, file_name):
        # print("aaaaaaaaaaaaaaaaaaa")
        global client_udp_address
        data = ""
        # print("bbbbbbbbbbbbbbbbb")
        client_sock = self.names[name]
        if file_name in self.files:
            # print("cccccccccccccccc")
            file_manager = PacketCreator.PacketCreator(file_name)
            # Sending ACK in return to the tcp request for the file
            client_sock.send("ACK".encode(FORMAT))
            # The flag makes sure we will send and receive NACK only once
            flag = False
            while True:
                if not flag:
                    try:
                        # Sending & receiving NACK, to get the client_udp_address and make sure both are listening
                        server_udp_socket.sendto("NACK".encode(FORMAT), (SERVER_IP, self.port_dict[name]))
                        print("NACK sent")
                        data, client_udp_address = server_udp_socket.recvfrom(1024)
                    finally:
                        if data:
                            if data.decode(FORMAT) == "NACK":
                                print("Received NACK2")
                                flag = True
                # Else, sending the file
                else:
                    flag = self.sending(client_udp_address, file_manager, file_name)
                    if flag:
                        break
        # File is not in the server possession
        else:
            client_sock.send("File do not exist!".encode(FORMAT))

    def sending(self, client_udp_address, file_manager, file_name):
        packet = file_manager.creat_next_packet()
        while packet:
            # Sending the current packet
            print(f"Sending {packet.sequence_num} packet")
            server_udp_socket.sendto(pickle.dumps(packet), client_udp_address)
            # Sent a new packet. therefore, Resetting the timer
            self.timer = threading.Timer(TIMEOUT, self.timer_handler, args=(packet, client_udp_address))
            self.timer.start()

            # wait for ACK or abort after a long period of time
            while True:
                try:
                    # Waiting For the packets ACK
                    print(f"\tWaiting For packet {packet.sequence_num} ACK")
                    ack_packet, address = server_udp_socket.recvfrom(4096)
                    # Make sure we got the wanted ACK from the client
                    if address == client_udp_address and pickle.loads(ack_packet).ack_num == packet.sequence_num:
                        self.timer.cancel()
                        print(f"\tGot packet {packet.sequence_num} ACK!")
                        packet = file_manager.creat_next_packet()  # update the packet
                        break
                except socket.timeout:
                    print("Socket Timeout! didnt get the desired packets in time :(")
                    self.timer.cancel()
                    return True
        end = file_manager.creat_last_packet()
        server_udp_socket.sendto(pickle.dumps(end), client_udp_address)
        print(f"{file_name} transferred successfully! :)")
        return True

    def timer_handler(self, packet, client_udp_address):
        # retransmit packet to the same client
        print(f"\tTimeout! didn't get the packet ACK in time, retransmitting packet {packet.sequence_num}")
        server_udp_socket.sendto(pickle.dumps(packet), client_udp_address)
        # Sent a new packet. therefore, Resetting the timer
        self.timer.cancel()
        self.timer = threading.Timer(TIMEOUT, self.timer_handler, args=(packet, client_udp_address))
        self.timer.start()


Server()
