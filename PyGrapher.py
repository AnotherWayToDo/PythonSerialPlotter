
# https://python-forum.io/Thread-PyQt-Threading-Class-handling
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QComboBox, QSizePolicy, QGridLayout
from PyQt5.QtCore import Qt, QObject, Qt, QRunnable, QThread, QThreadPool,pyqtSignal
from PyQt5.QtGui import QIcon
import pyqtgraph as pg
import numpy as np
from numpy_ringbuffer import RingBuffer

import SerialModule as serialMod
import serial

#==============================================================================
# Get the list of COM port on the system
lstComPorts = serialMod.listSerialPort()
strArrBaudrate = ["9600","115200"]





#==============================================================================
# A class to be able to read data from the serial port in a thread
class serialThreadWorker(QThread):
    # threadMsg is the structure used to exchange data between the thread and the application
    threadMsg = pyqtSignal(str)

    def __init__(self, parent=None):
        super(serialThreadWorker,self).__init__(parent)
        self.workerSerialPort = serial.Serial()
        self.baudrate = 0
        self.port = ""
       
    def openPort(self):
        self.workerSerialPort = serial.Serial(self.port,self.baudrate)

    def closePort(self):
        if (self.workerSerialPort.isOpen()):
            self.workerSerialPort.close()

    def run(self):
        if (self.workerSerialPort.isOpen()):
            while(True):
                buffer = self.workerSerialPort.readline()
                self.threadMsg.emit(str(buffer))
                

    def sendSerial(self):
        # Send data over the serial port
        self.serialPort.write(b'A')
    





#==============================================================================
# Class of the main application.
#   This class will handle all the UI and associted functions. It will also 
# handle thread operations
class App(QWidget):
    #--------------------------------------------------------------------------
    # Functions used in the interface
    # Functions callback on button connect
    def buttonConnect_click(self):
        print("buttonConnect_click")
        # Get the button text
        text = self.sender().text()

        # If "Connect" then
        if (text == "Connect"):
            self.serialPortThread.port = self.strCurrentPort
            self.serialPortThread.baudrate = self.strCurrentBaudrate
            self.serialPortThread.openPort()
            if (self.serialPortThread.workerSerialPort.isOpen() != True):
                print("Unable to open {0} port".format(self.strCurrentPort))
            else:
                self.serialPortThread.start()
                # Change the button text
                self.sender().setText("Disconnect")
                print("Connect -> Disconnect")
        else:
            # If "Disconnect" then
            # Check if the serial port is opened
            if (self.serialPortThread.workerSerialPort.isOpen()):
                # stop the thread
                self.serialPortThread.terminate()
                # close the serial port
                self.serialPortThread.closePort()
                # Change the button text
                self.sender().setText("Connect")
                print("Disconnect -> Connect")

    
    # Function callback on dropbox Com Port content change event
    def dropboxCom_indexChange(self):
        self.strCurrentPort = self.dropboxCom.currentText()
        print("dropboxCom_indexChange : {0}".format(self.strCurrentPort))
        

    # Function callback on dropbox Baudrate content change event
    def dropboxBaudRate_indexChange(self):
        self.strCurrentBaudrate = self.dropboxBaudRate.currentText()

        print("dropboxBaudRate_indexChange : {0}".format(self.strCurrentBaudrate))

    # Function callback on connect button click event
    def buttonReset_click(self):
        print("buttonReset_click")

    # Function callback on window resize event
    def onResize(self):
        print("onResize")

    # Function callback for the SerialWorker thread
    def onSerialWorkerMsg(self, str):
        strRes = "{0:s}".format(str)
        strRes = ((strRes.split('$'))[1].split(';')[0])
        
        print("ThreadMessage : {0}".format(strRes))

        values = strRes.split(' ')

        # If the dataArrays struct is empty ...
        if (len(self.dataArrays) == 0):
            # ... instanciate the needed nb of np.array in the struct
            for v in values:
                self.dataArrays.append(RingBuffer(capacity=200))
                

        # ... fill the struct 
        counter = 0
        for v in values:
            self.dataArrays[counter].append(float(v))
            counter+=1

        self.plotFunction()

        
    # Function to handle all the plot work in the pyQtGraph object
    def plotFunction(self,*data):
        self.graph.clear()
        for arr in self.dataArrays:
            if (len(arr) != 0):
                self.graph.plot(arr,pen=pg.mkPen(255, 0, 0))


    #--------------------------------------------------------------------------
    # Functions used to build the UI and initiate application vars
    def __init__(self):
        super().__init__()
        self.strCurrentBaudrate = ""
        self.strCurrentPort = ""
        self.serialPortThread = serialThreadWorker()
        self.serialPortThread.threadMsg.connect(self.onSerialWorkerMsg)
        
        self.dataArrays = [] # struct that will contain array of data to plot

        self.title = "PyGrapher - Graph from serial port"
        self.left = 100
        self.top = 100
        self.width = 800
        self.height = 600
        
        # Add the combo box component for ComPort
        self.dropboxCom = QComboBox(self)
        self.dropboxCom.resize(100,32)
        for port in lstComPorts:
            self.dropboxCom.addItem(port[0])
        self.dropboxCom.currentIndexChanged.connect(self.dropboxCom_indexChange)
        
        # Add the combo box component for BaudRate
        self.dropboxBaudRate = QComboBox(self)
        self.dropboxBaudRate.resize(100,32)
        for baud in strArrBaudrate:
            self.dropboxBaudRate.addItem(baud)
        self.dropboxBaudRate.currentIndexChanged.connect(self.dropboxBaudRate_indexChange)


        # Add the Connect button component
        self.buttonConnect = QPushButton("Connect",self)
        self.buttonConnect.resize(100,32)
        self.buttonConnect.clicked.connect(self.buttonConnect_click)

        # Add the Reset button component
        self.buttonReset = QPushButton("Rest graph",self)
        self.buttonReset.resize(100,32)
        self.buttonReset.clicked.connect(self.buttonReset_click)

        # Add the graph component
        self.graph = pg.PlotWidget(self)

        # Prepare the layout
        grid = QGridLayout()
        grid.addWidget(self.dropboxCom,0,0,Qt.AlignTop)
        grid.addWidget(self.dropboxBaudRate,0,1,Qt.AlignTop)
        grid.addWidget(self.buttonConnect,0,2,Qt.AlignTop)
        grid.addWidget(self.buttonReset,0,3,Qt.AlignTop)
        grid.addWidget(self.graph,1,0,1,4)

        self.setLayout(grid)

        
        # Initialise the UI
        self.initUI()

    #--------------------------------------------------------------------------
    # Functions to initialize UI
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()
        



#==============================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()

    sys.exit(app.exec_())
