#!/usr/bin/env python3

import sys, os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QListWidget, QListWidgetItem, QComboBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

import comms
comms.client(comms.address)

from ufContentProvider import prepareImageDir, fetchListData, fetchTargets
imageDir = prepareImageDir()

targetsList = fetchTargets()

def entry():
    app = QApplication(sys.argv)
    pyqtgui = Gui()
    sys.exit(app.exec_())

class Gui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.toolbar = self.addToolBar('Things')
        self.addBtn('video-display', 'Toggle Visibility', self.ipcToggleVisibility, self.toolbar)
        self.addBtn('media-playback-start', 'Toggle Play', self.ipcTogglePlay, self.toolbar)
        self.addBtn('view-fullscreen', 'Toggle Fullscreen', self.ipcToggleFullscreen, self.toolbar)
        self.toolbar.addSeparator()
        self.targetBox = QComboBox()
        self.targetBox.addItems(targetsList)
        self.toolbar.addWidget(self.targetBox)
        self.toolbar.addSeparator()
        self.addBtn('reload', 'Refresh', self.funRefresh, self.toolbar)
        self.addBtn('preferences', 'Settings', self.funComms, self.toolbar)
        self.toolbar.addSeparator()
        self.addBtn('exit', 'Exit', qApp.quit, self.toolbar)

        self.list = QListWidget(self)
        self.list.setIconSize(QSize(120,120))


        #self.list.resize(300, 200)
        self.setCentralWidget(self.list)

        self.resize(QSize(600,500))
        self.setWindowTitle('Toolbar')
        self.show()

    def addBtn(self, icon, tip, action, toolbar):
        act = QAction(QIcon.fromTheme(icon), tip, self)
        act.triggered.connect(action)
        toolbar.addAction(act)

    def funComms(self):
        comms.send('test')

    def funRefresh(self):
        self.list.clear()
        target = self.targetBox.currentIndex() + 1
        print(target)

        data = fetchListData(target)
        for k in data:
            item = QListWidgetItem(QIcon(os.path.join(imageDir, str(k['ID']) + '.jpg')), k['Description'] + '\n' + k['Duration'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable) # set checkable flag
            item.setCheckState(Qt.Checked) # AND initialize check state
            self.list.addItem(item)

    def ipcToggleFullscreen(self):
        comms.send('toggle-fullscreen')
    def ipcTogglePlay(self):
        comms.send('toggle-play')
    def ipcToggleVisibility(self):
        comms.send('toggle-visibility')



    def ipcScreenEnable(self):
        comms.send('screen-enable')
    def ipcScreenBlack(self):
        comms.send('screen-black')
    def ipcFullscreen(self):
        comms.send('fullscreen')
    def ipcWindowed(self):
        comms.send('windowed')
    def ipcPlay(self):
        comms.send('play')
    def ipcPause(self):
        comms.send('pause')

    def ipcNext(self):
        comms.send('next')
    def ipcPrev(self):
        comms.send('prev')
    def ipcRefresh(self):
        comms.send('refresh')
    def ipcGet(self, item):
        comms.send('get-' + item)
    def ipcTarget(self, target):
        comms.send('target-' + target)
    def ipcDisable(self, listItemId):
        comms.send('disable-' + listItemId)
    def ipcEnable(self, listItemId):
        comms.send('enable-' + listItemId)
