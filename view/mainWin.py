import sys , os ,asyncio,threading,modbus_tk
#导入上层模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modbus_tools.UI.Ui_main import Ui_MainWindow
from PyQt5.QtCore import QTimer,QThread,pyqtSignal
from PyQt5.QtWidgets import QMainWindow,QApplication,QWidget,QMessageBox ,QLCDNumber
from modbus_tools.rs485 import modbus_tool
from time import sleep
from concurrent.futures import ThreadPoolExecutor

STANDARD_WEIGHT = 400

class win(QMainWindow,Ui_MainWindow):
    def __init__(self,loop,parent=None):
        super(win,self).__init__(parent)
        #使用枚举
        self._sla_ENU = list(enumerate(['slave_1','slave_2','slave_3','slave_4','slave_5']))
        self.th,self.st = None,None
        self.slave_type = 1
        self.loop = loop
        self.setupUi(self)
        self.mtool = modbus_tool()
        self.connct_signal()
        self.initWin()
    
    def initWin(self):
        com_list = modbus_tool.ComAutoFind()
        if not com_list:
            self.cbox_com_list.addItem("无串口")
        else:
            self.conn_uart_btn.setEnabled(True)
            for com in com_list:
                self.cbox_com_list.addItem(com)
        self.cbox_slave_type.addItem("宇翔从板")
        self.cbox_slave_type.addItem("博途从板")
        self.cbox_slave_type.setCurrentIndex(0)
        self.st = ShowWhtThread(self.mtool,self._sla_ENU,self)
        self.st.sign_send_wht.connect(self.show_wht)
        self.st.start() 
    def connct_signal(self):
        self.slave_1.pressed.connect(lambda :self.btnListener(self.slave_1))
        self.slave_2.pressed.connect(lambda :self.btnListener(self.slave_2))
        self.slave_3.pressed.connect(lambda :self.btnListener(self.slave_3))
        self.slave_4.pressed.connect(lambda :self.btnListener(self.slave_4))
        self.slave_5.pressed.connect(lambda :self.btnListener(self.slave_5))
        self.conn_uart_btn.clicked[bool].connect(self.ccb)
        self.cbox_com_list.activated[str].connect(self.onActivated)
        # self.cbox_slave_type.activated[str].connect(self.chooseSlave)
        self.timer = QTimer()
        self.timer.start(1000) #每过1秒，定时器到期，产生timeout的信号
        self.timer.timeout.connect(self.call_thread)

    def btnListener(self,sender):
        btnName = sender.objectName()
        if "slave_" in btnName and self.mtool.master:
            sla_num = None
            for sla in  self._sla_ENU:
                if btnName in sla[1]:
                    sla_num = sla[0]+1
            self.th = StandThread(self.mtool,sla_num,self)
            # self.th.setDaemon(True)
            self.th._sign_standardize.connect(lambda x:self.textBrowser.setText(x))
            self.th.start()

    def ccb(self,press):
        com = self.cbox_com_list.currentText()
        
        if "无串口" not in com :
            if self.cbox_slave_type.currentIndex() == 0:
                brate =57600
            elif self.cbox_slave_type.currentIndex()==1:
                brate =19200
            self.type = self.cbox_slave_type.currentIndex()
            std_wht = int(self.qedit_standard_wht.text()) if self.qedit_standard_wht.text() else 400
            print(brate)
            if self.mtool.master:
                self.mtool.disconnectCOM()
                self.sender().setText("连接串口")
                self.connect_status.setText(f"已断开")
            else:
                self.mtool.connectCOM(com_port=com,brate=brate,sla_type=self.slave_type,sweight=std_wht)
                # self.mtool.connectCOM(com_port=com,brate=57600,sla_type=0,sweight=std_wht)
                self.sender().setText("关闭串口")
                self.connect_status.setText(f"已连接到{com}")
        else:
            # QMessageBox.warning(self,"错误","电脑无串口连接")
            pass 

    def closeEvent(self, a0):
        # self.loop.close()
        print("关闭程序")
        self.st.done = 0
        self.timer.stop()
        self.close()
        return super().closeEvent(a0)

    def onActivated(self,val):
        if "无串口" not in val:
            self.mtool.connectCOM(val)

    def call_thread(self):
        com_list = modbus_tool.ComAutoFind()  
        if not com_list:
            self.cbox_com_list.addItem("未发现串口")
            self.cbox_com_list.setEnabled(False)
            self.conn_uart_btn.setEnabled(False)
        else:
            self.conn_uart_btn.setEnabled(True)
            self.cbox_com_list.setEnabled(True)
            self.cbox_com_list.clear()
            for com in com_list:
                self.cbox_com_list.addItem(com)

    def show_wht(self,mlist):
        slaNum = mlist[0]
        slaVal = mlist[1]
        print(f"num={slaNum},val={slaVal}")
        qLcd = self.verticalWidget.findChildren(QLCDNumber)[slaNum-1]
        displayVal = "0000" if 'None' in  str(slaVal) else str(slaVal)
        qLcd.display(displayVal)

