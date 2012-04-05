import wx               #Used for the UI
import webbrowser       #Used to preview files
import os
import datetime         #To add timestamp when saving to the Logfile
import sys              #For exiting
import md5              #For Caching

#"Main" Panel
class MainPanel(wx.Panel):
    def __init__(self, parent, gui):
        #Constructor.
        wx.Panel.__init__(self, parent)
        self.gui = gui  #Refernce to GUI, allows each panel to communicate
        self.createButtons()    #Does the layout and bindings
        #Flags to allow same button to do different things
        self.running = False
        self.UsingProxy = False

    def createButtons(self):
        #Proxy Settings Label
        self.h1 = wx.StaticText(self, label="Proxy Settings", pos=(10, 10))

        #Username input
        self.nameLabel = wx.StaticText(self, label="Username:", pos=(10, 50))
        self.editname = wx.TextCtrl(self, value=self.gui.server.uname, pos=(10, 70), size=(150,-1))

        #Password input
        self.pwLabel = wx.StaticText(self, label="Password:", pos=(10, 100))
        self.editpw = wx.TextCtrl(self, value=self.gui.server.pword, pos=(10, 120),style=wx.TE_PASSWORD, size=(150,-1))

        #Save Proxy Settings Button
        self.save =wx.Button(self, label="Save", pos=(10, 160))
        self.clear =wx.Button(self, label="Clear", pos=(90, 160))
        self.closeProgram =wx.Button(self, size=(150, -1),label="Quit", pos=(10, 190))

        self.Bind(wx.EVT_BUTTON, self.CloseAll, self.closeProgram)

        #Server Settings:
        #Label
        self.h2 = wx.StaticText(self, label="Server Settings", pos=(330, 10))
        #Server Status
        self.status = wx.StaticText(self, label="Status: Stopped", pos=(330, 30))
        #Port
        self.portlabel = wx.StaticText(self, label="Port:", pos=(330, 70))
        self.editport = wx.TextCtrl(self, value=str(self.gui.server.port), pos=(330, 110), size=(60,-1))
        #Start/Stop Button
        self.startstop =wx.Button(self, label="Start", pos=(410, 110))

        #Bindings
        self.Bind(wx.EVT_BUTTON, self.startstopserver,self.startstop)
        self.Bind(wx.EVT_BUTTON, self.saveProxyDetails,self.save)
        self.Bind(wx.EVT_BUTTON, self.clearProxyDetails,self.clear)

    def startstopserver(self, event):
        #Check if server is running
        if self.running == False:
            #If it's not, then get the port, and check if it's valid
            port = self.editport.GetValue()
            if port != "":
                port = int(port)
                if port > 1900 and port < 2000:#Just a range I picked
                    self.running = True #Change running flag, so next time server will stop
                    message =  "Starting Proxy Server on port "+ str(port)
                    self.gui.logtab.appendToLog(message)
                    #Starts the server
                    self.gui.server.createServer("127.0.0.1", port)
                    #Spawn new thread for the Server
                    self.gui.server.daemon = True
                    self.gui.server.start()
                    #Update GUI
                    self.status.SetLabel("Status: Running")
                    self.startstop.SetLabel("Stop")
                else:
                    #Log that an invalid port was used
                    message = "Port is not in valid range"
                    self.gui.logtab.appendToLog(message)
                    self.editport.SetValue("")
            else:
                #Port cannot be blank, so log this
                message = "Please enter a port"
                self.gui.logtab.appendToLog(message)
        else:
            #Server is running, so stop the server, log it and update UI
            self.gui.server.stopServer()
            message =  "Stopping Proxy Server."
            self.gui.logtab.appendToLog(message)
            self.status.SetLabel("Status: Stopped")
            self.startstop.SetLabel("Start")
            self.running = False



    #On clicking the SAVE button, this event is triggered. The proxy username and PW is changed
    def saveProxyDetails(self, event):
        #Get uname and PW
        name = self.editname.GetValue()
        pw = self.editpw.GetValue()
        if name != "" and pw != "":
            #Update the server variables, and change the URLLIB2 Opener
            message =  "Proxy Username and password saved"
            self.gui.logtab.appendToLog(message)
            self.gui.server.uname = name
            self.gui.server.pword = pw
            self.gui.server.proxySign()
        else:
            message =  "Required fields cannot be left blank"
            self.gui.logtab.appendToLog(message)

    def clearProxyDetails(self, event):
        #Simply clears the form, and deletes the server variables
        message = "Clearing Proxy Details"
        self.gui.logtab.appendToLog(message)

        self.editname.SetValue("")
        self.editpw.SetValue("")
        self.gui.server.uname = ""
        self.gui.server.pword = ""
        self.gui.server.proxySign()

    def CloseAll(self, event):
        #Closes the program on clicking
        #First, some housekeeping
        message = "Program Closing"
        self.gui.logtab.appendToLog(message)
        if self.running:
            self.gui.server.stopServer()
            self.running = False    
        self.gui.logtab.SaveLogToFile("")
        f = open("./cache/sites", "w")
        if self.gui.server.cacheList:
            for i in self.gui.server.cacheList:
                f.write(i+'\n')
        f.close()
        sys.exit()

