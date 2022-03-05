import zlib
import numpy

PACKET_SIZE = 500


def do_crc(s):
    n = zlib.crc32(s)
    return n & 0xffffffff


class ACK:
    def __init__(self, ack_num):
        self.check_sum = numpy.uint16(ack_num)
        self.ack_num = numpy.uint32(ack_num)


class Packet:
    def __init__(self, sequence_num, data):
        self.check_sum = numpy.uint32(do_crc(bytes(sequence_num)))
        self.sequence_num = numpy.uint32(sequence_num)
        self.data = data


class PacketCreator:

    def __init__(self, file_name):
        self.sequence_num = 1
        self.file_name = file_name
        self.file = open(self.file_name, 'rb')

    def creat_packet(self, data_string):
        packet = Packet(self.sequence_num, data_string)
        self.sequence_num += 1
        return packet

    def creat_last_packet(self):
        packet = Packet(0, "")
        return packet

    def creat_next_packet(self):
        packet = self.get_next_packet()
        if packet:
            packet = Packet(self.sequence_num, packet)
            self.sequence_num += 1
            return packet
        return None

    def get_next_packet(self):
        packet_data = []
        for i in range(PACKET_SIZE):
            line = self.file.read(1)
            if not line:
                break
            packet_data.append(line)
        if packet_data:
            return packet_data
        return None