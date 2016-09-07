import socket
import fcntl
import struct
import serial

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', ifname[:15])
        )[20:24])

def send_lcd_serial():
    ser = serial.Serial(port='/dev/ttyAMA0' ,baudrate=9600)
    if ser.isOpen():
        ser.write(chr(12)) # Clear line and reset curson
        ser.write(str(get_ip_address('lo')))
        ser.write(chr(13))
        ser.write(str(get_ip_address('eth0')))

send_lcd_serial()
