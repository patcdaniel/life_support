'''
Author: Patrick Daniel

GOAL: Make a robust class to handle serial data inputs the ADAM Modules by a Rasperberry Pi. The emphasis
has to be on writting solid and easy to understand code.

Classes:
    commSupport: This should handle the serial communication and store the most recent status
    timer: These will handle the timers that are important for trimming the water levels
    email (possibly)

'''
import serial,sys,time,numpy,os
import json  # used to parse config.json
import datetime  # log and plot current time
import random
import plotly.plotly as py
import plotly.tools as tls
import plotly.graph_objs as go
import numpy as np

class LifeSupport(object):

    def __init__(self):
        self.ser = serial.Serial()
        self.__commPort = self.__which_port()
        self.__initialize_serial()
        self.__status = ''
        self.__do_status = ''
        self.__pump_on = False
        self.__recirc_on = False
        self.pump_timer = Timer()
        self.circulation_timer = Timer()
        self.last_state = 0
        self.state = 0
        self.start()
        
    def get_comm_port(self):
        return self.__commPort

    def get_status(self):
        return self.__status

    def get_pump_status(self):
        return self.__pump_on

    def get_circ_status(self):
        return self.__recirc_on

    def __which_port(self):
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
        except SerialException as (errno, strerror):
            print "Erorr: {0}".format(strerror)

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
            out = out.split()
            self.__status = out[-1]
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
        PUMP Status
        Circ. Valve Satus
        If the first digit of status is:
        0 : Both are off
        2 : Pump is ON, Circ is OFF
        4 : Circ Valve is ON, Pump is OFF
        6 : Both are ON

        :return:
        '''
        self.read_comm()
        print self.get_status()
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
        # When the pump is on, a second digital out
        state = int(self.__status[4])  # Float state
        print "DEBUG State:", state
        print "Last State:", self.last_state
        self.update_relays()
        
        # Cases:
        # !000000 - No floats on
        # !000400 - Bottom float on
        # !000600 - Bottom and middle float on
        # !000700 - Top Float on
        if (state == 0) and (state != self.last_state):
            # Case 0: Empty 
            print "Empty"
            self.toggle_pump(False)
            self.toggle_circ_valve(False)   
        elif (state == 4) and (state != self.last_state):
            # Case 1 : bottom switch only
            print "Bottom float on"
            self.toggle_pump(True)
            self.toggle_circ_valve(False)
        elif (state == 6) and (state != self.last_state):
            #Case 2: Middle switch
            print "Middle float on"
            self.toggle_pump(True)
            self.toggle_circ_valve(True)
        elif (state == 7) and (state != self.last_state):
            #Case 3: Top Switch
            print "Top Float on"
            self.toggle_pump(True)
            self.toggle_circ_valve(on=False)
        self.last_state = state
        return state

    def update_relays(self):
        state = self.get_status()
        state = int(state[1])
        if state == 0:
            self.__pump_on = False
            time.sleep(1)
            self.__recirc_on = False
        elif state == 2:
            self.__pump_on = True
            time.sleep(1)
            self.__recirc_on = False
        elif state == 4:
            self.__pump_on = False
            time.sleep(1)
            self.__recirc_on = True
        elif state == 6:
            self.__pump_on = True
            time.sleep(1)
            self.__recirc_on = True
        

            
    def toggle_pump(self,on=True):
        '''
        Check if pump is on or off, also check if pump timer is running, if so don't turn on
        :param on: Turn the pump on (True) or off (False)
        :return: NONE
        '''
        
        ##if self.pump_timer.is_running():
        if False:
            # To prevent cycling the pump on and off, set a tolerance
            print "Pump timer on: ", self.pump_timer.get_time_left()
            pass
        else:
            # Figure out how to check if the pump relay is open or not. This should be a read from the DO
            if on:
                print('Turning pump on')
                self.ser.write('#021501\r\n')
                #self.pump_timer.set_timer(10)
            else:
                print('Turning pump off')
                self.ser.write('#021500\r\n')
                #self.pump_timer.set_timer(10)
        time.sleep(2)

    def toggle_circ_valve(self,on):
        '''
        Check if circulation valve is on or off, also check if circ timer is running, if so don't turn on
        :param on: Turn the pump on (True) or off (False)
        :return: NONE
        '''
            # Figure out how to check if the pump relay is open or not. This should be a read from the DO
        if on:
            print('Turning recirc Valve On')
            self.ser.write('#021601\r\n')
            #self.circulation_timer.set_timer(10)
        else:
            print('Turning recirc valve Off')
            self.ser.write('#021600\r\n')
            #self.circulation_timer.set_timer(10)

    def start(self):
        self.open_com()
        tmp = Tmp_Probe()
        wr = WebReport()
        self.toggle_pump(False)
        time.sleep(1)
        self.toggle_circ_valve(False)
        while True:
            out_temp = tmp.get_temp()
            out_state = self.get_case()
            wr.stream(state=out_state,temp=out_temp)
            time.sleep(2)
        
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
    def __init__(self,token=1):
        self.stream_tokens = ["7c0ig164ac","64299hxjgr"]
        self.stream_id1 = dict(token=self.stream_tokens[0])
        self.stream_id2 = dict(token=self.stream_tokens[1])
        self.plot_url = py.plot(self.make_plots(),filename='Aq_Tank1')

        self.s1 = py.Stream(stream_id=self.stream_tokens[0])
        self.s2 = py.Stream(stream_id=self.stream_tokens[1])
        self.s1.open()
        self.s2.open()



    def make_plots(self):
        trace1 = go.Scatter(x=[], y=[], stream=self.stream_id1, name='trace1')
        trace2 = go.Scatter(x=[], y=[], stream=self.stream_id2, yaxis='y2', name='trace2',
                            marker=dict(color='rgb(148, 103, 189)'))

        data = [trace1, trace2]
        layout = go.Layout(
            title='Squid Lifesupport',
            yaxis=dict(
                title='Water Treatment state',
                range=[0,7]
            ),

            yaxis2=dict(
                title='Temperature [C]',
                range=[10,30],
                titlefont=dict(
                    color='rgb(148, 103, 189)'
                ),
                tickfont=dict(
                    color='rgb(148, 103, 189)'
                ),
                overlaying='y',
                side='right'
            )
        )

        fig = go.Figure(data=data, layout=layout)
        return fig

    def stream(self,temp,state):
        x = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        self.s1.write(dict(x=x, y=state))
        self.s2.write(dict(x=x, y=temp))

    def test_stream(self):
        k = 10
        i = 1

        while True:
            x = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            delta = np.random.randint(4, 10)
            y = (np.cos(k * i / 50.) * np.cos(i / 50.) + np.random.randn(1))[0]
            self.s1.write(dict(x=x, y=y))
            self.s2.write(dict(x=x, y=(-delta * y)))
            time.sleep(0.8)
            i += 1

class Tmp_Probe(object):
    '''
    Return the temperature reading from a one-wire probe. Currently using the Pin 4
    '''
    def __init__(self):
        self.temp_sensor = '/sys/bus/w1/devices/28-000006061eb7/w1_slave'
        self.__os_prep()

    def __os_prep(self):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

    def __temp_raw(self):
        f = open(self.temp_sensor, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def __read_temp(self):
        lines = self.__temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.__temp_raw()
        temp_output = lines[1].find('t=')
        if temp_output != -1:
            temp_string = lines[1].strip()[temp_output + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

    def get_temp(self):
        return self.__read_temp()

if __name__ == '__main__':
    life = LifeSupport()
