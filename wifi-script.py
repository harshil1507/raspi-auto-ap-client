import os

scriptWD = ""
debug = False

# Class of different styles
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

def installApplications() :
  """ 
    Update and install all required applications
  """
  # print name of Function
  print(style.RED + 'Running: ' + installApplications.__name__)
  # update package list -y for unattended install
  print(style.YELLOW + "Updating Applications")
  os.system("sudo apt-get update -y")

  # upgrade packages -y for unattended install
  os.system("sudo apt-get upgrade -y")

  print(style.YELLOW + "Installing required applications")
  # install hostapd and dnsmasq -y for unattended install
  os.system("sudo apt-get install hostapd dnsmasq -y")

def stopServices() :
  """ 
    Stop Any Running services and unmask hostapd
  """
  # stop services
  os.system("sudo systemctl stop hostapd")
  os.system("sudo systemctl stop dnsmasq")
  os.system("sudo systemctl stop dhcpcd")
  os.system("sudo systemctl disable hostapd")
  os.system("sudo systemctl disable dnsmasq")
  os.system("sudo systemctl disable dhcpcd")

  os.system("sudo systemctl unmask hostapd && sudo systemctl enable hostapd")

  # start custom script
  os.system("sudo sh /usr/local/bin/wifistart")

def setDirectory(path) :
  """ 
    Set Current Directory to a specfic path
    @param    path    to be set
    @return           current working directory
  """
  # change workdir to /etc
  os.chdir(path)
  cwd = os.getcwd()
  print(style.GREEN + "Settings Current Working Dir as -> ", cwd)
  return cwd

def readFile(path) :
  """ 
    Read a file
    @param    path    to the file
    @return           file's content
  """
  print(style.BLUE + 'Reading temp ' + path + ' | Path :' + style.RED + scriptWD + path)
  
  if path.count('/') > 2 :
    tempFile = open(path)
  else :
    tempFile = open(scriptWD + path)
    
  content = tempFile.read()
  tempFile.close()
  if debug:
    print(style.WHITE + content)
  return content

def setDHCPFile() :
  """ 
    Edit /etc/dhcpcd.conf file
  """

  # store current work dir (/etc) to pwd variable
  pwd = setDirectory('/etc')

  # set path to dhcpcd.conf file
  pathToDhcpcdConf = pwd + "/dhcpcd.conf"
  pathToDhcpcdConf = os.path.abspath(pathToDhcpcdConf)

  # reading temp file
  content = readFile('/dhcpcd.conf')
  
  # open dhcpcd.conf file in append mode
  print(style.GREEN + "Editing dhcpcd.conf")
  
  #erase any previous content
  open(pathToDhcpcdConf, 'w').close() 
  
  dhcpcd = open(pathToDhcpcdConf, "a")
  dhcpcd.writelines(content)
  dhcpcd.close()
  print(style.YELLOW + "File dhcpcd.conf configured")

def setDNSMasq() :
  """ 
    Saves the original, creates a new dnsmasq and defines it's settings.
  """
  # print name of Function
  print(style.RED + 'Running: ' + setDNSMasq.__name__)
  # make backup of dnsmasq.conf
  print(style.GREEN + "Making a copy of original File")
  os.system("sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig")

  content = readFile('/dnsmasq.conf')
  
  # create new dnsmasq.conf - open file in write mode to auto create
  # ip range is arbitrary but I have set the range to include the static ip of our ap interface
  pathToDnsmasq = "/etc/dnsmasq.conf"
  print(style.YELLOW + "Creating dnsmasq.conf")
  dnsmasq = open(pathToDnsmasq, "w")
  
  dnsmasq.write(content)
  dnsmasq.close()
  print(style.YELLOW + "dnsmasq.conf created")

def fetchChannels() :
  """ 
    Fetch the channel of the configured wlan0
    @return     the Channel
  """
  print(style.RED + 'Running: ' + fetchChannels.__name__)
  # Fetch channel of the wifi network rpi is currently connected to
  interfaces = os.popen("iwconfig").read()
  interfaces = str(interfaces)
  interfaces = interfaces.split()
  selectedInterface = interfaces[0]

  # get channel of the connected wifi network
  selectedChannel = ''
  getChannelCmd = "iw " + selectedInterface + " info"
  channels = os.popen(getChannelCmd).read()
  channels = channels.splitlines()
  for i in channels:
      if(i.find('channel') != -1):
          selectedChannel = i
  selectedChannel = selectedChannel.split()
  selectedChannel = selectedChannel[1]
  print(style.BLUE + 'Channel Found : ' + selectedChannel)
  return selectedChannel

def setHostAPD(SSID, PSK) :
  """ 
    Set hostapd.conf file
  """
  
  # getting the Channel
  selectedChannel = fetchChannels()
  
  # read and update file
  content = readFile('/hostapd.conf')
  content = content.replace("channel=1", "channel=" + selectedChannel)
  content = content.replace("ssid=yourSSIDher", "ssid=" + SSID)
  content = content.replace("wpa_passphrase=passwordBetween8and64charactersLong", "wpa_passphrase=" + PSK)
  print(style.GREEN + 'Content to be saved on the file -> ' + content)
  
  # create hostapd.conf file
  pathToHostapdConf = "/etc/hostapd/hostapd.conf"
  print(style.YELLOW + "Creating hostapd.conf")
  hostapdConf = open(pathToHostapdConf, "w")
  
  hostapdConf.writelines(content)
  hostapdConf.close()
  
  
  
  # edit /etc/default/hostapd
  path = '/etc/default/hostapd'
  content = readFile(path)
  if content.find('DAEMON_CONF="/etc/hostapd/hostapd.conf"') :
    print(style.GREEN + "DAEMON_CONF are already Updated")
  else :
    f = open(path, "a")
    print(style.CYAN + "Updating DAEMON_CONF")
    f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"')
    f.close()
  

def setStartupScript() :
  """ 
    Create startup Script
  """
  # create startup script
  startUpScriptPath = '/usr/local/bin/wifistart'
  
  # Read Temp File
  content = readFile('/wifistart')
  
  print(style.YELLOW + "Creating startup script")
  startUpScript = open(startUpScriptPath, "w")
  startUpScript.writelines(content)
  startUpScript.close()
  
  # edit /etc/rc.local
  pathToRcLocal = '/etc/rc.local'
  print(style.YELLOW + "Editing rc.local")
  rcLocalOriginal = open(pathToRcLocal, "r+")
  modifiedRcLocal = rcLocalOriginal.readlines()
  modifiedRcLocal.insert(-1, "/bin/bash /usr/local/bin/wifistart\n")
  rcLocalOriginal.seek(0)
  rcLocalOriginal.writelines(modifiedRcLocal)
  rcLocalOriginal.close()



""" main """
# Start by settings the working directory of the script
scriptWD = os.path.abspath(os.getcwd())
print(style.GREEN + "Saving current directory ( " + scriptWD + " ) as Global")
#installApplications()
setDHCPFile()
setDNSMasq()
setHostAPD("raspberrypi", "NOPSK")
setStartupScript()
stopServices()