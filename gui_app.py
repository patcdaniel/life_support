#!/usr/bin/env python3
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QGridLayout,
    QPushButton, QApplication, QLabel,QLineEdit,QTextEdit,QLCDNumber,QSlider,QVBoxLayout)
import sys, random
from PyQt5.QtWidgets import (QWidget, QHBoxLayout,QVBoxLayout, QPushButton, QApplication,QFrame)
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from time import strftime
import datetime as dt
import numpy as np
from PyQt5.QtGui import QPainter, QColor, QBrush, QPalette
from numpy import arange, sin, pi
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, MinuteLocator,SecondLocator
import lifesupport as ls


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.temp_data = [0]
        self.temp_time = [dt.datetime.now()]
        self.tmp_probe = ls.Tmp_Probe()    

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        try:
            self.temp_data.append(self.tmp_probe.get_temp())
        except:
            self.temp_data.append(0)
        self.temp_time.append(dt.datetime.now())
        if len(self.temp_time) > 30:
            self.temp_data =  self.temp_data[1:-1]
            self.temp_time = self.temp_time[1:-1]

        self.axes.plot(self.temp_time, self.temp_data, 'r')
        self.axes.set_ylim(0,30)
        self.axes.xaxis.set_minor_locator(SecondLocator())
        self.axes.xaxis.set_major_locator(MinuteLocator())
        self.axes.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        self.draw()


class verticalWaterLevel(QWidget):
    def __init__(self,lifeSupport):
        super(verticalWaterLevel,self).__init__()
        self.lifeSupport = lifeSupport
        self.initUI()

    def initUI(self):

        self.setMinimumSize(60, 190)
        lbl = QLabel('Water\n Level',self)
        lbl.move(0,0)

    def paintEvent(self,event):
        qp = QPainter()
        qp.begin(self)
        self.drawRectangles(qp)
        qp.end()

    def drawRectangles(self,qp):

        size = self.size()
        w = size.width()
        h = size.height()-40

        col = QColor(255,255,255)
        col.setNamedColor('#ffffff')
        qp.setPen(col)

        qp.setBrush(QColor(255,255,255))
        qp.drawRect(0,40,w-1,h-1)

        qp.setBrush(QColor(2,140,186))
        qp.drawRect(0, h+40, w-1, self.getHeight(h))

        qp.setBrush(QColor(0,0,0))
        for i in range(0,3):
            y = h *(.25 * i) + 40

            qp.drawLine(0,y,w,y)

    def getHeight(self,h,debug=False):

        if debug:
            i = random.randint(0,2)
            a = [0,1,2]
            val = a[i]
            if val == 0:
                return 0
            else:
                return (h *(-.25 * val))
        else:
            state = self.lifeSupport.last_state
            if state == 0:
                return (h * (-.25 * 1))
            elif state == 4:
                return (h * (-.25 * 2))
            elif state == 6:
                return (h * (-.25 * 3))
            elif state == 7:
                return (h * (-.25 * 4))

class statusWidget(QWidget):
    def __init__(self):
        super(statusWidget,self).__init__()
        self.initUI()

    def initUI(self):
        self.green = QColor(0, 128, 0)
        self.red = QColor(128,0,0)
        self.setMinimumSize(100,200)
        lbl1 = QLabel('Pump',self)
        lbl1.move(10,0)
        lbl2 = QLabel('Valve', self)
        lbl2.move(10, 85)
        lbl3 = QLabel('Status 3', self)
        lbl3.move(10, 170)

        self.square1 = QFrame(self)
        self.square1.setGeometry(10,20,60,60)
        self.square1.setStyleSheet("QWidget { background-color: %s }" %
                                  self.green.name())
        self.square2 = QFrame(self)
        self.square2.setGeometry(10,105,60,60)
        self.square2.setStyleSheet("QWidget { background-color: %s }" %
                                   self.red.name())
        self.square3 = QFrame(self)
        self.square3.setGeometry(10,190,60,60)
        self.square3.setStyleSheet("QWidget { background-color: %s }" %
                                   self.red.name())

class Example(QWidget):

    def __init__(self):
        super(Example,self).__init__()
        self.width = 800
        self.height = 600
        self.updateTemp = True
        self.initUI()


    def initUI(self):

        # Buttons
        self.startBtn = QPushButton('Start', self)
        self.startBtn.setGeometry(self.width/4 - 60, self.height/4 + 55, 60, 40)
        self.startBtn.setCheckable(True)
        self.startBtn.clicked.connect(self.toggleUpdate)

        # Time LCD
        self.lcd = QtWidgets.QLCDNumber(self)
        self.lcd.setDigitCount(9) # Allows to add the current seconds default was 7
        self.lcd.setBackgroundRole(QPalette.BrightText)
        self.lcd.setGeometry(self.width-110,10,100,50)
        self.lcd.display(strftime("%H" + ":" + "%M" + ":" + "%S"))
        self.lcd.setStyleSheet("QLCDNumber { background-color: %s }" %QColor("#1C5061").name())

        # Lifesupport Object
        self.lifeSupport = ls.LifeSupport()
        self.lifeSupport.start_up()

        #Water level Widget
        self.wLevel = verticalWaterLevel(self.lifeSupport)
        self.wLevel.resize(250, 150)
        self.wLevel.move(10,10)


        # Plotting Widget
        self.sc = MyDynamicMplCanvas(self, width=3, height=3, dpi=100)
        self.sc.move(self.width/2.-10,self.height/2.-10)

        #
        self.status = statusWidget()

        hbox = QHBoxLayout()
        hbox.addWidget(self.lcd)
        hbox.addWidget(self.startBtn)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.sc)
        hbox2.addWidget(self.wLevel)
        hbox2.addWidget(self.status)
        vbox.addLayout(hbox2)


        self.setLayout(vbox)
        self.setGeometry(600, 600, self.width, self.height)
        self.setWindowTitle('Life Support')
        self.show()


        # Main timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.Time)
        self.timer.timeout.connect(self.sc.update_figure)

        self.timer.start(1000)

    def toggleUpdate(self):
        if self.updateTemp:
            self.updateTemp = False
            self.startBtn.setText('Pause')
        else:
            self.updateTemp = True
            self.startBtn.setText('Start')

    def Time(self):
        self.lcd.display(strftime("%H" + ":" + "%M" + ":" + "%S"))
        self.lifeSupport.get_case(False)
        self.update()
        self.checkStatus()
        
    def checkStatus(self):
        # Update Recir Status Light
        if self.lifeSupport.get_circ_status:
            color = QColor(0,124,0)
        else:
            color = QColor(124,0,0)
        self.status.square2.setStyleSheet("QWidget { background-color: %s }" % color.name())
        # Update Pump Status light
        if self.lifeSupport.get_pump_status:
            color = QColor(0,124,0)
        else:
            color = QColor(124,0,0)
        self.status.square1.setStyleSheet("QWidget { background-color: %s }" % color.name())




        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
