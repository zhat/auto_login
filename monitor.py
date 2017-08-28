# -*- coding: utf-8 -*-


import pythoncom
import pyHook
import datetime
import time
import AmazonAutoLoginModule


class MouseAndKeyboardMonitor(AmazonAutoLoginModule):

    def __init__(self):
        self.mouse_window_name = ''
        self.keyboard_window_name = ''
        # 创建hook句柄
        self.hm = pyHook.HookManager()

    def onMouseEvent(self, event):
        "处理鼠标事件"
        if str(event.WindowName) != self.mouse_window_name:
            print('-' * 40 + 'MouseEvent Begin' + '-' * 40 + '\n')
            print("Current Time:%s\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # print("MessageName:%s\n" % str(event.MessageName))
            # print("Message:%d\n" % event.Message)
            # print("Time_sec:%d\n" % event.Time)
            print("Window:%s\n" % str(event.Window))
            # print(type(event.WindowName))
            if event.WindowName is not None:
                print("WindowName:%s\n" % str(event.WindowName).decode('GB2312'))
            else:
                print("WindowName is None")

            # print(event.WindowName.decode('GB2312'))
            # print("Position:%s\n" % str(event.Position))
            # print("Current Time:%s\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print('-' * 40 + 'MouseEvent End' + '-' * 40 + '\n')

            self.mouse_window_name = str(event.WindowName).decode('GB2312')

        return True

    def onKeyboardEvent(self, event):
        "处理键盘事件"
        if str(event.WindowName) != self.keyboard_window_name:
            print('-' * 40 + 'Keyboard Begin' + '-' * 40 + '\n')
            print("Current Time:%s\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # print("MessageName:%s\n" % str(event.MessageName))
            # print("Message:%d\n" % event.Message)
            # print("Time:%d\n" % event.Time)
            # print("Window:%s\n" % str(event.Window))
            # print("WindowName:%s\n" % str(event.WindowName))
            # print("Ascii_code: %d\n" % event.Ascii)
            # print("Ascii_char:%s\n" % chr(event.Ascii))
            # print("Key:%s\n" % str(event.Key))
            print('-' * 40 + 'Keyboard End' + '-' * 40 + '\n')

            self.keyboard_window_name = str(event.WindowName).decode('GB2312')
        return True

    def startMonitor(self, mouseFlag, keyboradFlag):
        if keyboradFlag:
            # 监控键盘
            self.hm.KeyDown = self.onKeyboardEvent
            self.hm.HookKeyboard()

        if mouseFlag:
            # 监控鼠标
            self.hm.MouseAll = self.onMouseEvent
            self.hm.HookMouse()

        # 循环获取消息
        pythoncom.PumpMessages()

    def monitorWindowHandle(self):
        time.sleep(1)
        winhandles = self.driver.window_handles
        if len(winhandles) == 0:
            self.deleteAll()
        print('-' * 80)
        print(len(winhandles))
        print('-' * 80)


if __name__ == "__main__":
    monitor = MouseAndKeyboardMonitor()
    monitor.startMonitor(True, False)