class ShowWhtThread(QThread):
    sign_send_wht = pyqtSignal(tuple)
    def __init__(self,mtool,mlist,parent):
        super(ShowWhtThread,self).__init__(parent)
        self.mtool = mtool
        self._sla_ENU = mlist
        self.loop = asyncio.new_event_loop()
        self.done = True

    def run(self):
        self.read_slave()
    def done(self):
        self.done = False
    def read_slave(self):
        while(self.done):
            sleep(0.01)
            if self.mtool.master:
                for sla in self._sla_ENU:
                    self.loop.run_until_complete(self.read_weight((sla[0]+1)))

    async def read_weight(self,sla_num):
        mlist = ((sla_num,))
        try:
            weight =  self.mtool.get_slave_weight(sla_num)
            mlist = mlist + (weight,)
        except Exception as e:
            print(e)
            mlist = mlist + ("None",)
        self.sign_send_wht.emit(mlist)
                
class StandThread(QThread):
    _sign_standardize = pyqtSignal(str)
    def __init__(self,mtool, num,parent):
        super(StandThread,self).__init__(parent)
        self.master = mtool
        self.num = num   
         
    def run(self):
        if not self.master:
            self._sign_standardize.emit("未连接串口")
            return
        try:
            self._sign_standardize.emit(f"开始标定{self.num}号从板")
            self._sign_standardize.emit(f"{self.num}号从板读取数值:{self.master.get_slave_weight(self.num)}")
            self._sign_standardize.emit(f"1秒后开始标定{self.num}号从板，请清空{self.num}号从板称重器...")
            sleep(1)
            self.master.set_slave_emtyvalue(self.num)
            self._sign_standardize.emit(f"{self.num}号从板请放入标定砝码，等待十秒")
            for i in range(0,10):
                self._sign_standardize.emit(f"{10-i}s ")
                sleep(1)
            self.master.set_slave_standardweight(self.num)
            if abs(self.master.get_slave_weight(self.num)-int(self.master.std_wht)) < 2 :
                self._sign_standardize.emit(f"{self.num}号从板标定成功,现在重量为{self.master.get_slave_weight(self.num)}")
            else:
                self._sign_standardize.emit(f"{self.num}号从板标定失败")
        except modbus_tk.modbus_rtu.ModbusInvalidResponseError as err:
                self._sign_standardize.emit(f"{self.num}号从板发生错误：{err}")

if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # mWin = win()
    # mWin.show()
    # tool = modbus_tool()
    # tool.connectCOM(com_port="COM8",brate=19200,sla_type=1,sweight=740)
    # for i in range(0,100):
    #     sleep(0.5)
    #     print(tool.get_slave_weight(2))
    # # tool.connectCOM("COM6")
    # # tool.standardize(5)
    # sys.exit(app.exec_())
    pass