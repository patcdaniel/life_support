'''
Author: Patrick Daniel

GOAL: Make a robust class to handle serial data inputs the ADAM Modules by a Rasperberry Pi. The emphasis
has to be on writting solid and easy to understand code.

Classes:
    commSupport: This should handle the serial communication and store the most recent status
    timer: These will handle the timers that are important for trimming the water levels
    email (possibly)

'''
import serial,sys,time,numpy


class LifeSupport(object):

    def __init__(self):
        self.ser = serial.Serial()
        self.__commPort = self.which_port()
        self.__initialize_serial()
        self.__status = ''
        self.pump_timer = Timer()
        self.circulation_timer = Timer()

    def get_comm_port(self):
        return self.__commPort

    def get_status(self):
        return self.__status

    def which_port(self):
        '''
        This function exists for debugging on a Mac vs a Raspberry Pi.
        :return: commPort (string): the location of the USB-Serial adapter
        '''

        if sys.platform == 'darwin':
            # Mac OS
            commport = '/dev/tty.usbserial'
        else:
            commport = '/dev/ttyUSB0'
        return commport

    def __initialize_serial(self):
        '''
        Set up the object used for serial communication with the ADAM Module
        All of the setup options are static and should not be part of the API
        :return:
        '''
        self.ser.setPort(self.__commPort)
        self.ser.setBaudrate(9600)
        self.ser.setParity(serial.PARITY_NONE)
        self.ser.setByteSize(serial.EIGHTBITS)

    def open_com(self):
        try:
            self.ser.open()
        except OSError as (errno, strerror):
            print "Erorr: {0}".format(strerror)
            print "Can't open serial port. Shutting down"
            sys.exit() # Quit the program

    def read_comm(self):
        cmd = '$026\r\n'  # Ask what switches are open
        self.ser.write(cmd)
        out = ''
        # let's wait one second before reading output (let's give device time to answer)
        time.sleep(2)
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1)
        if out != '':
            self.__status = out
        else:
            self.__status = 'ERROR, no reading'


class Timer(object):

    def __init__(self):
        self.status = False
        self.end_time = numpy.nan

    def set_timer(self,length):
        self.status = True
        self.end_time = time.time() + length

    def is_time_up(self):
        return time.time() - self.end_time > 0
        # Need to toggle the status too