"""
This panel handles all the required info for the Blacklisting Panel
"""
class BlacklistPanel(wx.Panel):
    def __init__(self, parent, gui):
        self.gui = gui  #Create a reference to the GUI so can access other classes
        wx.Panel.__init__(self, parent)
        self.createDisplay()        #does all the layout
    
    def createDisplay(self):
        self.blocklist = self.gui.server.blacklist #Uses the server blacklist,
        self.blocklistlabel = wx.StaticText(self, label="List of Blocked sites", pos=(10, 10))

        #Listbox Controllor
        self.listbox = wx.ListBox(self, wx.ID_ANY, style=wx.LB_EXTENDED,choices=self.blocklist, pos=(10, 30), size=(320, 270))

        #Right hand side box:
        self.removeChecked =wx.Button(self, size=(130, -1),label="Remove Selected", pos=(360, 110))
        self.enterprompt = wx.StaticText(self, label="Enter Host/IP to block:", pos=(360, 200))
        self.editBlocked = wx.TextCtrl(self, value="", pos=(360, 220), size=(140,-1))
        self.block =wx.Button(self, size=(130, -1),label="Block", pos=(360, 250))

        #Bindings for the buttons:
        #Syntax is EVENT TYPE, CALLBACK, BOUND_TO
        self.Bind(wx.EVT_BUTTON, self.RemoveCheckedSite,self.removeChecked)
        self.Bind(wx.EVT_BUTTON, self.BlockInputtedSite,self.block)

    #Callback function that removes the selected website on the list from the checklist
    def RemoveCheckedSite(self, event):
        id = self.listbox.GetSelection()#Gets the ID of the selected site
        #If a site is selected, remove it, otherwise just log it
        if id > -1 :
            message = "Removing "+self.blocklist[id]
            self.blocklist.pop(id)#Pop the host from the list, and update the GUI
            self.listbox.Delete(id)
        else:
            message = "No site selected to remove from Blacklist"
        self.gui.logtab.appendToLog(message)

    #Adds a site to the blacklist. Callback function
    def BlockInputtedSite(self, event):

        hostblock = self.editBlocked.GetValue()
        if hostblock != "":
            #A value was put into the box, so add the host to the list, and update the GUI
            self.blocklist.append(hostblock)
            self.listbox.Append(hostblock)
            self.editBlocked.SetValue("")
            message = "Blocking "+hostblock
        else:
            #No value was given, so just log
            message = "Empty string is not a valid host/IP to block"
        self.gui.logtab.appendToLog(message)

