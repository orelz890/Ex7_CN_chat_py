import unittest
from src.Client import Client
import time

FORMAT = 'utf-8'
NAME = "aviel"
c = Client(NAME)


# ================================================================
# In order to start the test we need to open the server first!
# Please open the CMD in this folder and write "py Server.py"
# Now, we can start the test! :)
# ================================================================


class Test(unittest.TestCase):

    def test_client(self):
        global data
        # Checking aviel connection
        self.assertEqual("aviel", c.nickname)
        msg1 = f"connected \n"
        c.connection(msg1)
        time.sleep(0.5)
        name, msg = c.receive_message()
        self.assertEqual("aviel", name)
        self.assertEqual("connected ", msg[:-1])
        self.assertTrue(55000 < c.get_port() < 55010)

        #   Get a file

        # File dont exist:
        time.sleep(0.5)
        c.send_data("!SF", "", "aaa")
        time.sleep(0.5)
        ans = c.client_socket.recv(1024)
        self.assertEqual("File do not exist!", ans.decode(FORMAT))

        # File do exist:
        c.send_data("!SF", "", "Hello_World.txt")
        time.sleep(0.5)
        ans = c.client_socket.recv(1024)
        self.assertEqual("ACK", ans.decode(FORMAT))
        c.file_to_download = "Hello_World.txt"
        c.file_exist = True
        time.sleep(0.5)
        data, server_udp_address = c.udp_socket.recvfrom(1024)
        self.assertEqual("NACK", data.decode(FORMAT))
        c.udp_socket.sendto("NACK".encode(FORMAT), server_udp_address)
        time.sleep(2)
        flag = True
        while flag:
            ans = c.receive_file()
            if ans:
                if 0 <= ans <= 2:
                    flag = False
        with open("Hello_World2.txt", "rb"):
            self.assertTrue(True)

        # ==============================================================================================================
        # In order to check a big file transfer please add "BigFile.txt" to the server file list and then test the below
        # ==============================================================================================================

        # c.file_to_download = ""
        # c.file_exist = False
        # # Big file transfer:
        #
        # c.send_data("!SF", "", "BigFile.txt")
        # time.sleep(0.5)
        # ans = c.client_socket.recv(1024)
        # self.assertEqual("ACK", ans.decode(FORMAT))
        # c.file_to_download = "BigFile.txt"
        # c.file_exist = True
        # time.sleep(0.5)
        # data, server_udp_address = c.udp_socket.recvfrom(1024)
        # self.assertEqual("NACK", data.decode(FORMAT))
        # c.udp_socket.sendto("NACK".encode(FORMAT), server_udp_address)
        # time.sleep(2)
        # flag = True
        # while flag:
        #     ans = c.receive_file()
        #     if ans:
        #         if 0 <= ans <= 2:
        #             flag = False
        # with open("BigFile2.txt", "rb"):
        #     self.assertTrue(True)
        # c.file_to_download = ""
        # c.file_exist = False
