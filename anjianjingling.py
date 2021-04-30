#!/usr/bin/python
# -*- coding: utf-8 -*-
#coding:utf-8
# Author:AlwaysSun
# Time:2021-04-28
# function:实现按键精灵的功能 目前鼠标没问题 键盘还有问题

import json
import threading
import time
#import tkinter
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from PyQt5 import QtCore,QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow,QWidget,QMessageBox,QFileDialog
from PyQt5.QtGui import QPalette, QBrush, QPixmap
from anjian import Ui_Dialog
import os

from pynput import keyboard, mouse
from pynput.keyboard import Controller as KeyBoardController, KeyCode
from pynput.mouse import Button, Controller as MouseController
from PyQt5.QtCore import *

rate = 0
moveTime = 0.02
# 键盘动作模板
def keyboard_action_template():
    return {
        "name": "keyboard",
        "event": "default",
        "vk": "default"
    }


# 鼠标动作模板
def mouse_action_template():
    return {
        "name": "mouse",
        "event": "default",
        "target": "default",
        "action": "default",
        "location": {
            "x": "0",
            "y": "0"
        }
    }


# 倒计时监听，更新UI触发自定义线程对象
class UIUpdateCutDownExecute(threading.Thread):
    def __init__(self, cut_down_time, custom_thread_list):
        super().__init__()
        self.cut_down_time = cut_down_time
        self.custom_thread_list = custom_thread_list

    def run(self):
        while self.cut_down_time > 0:
            for custom_thread in self.custom_thread_list:
                if custom_thread['obj_ui'] is not None:
                    custom_thread['obj_ui']['text'] = str(self.cut_down_time)
                    custom_thread['obj_ui']['state'] = 'disabled'
                    self.cut_down_time = self.cut_down_time - 1
            time.sleep(1)
            print("倒计时：",str(self.cut_down_time),'秒后开始')
        else:
            for custom_thread in self.custom_thread_list:
                if custom_thread['obj_ui'] is not None:
                    custom_thread['obj_ui']['text'] = custom_thread['final_text']
                    custom_thread['obj_ui']['state'] = 'disabled'
                if custom_thread['obj_thread'] is not None:
                    custom_thread['obj_thread'].start()
                    time.sleep(1)


# 键盘动作监听
class KeyboardActionListener(QtCore.QThread):

    _signal = pyqtSignal()
    def __init__(self, file_name='keyboard.action'):
        super().__init__()
        self.file_name = file_name

    def run(self):
        with open(self.file_name, 'w', encoding='utf-8') as file:
            # 键盘按下监听
            def on_press(key):
                template = keyboard_action_template()
                template['event'] = 'press'
                try:
                    template['vk'] = key.vk
                except AttributeError:
                    template['vk'] = key.value.vk
                finally:
                    file.writelines(json.dumps(template) + "\n")
                    file.flush()

            # 键盘抬起监听
            def on_release(key):
                if key == keyboard.Key.esc:
                    # 停止监听
                    startListenerBtn['text'] = '开始录制'
                    startListenerBtn['state'] = 'normal'
                    MouseActionListener.esc_key = True
                    keyboardListener.stop()
                    self._signal.emit()
                    print("+++++++++++++++++++++++++esc 按下 录制结束+++++++++++++++")
                    return False
                template = keyboard_action_template()
                template['event'] = 'release'
                try:
                    template['vk'] = key.vk
                except AttributeError:
                    template['vk'] = key.value.vk
                finally:
                    file.writelines(json.dumps(template) + "\n")
                    file.flush()

            # 键盘监听
            with keyboard.Listener(on_press=on_press, on_release=on_release) as keyboardListener:
                keyboardListener.join()


# 键盘动作执行
class KeyboardActionExecute(threading.Thread):

    def __init__(self, file_name='keyboard.action', execute_count=0):
        super().__init__()
        self.file_name = file_name
        self.execute_count = execute_count

    def run(self):
        while self.execute_count > 0:
            print("第", self.execute_count, '次回放')
            with open(self.file_name, 'r', encoding='utf-8') as file:
                keyboard_exec = KeyBoardController()
                line = file.readline()
                while line:
                    obj = json.loads(line)
                    if obj['name'] == 'keyboard':
                        if obj['event'] == 'press':
                            keyboard_exec.press(KeyCode.from_vk(obj['vk']))
                            time.sleep(moveTime)

                        elif obj['event'] == 'release':
                            keyboard_exec.release(KeyCode.from_vk(obj['vk']))
                            time.sleep(moveTime)
                    line = file.readline()
                startExecuteBtn['text'] = '开始回放'
                startExecuteBtn['state'] = 'normal'
            self.execute_count = self.execute_count - 1


# 鼠标动作监听
class MouseActionListener(threading.Thread):
    esc_key = False

    def __init__(self, file_name='mouse.action'):
        super().__init__()
        self.file_name = file_name

    def close_listener(self, listener):
        if self.esc_key:
            listener.stop()

    def run(self):
        with open(self.file_name, 'w', encoding='utf-8') as file:
            # 鼠标移动事件
            def on_move(x, y):
                template = mouse_action_template()
                template['event'] = 'move'
                #template['location']['x'] = x/rate
                #template['location']['y'] = y/rate
                template['location']['x'] = x
                template['location']['y'] = y
                file.writelines(json.dumps(template) + "\n")
                file.flush()
                self.close_listener(mouseListener)

            # 鼠标点击事件
            def on_click(x, y, button, pressed):
                template = mouse_action_template()
                template['event'] = 'click'
                template['target'] = button.name
                template['action'] = pressed
                #template['location']['x'] = x/rate
                #template['location']['y'] = y/rate
                template['location']['x'] = x
                template['location']['y'] = y
                file.writelines(json.dumps(template) + "\n")
                file.flush()
                self.close_listener(mouseListener)

            # 鼠标滚动事件
            def on_scroll(x, y, x_axis, y_axis):
                template = mouse_action_template()
                template['event'] = 'scroll'
                #template['location']['x'] = x_axis/rate
                #template['location']['y'] = y_axis/rate
                template['location']['x'] = x_axis
                template['location']['y'] = y_axis
                file.writelines(json.dumps(template) + "\n")
                file.flush()
                self.close_listener(mouseListener)

            with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as mouseListener:
                mouseListener.join()


