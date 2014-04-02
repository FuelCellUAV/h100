#!/usr/bin/env python3

import binascii, multiprocessing, serial, time


class Quick:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyAMA0', 38400, timeout=2, rtscts=1)

    def send(self, data):
        print(self.ser.write(data), ' bytes sent')
        #        x=''
        time.sleep(0.25)
        # while True:
        x = (self.ser.read(10))
        # if x: break
        return x


class FlowBus232:
    def __init__(self):
        self.bus = serial.Serial("/dev/ttyAMA0", 38400, timeout=5)

    def readLine(self):
        parse_msg = ""
        raw_bus_data = self.bus.read()
        if raw_bus_data == ':':
            while raw_bus_data != b'\r':  # "\r" = end of command/exit code
                parse_msg += raw_bus_data
                if raw_bus_data == b':':  # ":" = New command so save and restart buffer ## not sure this will be needed.
                    parse_msg = b""
                raw_bus_data = self.bus.read()

            return parse_msg

        else:
            return False

    @staticmethod
    def decoder(msg, pointer, length):
        return binascii.a2b_hex(msg[pointer:pointer + length])

    @staticmethod
    def parse232(msg):
        data = decoder(msg, 0, 1)
        length = int(data, 16)

        if length is 1:
            # Special error message
            return -1 * int(decoder(msg, 2, 1), 16)  ########## UNSURE ABOUT THE LOGIC HERE
        else:
            data[0:] = decoder(msg, 4, length - 4)

        return data

    @staticmethod
    def getValue(data, pointer):
        dataType = data[pointer]

        if b'00' in dataType:
            #char
            return int.from_bytes(data[pointer + 2:pointer + 4],
                                  byteorder='big')  ########### not sure why you want ints returned?

        elif b'20' in dataType:
            #int
            return int.from_bytes(data[pointer + 2:pointer + 6], byteorder='big')

        elif b'40' in dataType:
            #long
            return int.from_bytes(data[pointer + 2:pointer + 10], byteorder='big')

        elif b'60' in dataType:
            #string
            length = int.from_bytes(data[pointer + 2:pointer + 4], byteorder='big')
            mystring = b""
            for x in range(5, 5 + length - 1, 2):
                mystring += data[x:x + 2]

            return mystring


    def parse(self, data):
        length = data[0]
        node = data[1]
        cmd = data[2]

        if cmd is 0:
            #status message
            status = data[3]
            if status != 0:
                index = data[4]

        elif cmd is 2:
            #incoming data
            return getValue(data, 4)

        else:
            return False

    def run(self):
        while True:
            msg = readLine()
            if msg is False:
                # Start the while loop again
                continue

            data = parse232(msg)

            myValue = parse(data)

            if (myValue):
                print(myValue)
            else:
                print("FAIILLLL, You Suck")


class FlowBus232Daemon(FlowBus232, multiprocessing.Process):
    val = multiprocessing.Array('d', range(8))

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.threadId = 1
        self.Name = 'FlowBus232'