class CachePanel(wx.Panel):
    def __init__(self, parent, gui):
        wx.Panel.__init__(self, parent)
        self.gui = gui
        self.blocklistlabel = wx.StaticText(self, label="List of Cached sites", pos=(10, 10))
        #Listbox Controllor
        self.listbox = wx.ListBox(self, wx.ID_ANY,style=wx.LB_EXTENDED, choices=self.gui.server.cacheList,pos=(10, 30), size=(320, 270))
        #self.listbox.Bind(wx.EVT_LISTBOX, self.listboxClick)

        #Right hand side box:
        self.viewSelected =wx.Button(self, size=(130, -1), label="View Selected", pos=(360, 110))
        self.removeSelected =wx.Button(self, size=(130, -1), label="Remove Selected", pos=(360,150))
        self.clearCache =wx.Button(self, size=(130, -1), label="Clear Cache", pos=(360, 250))

        self.Bind(wx.EVT_BUTTON, self.RemoveSelectedSite,self.removeSelected)
        self.Bind(wx.EVT_BUTTON, self.ViewSelectedSite,self.viewSelected)
        self.Bind(wx.EVT_BUTTON, self.ClearCacheList,self.clearCache)


    def RemoveSelectedSite(self, event):
        #Deletes cached file
        id = self.listbox.GetSelection()    #Get id of cached file
        if id > -1 :
            message = "Removing Cached data for"+ self.gui.server.cacheList[id]
            #Delete the file, from cachelist and update GUI
            os.remove('./cache/'+md5.md5(self.gui.server.cacheList[id]).hexdigest())
            self.gui.server.cacheList.pop(id)
            self.listbox.Delete(id)
        else:
            message = "No site selected to view cache of"
        self.gui.logtab.appendToLog(message)

    #Launch browser to view cached copy of the site.
    def ViewSelectedSite(self, event):
        id = self.listbox.GetSelection()#Get ID
        if id > -1:
            webbrowser.get('firefox').open('file://'+os.getcwd()+'/cache/'+md5.md5(self.gui.server.cacheList[id]).hexdigest())#This loops back through the proxy and serves up the cached copy of the site.
            message = "Viewing cached copy of "+self.gui.server.cacheList[id]
        else:
            message = "Invalid selection of cached site to view"
        self.gui.logtab.appendToLog(message)

    #Deletes all files in the cache folder, and pops all Caches from the list, updates the GUI
    def ClearCacheList(self, event):
        self.gui.logtab.appendToLog('Clearing Cache List')
        for i in self.gui.server.cacheList:
            os.remove('./cache/'+md5.md5(i).hexdigest())
        self.gui.server.cacheList = []
        self.listbox.SetItems([])
        f = open("./cache/sites","w")
        f.write("")
        f.close()
        #Remember to delete the files


#This is the Logging Panel
class LogPanel(wx.Panel):
    def __init__(self, parent, gui):
        #Constructs the frame
        wx.Panel.__init__(self, parent)
        self.gui = gui  #Refernce to the gui, allowing the logger to be called
        self.blocklistlabel = wx.StaticText(self, label="Log:", pos=(10, 10))

        #Instantiate empty list as log
        self.logList = []
        #Listbox Controllor
        self.listbox = wx.ListBox(self, wx.ID_ANY,style=wx.LB_EXTENDED, pos=(10, 30), size=(320, 270))
        #self.listbox.Bind(wx.EVT_LISTBOX, self.listboxClick)

        #Right hand side box:
        self.saveLog =wx.Button(self, size=(130, -1), label="Save", pos=(360, 110))
        self.clearLog =wx.Button(self, size=(130, -1), label="Clear", pos=(360,150))

        #Bind event handlers to save and clear
        self.Bind(wx.EVT_BUTTON, self.SaveLogToFile,self.saveLog)
        self.Bind(wx.EVT_BUTTON, self.ClearLogFromList,self.clearLog)

    #Function is called on each event, and appends the event to the log each time.
    def appendToLog(self, string):
        self.logList.append(string)
        self.listbox.Append(string)     #Remember to update the GUI

    def SaveLogToFile(self, event):
        #Write the log to proxylog.log file
        self.appendToLog("Saving Log")
        f = open("./proxylog.log", 'a')#Open file in append mode
        #Print a timestamp onto the log file. 
        #Gotten from http://stackoverflow.com/questions/2204856/write-timestamp-to-file-every-hour-in-python
        f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n')
        #Write the log to the textfile
        for i in self.logList:
            f.write(i+'\n')
        f.close()

    #Clear up the log list.
    def ClearLogFromList(self, event):
        #Blank the local copy, and the GUI copy too
        self.logList = []
        self.listbox.SetItems([])
        #Log clearing the log
        self.appendToLog("Clearing Log")