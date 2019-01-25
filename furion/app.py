import os, os.path
import sys
import wx
import threading
import subprocess

from .furion import setup_server

ID_ICON_TIMER = wx.NewId()  
OPEN_CONFIG=wx.NewId()
SHOW_LOGS=wx.NewId()  


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class FurionTaskBarIcon(wx.TaskBarIcon):

    def __init__(self, parent):  
        wx.TaskBarIcon.__init__(self)  
        self.parentApp = parent  
        self.icon = wx.Icon(resource_path("furion.ico"), wx.BITMAP_TYPE_ICO)  
        self.CreateMenu()  
        self.SetIconImage()

    def CreateMenu(self):  
        self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.ShowMenu)  
        self.Bind(wx.EVT_MENU, self.parentApp.openConfig, id=OPEN_CONFIG)  
        self.Bind(wx.EVT_MENU, self.parentApp.showLogs, id=SHOW_LOGS)  
        self.menu=wx.Menu()  
        self.menu.Append(OPEN_CONFIG, "Open Config File")
        # self.menu.Append(SHOW_LOGS, "Show Logs")            
        self.menu.AppendSeparator()  
        self.menu.Append(wx.ID_EXIT, "Exit Furion")

    def ShowMenu(self,event):  
        self.PopupMenu(self.menu)

    def SetIconImage(self, mail=False):  
        self.SetIcon(self.icon)


class FurionFrame(wx.Frame):

    def __init__(self, parent, id, title):  
        wx.Frame.__init__(self, parent, -1, title, size = (1, 1),  
            style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)

        self.tbicon = FurionTaskBarIcon(self)  
        self.tbicon.Bind(wx.EVT_MENU, self.exitApp, id=wx.ID_EXIT)   
        self.Show(True)
        self.svr = None
        self.thr = threading.Thread(target=self.runServer)
        self.thr.setDaemon(1)
        self.thr.start()

    def runServer(self):
        self.svr = setup_server()
        self.svr.serve_forever()

    def exitServer(self):
        self.svr.server_close()

    def exitApp(self, event):  
        self.tbicon.RemoveIcon()  
        self.tbicon.Destroy()  
        self.exitServer()
        sys.exit()

    def openConfig(self, event):
        fpath = 'furion.cfg'  
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', fpath))
        elif os.name == 'nt': # For Windows
            os.startfile(fpath)
        elif os.name == 'posix': # For Linux, Mac, etc.
            subprocess.call(('xdg-open', fpath))

    def showLogs(self, event):  
        pass


def main(argv=None):  
    app = wx.App(False)  
    frame = FurionFrame(None, -1, ' ')  
    frame.Show(False)  
    app.MainLoop()

if __name__ == '__main__':  
    main()