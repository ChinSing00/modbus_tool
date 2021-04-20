# -*- coding:utf-8 -*-
import time
import sys ,asyncio
import serial
import serial.tools.list_ports
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
from time import sleep

# STANDARD_WEIGHT = 400
# baudrate        = 57600

class modbus_tool():
    def __init__(self):
        super().__init__()
        self.master = None
            
    def connectCOM(self,com_port,brate=57600,sweight=None,sla_type=0):
        self.sla_type = sla_type
        self.std_wht = sweight
        if self.master:
            self.master.close()
            self.master=None
        self.rate = brate    
        self.master = modbus_rtu.RtuMaster(serial.Serial(port=com_port,
            baudrate=brate,
            bytesize=8,
            parity='E',
            stopbits=1,
            xonxoff=0))
        self.master.set_timeout(1)
        self.master.set_verbose(True)

    def disconnectCOM(self):
        self.master = None
        
    def standardize(self,slave_num):
        if not self.master:
            print("未连接串口")
            return
        try:
            print("读取数值:",self.get_slave_weight(slave_num))
            print("1秒后开始标定，请清空称重器...")
            sleep(1)
            self.set_slave_emtyvalue(slave_num)
            print("请放入标定砝码，等待十秒",end="",flush=True)
            for i in range(0,10):
                print(f"{10-i}s  ",end="",flush=True)
                sleep(1)
            print("")
            self.set_slave_standardweight(slave_num)
            if abs(self.get_slave_weight(slave_num)-self.std_wht) < 2 :
                print(f"标定成功,现在重量为{self.get_slave_weight(slave_num)}")
            else:
                print("标定失败")
        except modbus_tk.modbus_rtu.ModbusInvalidResponseError as err:
                print(f"错误：{err}")

    def set_baudrate(self,rate):
        self.baudrate = rate
        

    def get_slave_weight(self,slave_num):
        return self.master.execute(slave_num,cst.READ_HOLDING_REGISTERS,42,1)[0]

    def set_slave_emtyvalue(self,slave_num,type=0):
        if self.sla_type == 0:
            self.master.execute(slave_num,cst.WRITE_SINGLE_REGISTER,8,output_value=0)
        elif self.sla_type == 1:
            self.master.execute(slave=slave_num,function_code=16,starting_address=8,output_value=[0,0])
        print(f"{slave_num}号从板设定空载值")

    def set_slave_standardweight(self,slave_num,stard_wht=None):
        if not stard_wht:
            stard_wht = self.std_wht
        if self.sla_type == 0:
            self.master.execute(slave_num,cst.WRITE_SINGLE_REGISTER,16,output_value=stard_wht)
        elif self.sla_type == 1:
            self.master.execute(slave=slave_num,function_code=16,starting_address=16,output_value=[stard_wht,0])
        print(f"{slave_num}号从板标定完成")

    #获取串口列表    
    def ComAutoFind():
    #先获取所以有USB串口挂载的设备
        scomList = list(serial.tools.list_ports.comports())
        usbComList = []
        if(len(scomList) <= 0):
            print("未发现Modbus接口，请检查线缆连接")
            return None
        else:
            comNum = len(scomList)
            # print(f"找到{str(comNum)}个串口")
            def funcCom(arrContent):
                return "USB-SERIAL" in arrContent.description
            #//通过filter函数筛选出设备描述里包含USB-SERIAL的设备
            b = list(filter(funcCom,scomList))
            comNum = len(b)
            while comNum:
                comNum = comNum - 1
                usbComList.append(b[comNum].device)
            # print(usbComList)
            return usbComList
            
if __name__ == "__main__":
    PORT            = 'COM8'
    sla_num         = 2
    m = modbus_tool()
    # m = modbus_tool(brate=57600,ema=8,sma=16,sweight=400)
    m.connectCOM(com_port=PORT,brate=19200,sla_type=0,sweight=740)
    # print("当前重量为：",m.master.execute(sla_num,3,42,1)[0])
    # sleep(1)
    # print("设置空载值完成...，放入标定物...",m.master.execute(slave=sla_num,function_code=16,starting_address=8,output_value=[0,0]))
    # sleep(3)
    # # 0x10 = 16
    # print("标定完成",m.master.execute(slave=sla_num,function_code=16,starting_address=16,output_value=[740,0]))
    while True:
        try:
            sleep(0.3)
            # print(m.master.execute(sla_num,3,42,1)[0])
            print(m.get_slave_weight(2))
        except  Exception as e :
            print(e)
    # pass