# 鼠标动作执行
class MouseActionExecute(threading.Thread):

    def __init__(self, file_name='mouse.action', execute_count=0):
        super().__init__()
        self.file_name = file_name
        self.execute_count = execute_count

    def run(self):
        while self.execute_count > 0:
            with open(self.file_name, 'r', encoding='utf-8') as file:
                mouse_exec = MouseController()
                line = file.readline()
                while line:
                    obj = json.loads(line)
                    if obj['name'] == 'mouse':
                        if obj['event'] == 'move':
                            mouse_exec.position = (obj['location']['x'], obj['location']['y'])
                            time.sleep(moveTime)
                        elif obj['event'] == 'click':
                            if obj['action']:
                                if obj['target'] == 'left':
                                    mouse_exec.press(Button.left)
                                else:
                                    mouse_exec.press(Button.right)
                            else:
                                if obj['target'] == 'left':
                                    mouse_exec.release(Button.left)
                                else:
                                    mouse_exec.release(Button.right)
                            time.sleep(moveTime)
                        elif obj['event'] == 'scroll':
                            mouse_exec.scroll(obj['location']['x'], obj['location']['y'])
                            time.sleep(moveTime)
                    line = file.readline()
            self.execute_count = self.execute_count - 1





startListenerBtn={"text":"开始录制"}
startExecuteBtn={'text':'开始回放'}

class anjian(QWidget,Ui_Dialog):
    def __init__(self):
        global rate,moveTime
        desktop = QApplication.desktop()
        width = desktop.width()
        height = desktop.height()
        rate = round(desktop.width() / desktop.height(), 2)
        print("屏幕宽度：", desktop.width(), "屏幕高度：",desktop.height())
        super(anjian,self).__init__()
        self.setupUi(self,width,height)

        self.startDelayTime = 2
        self.reSeeDelayTime = 2
        self.reSeeTimes = 1
        self.startBtnFlag = 0
        self.endBtnFlag = 0
        self.KeyPress = KeyboardActionListener()
        self.KeyPress._signal.connect(self.callbacklog)
        self.pushButton.clicked.connect(lambda: self.command_adapter('listener'))
        self.pushButton_2.clicked.connect(lambda: self.command_adapter('execute'))
        moveTime = int(self.spinBox_5.value())/1000.0
        #print(moveTime)
    def callbacklog(self):
        self.pushButton.setText("开始录制")
        #print("I get")
    def command_adapter(self,action):
        moveTime = int(self.spinBox_5.value()) / 1000.0
        print("鼠标每次更新时间为：",moveTime,"秒")
        self.reSeeTimes = int(self.spinBox_3.value())
        #print("重复次数：", self.reSeeTimes, "次")
        if action == 'listener':
            if startListenerBtn['text'] == '开始录制':
                print("开始录制")
                #return
                custom_thread_list = [
                    {
                        'obj_thread': self.KeyPress,
                        'obj_ui': startListenerBtn,
                        'final_text': '录制中...esc停止录制'
                    },
                    {
                        'obj_thread': MouseActionListener(),
                        'obj_ui': None,
                        'final_text': None
                    }
                ]
                self.startBtnFlag = 1 if self.startBtnFlag==0 else 0
                self.pushButton.setText(custom_thread_list[0]['final_text'] if self.startBtnFlag==1 else "开始录制")
                MouseActionListener.esc_key = False
                self.startDelayTime = int(self.spinBox.value())
                #print(self.startDelayTime)
                UIUpdateCutDownExecute(self.startDelayTime, custom_thread_list).start()

        elif action == 'execute':
            if startExecuteBtn['text'] == '开始回放':
                #print("开始回放")
                #return
                custom_thread_list = [
                    {
                        # 'obj_thread': KeyboardActionExecute(execute_count=playCount.get()),
                        'obj_thread': KeyboardActionExecute(execute_count=self.reSeeTimes),
                        'obj_ui': startExecuteBtn,
                        'final_text': '回放中...关闭程序停止回放'
                    },
                    {
                        # 'obj_thread': MouseActionExecute(execute_count=playCount.get()),
                        'obj_thread': MouseActionExecute(execute_count=self.reSeeTimes),
                        'obj_ui': None,
                        'final_text': None
                    }
                ]
                self.endBtnFlag = 1 if self.endBtnFlag == 0 else 0
                self.pushButton_2.setText(custom_thread_list[0]['final_text'] if self.endBtnFlag == 1 else "开始回放")
                # UIUpdateCutDownExecute(endTime.get(), custom_thread_list).start()
                self.reSeeDelayTime = int(self.spinBox_2.value())
                #print(self.reSeeDelayTime)
                UIUpdateCutDownExecute(self.reSeeDelayTime, custom_thread_list).start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = anjian()
    ex.show()
    sys.exit(app.exec_())

