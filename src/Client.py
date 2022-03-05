import socket
import sys
import pickle
import zlib
import numpy
from PacketCreator import Packet, ACK, do_crc

HEADER_LEN = 10
IP = "10.0.0.9"
SERVER_IP = "10.0.0.9"
PORT = 55000
UDP_PORT = 55001
SERVER_UDP_ADDRESS = (IP, UDP_PORT)
FORMAT = 'utf-8'
BUF_SIZE = 4096
# Setting timeout
TIMEOUT = 20
legal_actions = ["!NA", "!NP", "!CL", "!FL", "!DI", "!SF"]
client_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


class Client:
    def __init__(self, nickname: str = "avi"):
        # Getting the user name
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = client_udp_socket
        self.nickname = nickname
        self.user_name = self.nickname.encode(FORMAT)
        self.user_header = f"{len(self.user_name):<{HEADER_LEN}}".encode(FORMAT)
        self.file_to_download = ""
        self.curr_seq_num = 1
        self.last_ack = -1
        self.file_exist = False
        self.last_data = ""

    def get_port(self):
        return UDP_PORT

    def connection(self, msg):
        self.client_socket.connect((IP, PORT))
        self.client_socket.setblocking(False)
        actions = f"Welcome to our chat room!:)\n"
        print(actions)
        flag = True
        port_udp = ""
        # Getting the UDP port number from the server
        while True:
            try:
                port_udp = self.client_socket.recv(1024)
                if port_udp:
                    UDP_PORT = int(port_udp.decode(FORMAT)[:5])
                    print(UDP_PORT, type(UDP_PORT))
                    client_udp_socket.bind((IP, UDP_PORT))
                    client_udp_socket.settimeout(TIMEOUT)
                    flag = False
                    break
            finally:
                if flag:
                    continue
        self.send_data("!NA", msg, "")

    # Function that encodes and sends the data we want (in this format - Header|Data|Header2|Data2..)
    # The Header contains the next data length, so we will know how much to receive at a given time.
    def send_data(self, client_action, client_msg, additional):
        client_action = client_action.encode(FORMAT)
        action_header = f"{len(client_action):<{HEADER_LEN}}".encode(FORMAT)

        client_msg = client_msg.encode(FORMAT)
        msg_header = f"{len(client_msg):<{HEADER_LEN}}".encode(FORMAT)

        additional_data = additional.encode(FORMAT)
        additional_header = f"{len(additional_data):<{HEADER_LEN}}".encode(FORMAT)

        final = self.user_header + self.user_name + action_header + client_action + msg_header + client_msg + \
                additional_header + additional_data
        self.client_socket.send(final)

    # Receives decodes and returns a message (receives in this format - Header|Name|Header|msg , returns (name, msg))
    def receive_message(self):
        user_header = self.client_socket.recv(HEADER_LEN).decode(FORMAT)

        if not len(user_header):
            return False
        # else:
        # Get the user name
        user_name_len = int(user_header.strip())
        # user_name_len = int(user_header.decode(FORMAT).strip())
        user_name = self.client_socket.recv(user_name_len).decode(FORMAT)
        # Now we are at the start of the message header. Get it as well
        message_header = self.client_socket.recv(HEADER_LEN)
        message_len = int(message_header.decode(FORMAT).strip())
        message = self.client_socket.recv(message_len).decode(FORMAT)
        print(f"{user_name}> {message}")
        sys.stdout.flush()

        return user_name, message

    def receive_list(self):
        try:
            msg_head = self.client_socket.recv(HEADER_LEN)
            if msg_head:
                msg_len = int(msg_head.decode(FORMAT).strip())
                data = self.client_socket.recv(msg_len).decode(FORMAT)
                full_msg = "List:\n" + data + "\n"
                print(full_msg)
                sys.stdout.flush()
                return full_msg
        except:
            return False

    # ==================================
    #         FILE TRANSFER
    # ==================================

    # This function duty is to ask the server for a specific file with the TCP connection. If he has that file, send
    # a msg through the UDP socket so the server will get its address.
    def download_file(self, file_name):
        global server_udp_address, data
        data2 = ""
        self.send_data("!SF", "", file_name)
        while True:
            try:
                data, server_address = self.client_socket.recvfrom(1024)
                if data.decode(FORMAT) == "ACK":
                    print("ACK received")
                    self.file_to_download = file_name
                    self.file_exist = True
                    while True:
                        try:
                            data2, server_udp_address = client_udp_socket.recvfrom(1024)
                        finally:
                            if data2:
                                if data2.decode(FORMAT) == "NACK":
                                    print("Client sent NACK")
                                    client_udp_socket.sendto("NACK".encode(FORMAT), server_udp_address)
                                    return
            finally:
                if data.decode(FORMAT) == "File do not exist!":
                    self.file_to_download = "File do not exist!"
                    print("File do not exist!")
                    return

    # Function that receives the file if it exist in the server. The GUI thread will enter this function until it
    # will get a different request waiting to received the file from the moment the download file will be pressed
    def receive_file(self):
        if self.file_to_download == "File do not exist!":
            # print("aaaaa")
            self.file_exist = False
            self.file_to_download = ""
            return 0
        if self.file_exist:
            # print("bbbb")
            try:
                received = self.receive_packet()
            except socket.timeout:
                print("Timeout: Connection closed unexpectedly")
                self.file_exist = False
                self.file_to_download = ""
                return 1

            if not received:
                return 2

    # Function that receives a packet at a time and writing it to our new file.
    def receive_packet(self):
        byte, address = client_udp_socket.recvfrom(BUF_SIZE)
        packet: Packet = pickle.loads(byte)
        print("Received packet ", packet.sequence_num)
        calculate_check_sum = numpy.uint32(do_crc((bytes(packet.sequence_num))))
        # Check if the checksum matches and its not the last packet
        if packet.check_sum != calculate_check_sum and packet.sequence_num != 0:
            print(f"\tPacket {packet.sequence_num} checksum don't match, Discard.")
            return True
        # Check if its the last packet
        if packet.sequence_num == 0:
            print(f"File received successfully! The last data we received is: {self.last_data}")
            # self.send_data("!NP", "File received successfully!\n", self.nickname)
            self.last_data = ""
            return False
        # If we got here it means we got a valid data from the server, so write!
        self.write_to_file(packet)
        # Send ack for the received packet
        ack_packet = ACK(packet.sequence_num)
        client_udp_socket.sendto(pickle.dumps(ack_packet), address)
        return True

    def write_to_file(self, packet):
        with open(self.file_to_download[:-4] + "2" + self.file_to_download[-4:], "ab") as file:
            for i in range(len(packet.data)):
                file.write(packet.data[i])
                self.last_data = packet.data[i]
            print(f"\tPacket {packet.sequence_num} received!")
            file.flush()
