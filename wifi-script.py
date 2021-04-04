import os

# update package list -y for unattended install
os.system("sudo apt-get update -y")

# upgrade packages -y for unattended install
os.system("sudo apt-get upgrade -y")

# install hostapd and dnsmasq -y for unattended install
os.system("sudo apt-get install hostapd dnsmasq -y")

# edit /etc/dhcpcd.conf file

# change workdir to /etc
os.chdir("/etc")

# store current work dir (/etc) to pwd variable
pwd = os.getcwd()
print("PWD -> ", pwd)

# set path to dhcpcd.conf file
pathToDhcpcdConf = pwd + "/dhcpcd.conf"
pathToDhcpcdConf = os.path.abspath(pathToDhcpcdConf)

# open dhcpcd.conf file in append mode
print("editing dhcpcd.conf")
dhcpd = open(pathToDhcpcdConf, "a")
dhcpd.write(
    "interface uap0\n\tstatic ip_address=192.168.50.1/24\n\tnohook wpa_supplicant")
dhcpd.close()
print("dhcpcd.conf configured")

# make backup of dnsmasq.conf
os.system("sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig")

# create new dnsmasq.conf - open file in write mode to auto create
# ip range is arbitrary but I have set the range to include the static ip of our ap interface
pathToDnsmasq = pwd + "/dnsmasq.conf"
print("creating dnsmasq.conf")
dnsmasq = open(pathToDnsmasq, "w")
dnsmasq.write("interface=lo,uap0\nbin-interfaces\nserver=8.8.8.8\ndomain-needed\nbogus-priv\ndhcp-range=192.168.50.1,192.168.50.150,12h\n")
dnsmasq.close()
print("dnsmasq.conf created")

# Fetch channel of the wifi network rpi is currently connected to
interfaces = os.popen("iwconfig").read()
interfaces = str(interfaces)
interfaces = interfaces.split()
selectedInterface = interfaces[0]

# get channel of the connected wifi network
selectedChannel = ''
getChannelCmd = "iw" + selectedInterface + "info"
channels = os.popen(getChannelCmd).read()
channels = channels.splitlines()
for i in channels:
    if(i.find('channel') != -1):
        selectedChannel = i
selectedChannel = selectedChannel.split()
selectedChannel = selectedChannel[1]

# create hostapd.conf file
pathToHostapdConf = pwd + "/hostapd/hostapd.conf"
print("Creating hostapd.conf")
hostapdConf = open(pathToHostapdConf, "w")
hostapdConfigToWrite = "channel={channel}\nssid=raspi\nwpa_passphrase=raspberry\ninterface=uap0\nhw_mode=g\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=0\nwpa=2\nwpa_key_mgmt=WPA-PSK\nwpa_pariwise=TKIP\nrsn_pairwise=CCMP\ndriver=nl80211"
hostapdConf.write(hostapdConfigToWrite)
hostapdConf.close()
print("created hostapd.conf")

# edit /etc/default/hostapd
path = pwd + '/default/hostapd'
f = open(path,"a")
f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"')
f.close()

# create startup script
os.chdir("usr/local/bin")
newPwd = os.getcwd()
startUpScriptPath = newPwd + '/wifistart'
print("creating startup script")
startUpScript = open(startUpScriptPath, "w")
startUpScript.write('#!/bin/bash\n\necho "stopping newtwork services if running"\nsystemctl stop hostapd.service\nsystemctl stop dnsmasq.service\nsystemctl stop dhcpcd.service\n\necho "Removing uap0 interface"\niw dev uap0 del\necho "adding uap0 interface"\niw dev wla0 interface add uap0 type __ap\necho "IPV4 forwarding setting..."\nsysctl net.ipv4.ip_forward=1\necho "editing IP tables"\niptables -t nat -A POSTROUTING -s 192.168.70.0/24 ! -d 192.168.70.0/24 -j MASQUERADE\nifconfig uap0 up\n\necho "Starting hostapd service..."\nsystemctl start hostapd.service\nsleep 10\n\necho "Starting dhcpcd service..."\nsystemctl start dhcpcd.service\nsleep 5\n\necho "Starting dnsmasq service..."\nsystemctl start dnsmasq.service\necho "wifistart DONE"')
startUpScript.close()
print("startup script created")

# edit /etc/rc.local
os.chdir('/etc')
pwd = os.getcwd()
pathToRcLocal = pwd + '/rc.local'
print("editing rc.local")
rcLocalOriginal = open(pathToRcLocal, "r+")
modifiedRcLocal = rcLocalOriginal.readlines();
modifiedRcLocal.insert(-1, "/bin/bash /usr/local/bin/wifistart\n")
rcLocalOriginal.writelines(modifiedRcLocal)
rcLocalOriginal.close()
print("rc.local edited")

# stop services
os.system("sudo systemctl stop hostapd")
os.system("sudo systemctl stop dnsmasq")
os.system("sudo systemctl stop dhcpcd")
os.system("sudo systemctl disable hostapd")
os.system("sudo systemctl disable dnsmasq")
os.system("sudo systemctl disable dhcpcd")

# start custom script
os.system("sudo sh /usr/local/bin/wifistart")