#GUI Client for the Proxy Server.
import wx           #GUI Framework
from threading import Thread #For spawning multiple threads(one for the GUI, one for the proxy)
from UI_Panel import BlacklistPanel, CachePanel, LogPanel, MainPanel #Each of these is a tab.

import proxyServer #The proxy Server itself
 
#This class is a GUI for the Proxy Server. It is a WX Notebook 
class ProxyServerGUI(wx.Frame):
    #Creates a GUI, window size 550x400 and with  a position of 120, 90
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "Simple Proxy Server",
                          size=(550,400),
                          pos=(120, 90)
                          )
        #Constructor creates a frame to hold the Notebook, with "Simple Proxy Server" as the window title
        self.server = proxyServer.proxyServer(self) #Creates an instance of the Proxy Server
        #Create the Notebook, and put it on a blank panel
        panel = wx.Panel(self)
        self.notebook = self.createNotebook(panel)
        #Shape the main window
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        # Add the MenuBar to the Frame content.
        self.createMenu()
        self.Layout()
        #Display it all
        self.Show()

 
    def createNotebook(self, panel):
        #Creates a "Notebook", or a tabbed layout view
        notebook = wx.Notebook(panel)
        #Creates four panels, one for each tab, and returns an instance of the notebook
        #Create the main tab
        self.maintab = MainPanel(notebook, self)
        notebook.AddPage(self.maintab, "Main")
        #Create the blacklist tab
        self.blacklisttab = BlacklistPanel(notebook, self)
        notebook.AddPage(self.blacklisttab, "Blacklist")
        #Create the caching tab
        self.cachetab = CachePanel(notebook, self)
        notebook.AddPage(self.cachetab, "Cache")
        #Create the logging tab
        self.logtab = LogPanel(notebook, self)
        notebook.AddPage(self.logtab, "Log")
        #Return the created notebook
        return notebook

    def createMenu(self):
        #Creates the menu bar, gives the window option and help sort of...
        self.CreateStatusBar()
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

if __name__ == '__main__':
    #Run the program if script is ran from terminal
    app = wx.App(False)
    frame = ProxyServerGUI()
    app.MainLoop()