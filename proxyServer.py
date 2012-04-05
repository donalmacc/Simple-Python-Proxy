"""
Donal Mac Carthy
09706054
"""

import socket                   #Necessary for Connections to the browser
import os                       #For checking files, getting list of files
import string                   #Splits up the headers, etc
import urllib2                  #For connectionis with the WWW
from md5 import md5             #Used for naming cache files
from threading import Thread    #Spawning a new thread each time a request comes in

#This is the main class, does most of the work.
class proxyServer(Thread):

    def __init__(self, gui):
        #Constructor, initialises blank lists that can be seen all across the GUI
        Thread.__init__(self)
        self.gui = gui  #Reference to the GUI, allows everything to communicate nicely
        self.loadVariables()

    def loadVariables(self):
        #The list of blacklisted sited, and cached sites
        self.blacklist = []
        self.cacheList = []
        self.fillcachelist()    #Fills the cached list from last time
        #Default Proxy details, can be changed in the GUI, login for TCD proxy
        self.uname = 'UNAME'
        self.pword = 'PASSWORD'
        #The port that my FF is configured to use
        self.port = 1913
        #Create a new socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #Quicker timeouts, used to close socket even if it was closed improperly

    def createServer(self, host, port):
        #Creates an instance of the server, and ties the proxy to the TCD proxy.
        self.port = port
        self.s.bind((host, port))#Listen on localhost:port specified above/UI
        self.signProxy()    #Link the TCD/SCSS proxy
 
    def signProxy(self):
        #Creates a URLLIB2 opener and installs it globally, allows to connect via tcdproxy with a valid username and password
        paddr = "http://"+self.uname+":"+self.pword+"@www-proxy.scss.tcd.ie:8080" #Creates the URL
        proxy = urllib2.ProxyHandler({'http': paddr})#PRoxy type, and URl specified
        #Create and install
        auth = urllib2.HTTPBasicAuthHandler()
        opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
        urllib2.install_opener(opener)      

    def run(self):
        #This function is not called directly, it is used for the thread
        message =  "Listening on port"+ str(self.port)
        self.gui.logtab.appendToLog(message)#Log the fact that the server is listening
        self.s.listen(8)
        while(self.gui.maintab.running):
            #Infinte loop, but can be interrupted
            #Listen with a backlog of 8 requests, and spawn a thread for each request received
            t = threadedUrl(self, self.s)
            t.start()
        #close the socket if main loop has been stopped
        self.s.close()

    def makeCall(self, c):
        #Request a response from a URL, given a request from a browser
        #Take in the browser request
        data = c.recv(4096)
        if data:
            #break up the request
            header = data.split()
            if header[0] =='CONNECT':
                #HTTPS request
                self.gui.logtab.appendToLog("CONNECT request detected, passing.")
                x = "Sorry, no HTTPS support"
            else:
                #Check if site is blacklisted
                if self.checkBlackList(header[4]) is False:
                    message =  "Requesting: "+ header[1]
                    self.gui.logtab.appendToLog(message)
                    x = self.visitUrl(header[1],header) #Make request
                else:
                    #Site is blacklisted, so cannot access it
                    x = "This site has been blacklisted, sorry."
        else:
            #No headers sent, so send back blank response
            x = ""
        c.sendall(x)    #Send response
        self.gui.logtab.appendToLog('Sent all of '+ header[1])#Log the request as finsihed
        c.close()       #Close the client response

    #Checks the cache, and also makes the URL calls if necessary
    def visitUrl(self, url, header):
        #MD5 the url, to make it a fixed length and easier to manage
        md5url =  md5(url).hexdigest()
        if header[0] =='POST':
            postdata = header[-1]#POST data is now postdata
            ignoreCache = True
            self.gui.logtab.appendToLog('POST data detected, ignoring cache.')
        else:
            postdata = None
            ignoreCache = False
        if self.checkCache(url) and not ignoreCache:
            #Page has been cached before                
            data = self.loadCached(url, md5url)
        else:
            #Page hasn't been cached, so create a request
            req = urllib2.Request(url, postdata)
            #Add the FF user agent so we can bypass certain forms
            req.add_header('User-agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:9.0.1) Gecko/20100101 Firefox/9.0.1')
            try:
                #Try requesting from the URL, but catch errors if they come along
                conn = urllib2.urlopen(req)
            except urllib2.HTTPError as e:
                if hasattr(e, 'reason'):
                    self.gui.logtab.appendToLog('Failed to reach server. Reason: '+ str(e.reason))
                elif hasattr(e, 'code'):
                    self.gui.logtab.appendToLog('Unable to fulfil request. Error code'+ str(e.code))
                data = ""
            else:
                #If all is successful, read the response, and cache it for later use
                data = conn.read()
                if not ignoreCache:
                    self.writeToCache(data, url)
                #return the response, whther it is from the cache or from the web.
        return data

    #Checks if a website is blacklisted, either by hostname or IP address
    def checkBlackList(self, host):
        #Get IP of the requested host
        ip = socket.gethostbyname(host)
        #Loop through blacklist, and check if the host is found
        for blocked in self.blacklist:
            if host.find(blocked) != -1 or ip.find(blocked) != -1:
                #Host is blacklisted, not allowed access
                self.gui.logtab.appendToLog('Attempted to access Blacklisted site: '+host+' at IP '+ip);
                return True
        #Host isn't on blacklist, so proceed with request
        return False

    def appendtoBlackList(self, host):
        self.blacklist.append(host) #Simply add a site to the blacklist

    def fillcachelist(self):
            self.cacheList = [line.strip() for line in open('./cache/sites', "r")]

    def checkCache(self, url):
        #Checks if file is cached or not
        if any(url in s for s in self.cacheList):
            #The MD5 of the url was found in the cache folder, meaning page was cached previously
            #Serve this up as a response instead
            return True
        else:
            #Hasn't been found on the cachelist.
            return False
    def loadCached(self, url, md5url):
        #Serve a cached request to the user.
        self.gui.logtab.appendToLog('Serving up cached request of: '+url);  
        #Open the cached file    
        f = open('./cache/'+str(md5url), "r")
        html = f.read()
        return html

    def writeToCache(self, data, url):
        #Writes the HTML returned to the cache
        self.gui.logtab.appendToLog('Caching: '+url);
        md5url =  md5(url).hexdigest() #Gives the filename, to be opened for writing.
        self.cacheList.append(url) #Add the file to the cachelist
        self.gui.cachetab.listbox.Append(url)#Update the gui
        f = open('./cache/'+str(md5url),"w")#Open the file for writing
        f.write(data)#Write the HTML to a file
        f.close()#Close the file

    def stopServer(self):
        #Close socket connection
        self.gui.logtab.appendToLog("Closing Proxy Server")
        # self.s.shutdown(socket.SHUT_WR)
        self.s.close()
        try:
                #Try requesting from the URL, but catch errors if they come along
            conn = urllib2.urlopen('http://www.python.org')
        except urllib2.HTTPError as e:
            if hasattr(e, 'reason'):
                pass
            elif hasattr(e, 'code'):
                pass

"""
This class simply responds to a request from the proxy server, and spawns a new thread
for each one.
"""
class threadedUrl (Thread): 
    def __init__(self, server, s):
        Thread.__init__(self)
        self.thisServer = server
        if self.thisServer.gui.maintab.running:
            self.client, addr = s.accept()
        
    def run(self):
        # print self.name," Running"
        if self.thisServer.gui.maintab.running:
            self.thisServer.makeCall(self.client)
