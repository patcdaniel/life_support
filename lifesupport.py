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
import plotly.plotly as py
import json  # used to parse config.json
import datetime  # log and plot current time
import random

class LifeSupport(object):

    def __init__(self):
        self.ser = serial.Serial()
        self.__commPort = self.which_port()
        self.__initialize_serial()
        self.__status = ''
        self.pump_timer = Timer()
        self.circulation_timer = Timer()
        self.last_state = 0
        self.state = 0

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

    def is_open(self):
        return self.ser.isOpen()

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

    def get_case(self):
        '''
        Parse and interpret the current water level status
        Need to compare it to previous level and figure out next move
        Casese:
        0: No/very low water -> shut off pump, set timer to wait for fubar -> Send email alert, shut off UV
        1: Bottom switch is closed, but middle is not. Open recir valve, pump on
        2: Middle switch is closed, but not top. Open recir valve, pump on
        3: Top switch is closed, Water is too High -> Close Recirc valve, set timer --> send email alert
        :return:
        '''
        self.read_comm()
        if self.__status == 'Error, no reading':
            # Try to get reading 4 more times
            for i in range(4):
                self.read_comm()
                if self.__status != 'Error, no reading':
                    break
                else:
                    time.sleep(2)
            print "Fatal Error, can't read switches"
            sys.exit()  # Quit the program

        # This is the main logic
        state = int(self.__status[4])  # Float state
        # Cases:
        # !000000 - No floats on
        # !000400 - Bottom float on
        # !000600 - Bottom and middle float on
        # !000700 - Top Float on
        if state == 0:
            # Case 0: Empty
            print "Empty"

        elif state == 4:
            # Case 1 : bottom switch only
            print "Bottom float on"

        elif state == 6:
            #Case 2: Middle switch
            print "Middle float on"

        elif state == 7:
            #Case 3: Top Switch
            print "Top Float on"

    def toggle_pump(self,on=True):
        '''
        Check if pump is on or off, also check if pump timer is running, if so don't turn on
        :param on: Turn the pump on (True) or off (False)
        :return: NONE
        '''
        if self.pump_timer.is_running():
            pass
        else:
            # Figure out how to check if the pump relay is open or not. This should be a read from the DO
            if on:
                self.ser.write('#021501\r\n')
                self.pump_timer.set_timer(10)
            else:
                self.ser.write('#021500\r\n')
                self.pump_timer.set_timer(10)

class Timer(object):

    def __init__(self):
        self.__running = False
        self.end_time = numpy.nan

    def is_running(self):
        if self.__is_time_up():
            self.__running = False
        else:
            self.__running = True
        return self.__running

    def set_timer(self,length):
        self.__running = True
        self.end_time = time.time() + length

    def __is_time_up(self):
        if self.__running:
            if time.time() - self.end_time > 0:
                self.__running = False
                return True
            else:
                return False
        else:
            return True

    def get_time_left(self):
        if self.__is_time_up():
            return 0
        else:
            return int(time.time() - self.end_time * 1)

class WebReport(object):
    '''
    Generate a webreport with Temp and the state of the program
    Use plot.ly to update an embedded iframe that will house the water level, termperature, etc.

    An alternative method would be to update a static page with using the highcharts JS library or even better, updating
    a file and using AJAX read it into the highcharts library.
    '''
    def __init__(self):
        pass

    def start_py(self):
        with open('./config.json') as config_file:
            self.plotly_user_config = json.load(config_file)
            py.sign_in(self.plotly_user_config["plotly_username"], self.plotly_user_config["plotly_api_key"])
        self.stream = py.Stream(self.plotly_user_config['plotly_streaming_tokens'][0])

    def plot_data(self):
        url = py.plot([
            {
                'x': [], 'y': [], 'type': 'scatter',
                'stream': {
                    'token': self.plotly_user_config['plotly_streaming_tokens'][0],
                    'maxpoints': 2880 # THis is one day of points at .5 Hz
                }
            }], filename='Raspberry Pi Streaming Example Values')
        self.plot = url
        self.url= url
        self.stream.open()

    def update_plot(self,y):
        self.stream.write({'x': datetime.datetime.now(), 'y': y})

    def gen_test_data(self):
        return random.randint(0,3)

    def start_web_report(self):
        self.start_py()
        self.plot_data()

    def run_test(self):
        self.start_py()
        self.plot_data()
        while True:
            self.update_plot(self.gen_test_data())
            time.sleep(10)