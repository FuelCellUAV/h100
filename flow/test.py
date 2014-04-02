from flow import Quick
import argparse

parser = argparse.ArgumentParser(description='tester')
parser.add_argument('--i', type=str, default=':06030101210000')
args = parser.parse_args()
args.i += '\r\n'

ser = Quick()
#x=ser.send(bytearray(args.i,'ascii'))

while True:
    i = input('Enter message to send:   ')
    i += '\r\n'
    x = ser.send(bytearray(i, 'ascii'))
    print(len(x), ' bytes received')
    print(x)

