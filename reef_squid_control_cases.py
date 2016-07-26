# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 14:03:46 2016

@author: Patrick
"""

import serial,time, sys
ser = serial.Serial()

pumpTimer = 0
pumpTimerOn = False

recircValve1Timer = 0
recircValve1TimerOn = False

offSwitch = False
lastCase = 0

def initializePort():
    global ser
    if sys.platform == 'darwin':
        commPort = '/dev/tty.usbserial'
    else:
        commPort ='/dev/ttyUSB0'
    ser.setPort(commPort)
    ser.setBaudrate(9600)
    ser.setParity(serial.PARITY_NONE)
    ser.setByteSize(serial.EIGHTBITS)
    
    try:    
        ser.open()
    except OSError as (errno, strerror):
        print "Erorr: {0}".format(strerror)
        print "Can't find serial port. Shutting down"
        sys.exit()
    openPort()
    
def getStatus():
    global ser
    cmd = '$026\r\n' #Ask what switches are open
    ser.write(cmd)
    out = ''
        # let's wait one second before reading output (let's give device time to answer)
    time.sleep(2)
    while ser.inWaiting() > 0:
        out += ser.read(1)
    if out != '':
        return out

def openPort():
    global ser, lastCase
    while ser.isOpen() and ~offSwitch:
        out = getStatus()       
        if out != None:
            state = int(out[4]) # Float state
        
        # Cases:
            # !000000 - No floats on
            # !000400 - Bottom float on
            # !000600 - Bottom and middle float on
            # !000700 - Top Float on
        
        if lastCase != state:
            if state == 0:
                print "Empty"
                togglePumpOff()
            elif state == 4:
                print "Bottom float on"
                print "Last state:"+ str(lastCase)
                print "Now state: "+ str(state)
                toggleRecircValveOff()
            elif state == 6:
                print "Middle float on"
                togglePumpOn()
                toggleRecircValveOn()
            elif state == 7:
                print "Top Float on"
                togglePumpOn()
                toggleRecircValveOff()
            elif state == 99:
                print "No Reading!"
        else:
            if state == 0:
                pass
                print "Empty"
            elif state == 4:
                pass
                print "Bottom float on"
            elif state == 6:
                pass
                print "Middle float on"
            elif state == 7:
                pass
                print "Top Float on"
            elif state == 99:
                pass
                print "No Reading!"
        lastCase = state
def togglePumpOn():
    global ser
    global pumpTimer
    global pumpTimerOn
    print "Pump timer on:", pumpTimerOn
    if not pumpTimerOn:
        cmd = '#021501\r\n'
        print 'Toggleing pump on'
        ser.write(cmd)
        #start timer
        recircValve1Timer = time.time()
        recircValve1TimerOn = True
    else:
        pumpTimerOn = checkTimer(pumpTimer)

def togglePumpOff():
    global ser
    global pumpTimer
    global pumpTimerOn
    print "Pump timer is", pumpTimerOn
    if not pumpTimerOn:
        cmd = '#021500\r\n'
        print 'Toggling pump off'
        ser.write(cmd)
        pumpTimer, pumpTimerOn = startTimer()
    else:
        pumpTimerOn = checkTimer(pumpTimer)
    
def toggleRecircValveOn():
    global ser
    global recircValve1Timer
    global recircValve1TimerOn
    valStatus = getStatus()
    if not recircValve1TimerOn:
        cmd = '#021601\r\n'
        print 'Toggleing recir on'
        ser.write(cmd)

        #start timer
        recircValve1Timer = time.time()
        recircValve1TimerOn = True
    else:
        recircValve1TimerOn = checkTimer(recircValve1Timer)

def toggleRecircValveOff():
    global ser
    global recircValve1Timer
    global recircValve1TimerOn
    
    valStatus = getStatus()
    if not recircValve1TimerOn:
        cmd = '#021600\r\n'
        print 'Toggling recir off'
        ser.write(cmd)
        recircValve1Timer, recircValve1TimerOn = startTimer()
    else:
        recircValve1TimerOn = checkTimer(recircValve1Timer)

def startTimer():
    return time.time(), True

def checkTimer(timer):
    delayTime = 15 # This is the number of seconds before pump can be toggled again
    ellapsedtime = int(time.time() - timer)
    print "Ellapsedtime",ellapsedtime
    if ellapsedtime >= delayTime:
        return False
    else:
        return True

def checkOffSwitch():
    ### Create a hardware switch to initialize shut down of everything.
    global offSwitch
    pass

if __name__ == "__main__":
    initializePort()

initializePort()
