import unittest
from src.Client import Client
import time

NAME = "orel"
c = Client(NAME)


class Test(unittest.TestCase):

    def test_client(self):
        global data
        # Checking orel connection
        self.assertEqual("orel", c.nickname)
        msg1 = f"connected \n"
        c.connection(msg1)
        time.sleep(0.5)
        name, msg = c.receive_message()
        self.assertEqual("orel", name)
        self.assertEqual("connected ", msg[:-1])
        self.assertTrue(55000 < c.get_port() < 55010)

        # Checking the corresponding between client and server
        c.send_data("!NA", "fdb", "")
        time.sleep(0.5)
        name, msg = c.receive_message()
        self.assertEqual("orel", name)
        self.assertEqual("fdb", msg)
        c.send_data("!NA", "Hello", "")
        time.sleep(0.5)
        msg = c.receive_message()
        self.assertEqual((NAME, "Hello"), msg)
        c.send_data("!NA", "world", "")
        time.sleep(0.5)
        msg = c.receive_message()
        self.assertEqual((NAME, "world"), msg)
        c.send_data("!NA", "Do you want to be my friend", "")
        time.sleep(0.5)
        msg = c.receive_message()
        self.assertEqual((NAME, "Do you want to be my friend"), msg)

        # Checking the client functions:

        # Get file list
        c.send_data("!FL", "fdb", "")
        time.sleep(0.5)
        files = c.receive_list()
        self.assertEqual("List:\n1> Hello_World.txt \n", files)

        # Get client list
        c.send_data("!CL", "fdb", "")
        time.sleep(0.5)
        clients = c.receive_list()
        self.assertEqual("List:\n1> server 2> orel \n", clients)

        # Checking the disconnect func:
        c.send_data("!DI", "Orel disconnected", "")
        time.sleep(0.5)
        name, msg = c.receive_message()
        self.assertEqual("orel", name)
        self.assertEqual("Orel disconnected", msg)
