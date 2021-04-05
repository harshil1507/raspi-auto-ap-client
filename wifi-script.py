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
dhcpcd = open(pathToDhcpcdConf, "a")
dhcpcd_content = ["interface uap0\n",
                  "\tstatic ip_address=192.168.50.1/24\n", "\tnohook wpa_supplicant\n"]
dhcpcd.writelines(dhcpcd_content)
dhcpcd.close()
print("dhcpcd.conf configured")

# make backup of dnsmasq.conf
os.system("sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig")

# create new dnsmasq.conf - open file in write mode to auto create
# ip range is arbitrary but I have set the range to include the static ip of our ap interface
pathToDnsmasq = pwd + "/dnsmasq.conf"
print("creating dnsmasq.conf")
dnsmasq = open(pathToDnsmasq, "w")
dnsmasq_content = ["interface=lo,uap0               #Use interfaces lo and uap0\n",
                   "bind-interfaces                 #Bind to the interfaces\n",
                   "server= 8.8.8.8  # Forward DNS requests to Google DNS\n",
                   "domain-needed  # Don't forward short names\n",
                   "bogus-priv  # Never forward addresses in the non-routed address spaces\n",
                   "# Assign IP addresses between 192.168.70.50 and 192.168.70.150 with a 12-hour lease time\n",
                   "dhcp-range= 192.168.70.50, 192.168.70.150, 12h"]
dnsmasq.write("interface=lo,uap0\nbind-interfaces\nserver=8.8.8.8\ndomain-needed\nbogus-priv\ndhcp-range=192.168.50.1,192.168.50.150,12h\n")
dnsmasq.close()
print("dnsmasq.conf created")

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

# create hostapd.conf file
pathToHostapdConf = pwd + "/hostapd/hostapd.conf"
print("Creating hostapd.conf")
hostapdConf = open(pathToHostapdConf, "w")
hostapdConfigToWrite = ["# Set the channel (frequency) of the host access point\n",
                        "channel={channel}\n".format(channel=selectedChannel),
                        "# Set the SSID broadcast by your access point (replace with your own, of course)\n",
                        "ssid=raspi\n",
                        "# This sets the passphrase for your access point (again, use your own)\n",
                        "wpa_passphrase=raspberry\n",
                        "# This is the name of the WiFi interface we configured above\n",
                        "interface=uap0\n",
                        "# Use the 2.4GHz band (I think you can use in ag mode to get the 5GHz band as well, but I have not tested this yet)\n",
                        "hw_mode=g\n",
                        "# Accept all MAC addresses\n",
                        "macaddr_acl=0\n",
                        "# Use WPA authentication\n",
                        "auth_algs=1\n",
                        "# Require clients to know the network name\n",
                        "ignore_broadcast_ssid=0\n",
                        "# Use WPA2\n",
                        "wpa=2\n",
                        "# Use a pre-shared key\n",
                        "wpa_key_mgmt=WPA-PSK\n",
                        "wpa_pairwise=TKIP\n",
                        "rsn_pairwise=CCMP\n",
                        "driver=nl80211\n",
                        "# I commented out the lines below in my implementation, but I kept them here for reference.\n",
                        "# Enable WMM\n",
                        "#wmm_enabled=1\n",
                        "# Enable 40MHz channels with 20ns guard interval\n",
                        "#ht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]\n"]
hostapdConf.writelines(hostapdConfigToWrite)
hostapdConf.close()
print("created hostapd.conf")

# edit /etc/default/hostapd
path = pwd + '/default/hostapd'
f = open(path, "a")
f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"')
f.close()

# create startup script
os.chdir("/usr/local/bin")
newPwd = os.getcwd()
startUpScriptPath = newPwd + '/wifistart'
print("creating startup script")
startUpScript = open(startUpScriptPath, "w")
startUpScriptToWrite = ['#!/bin/bash\n',

                        '# Redundant stops to make sure services are not running\n',
                        'echo "Stopping network services (if running)..."\n',
                        'systemctl stop hostapd.service\n',
                        'systemctl stop dnsmasq.service\n',
                        'systemctl stop dhcpcd.service\n',

                        '#Make sure no uap0 interface exists (this generates an error; we could probably use an if statement to check if it exists first)\n',
                        'echo "Removing uap0 interface..."\n',
                        'iw dev uap0 del\n',

                        '#Add uap0 interface (this is dependent on the wireless interface being called wlan0, which it may not be in Stretch)\n',
                        'echo "Adding uap0 interface..."\n',
                        'iw dev wlan0 interface add uap0 type __ap\n',

                        '#Modify iptables (these can probably be saved using iptables-persistent if desired)\n',
                        'echo "IPV4 forwarding: setting..."\n',
                        'sysctl net.ipv4.ip_forward=1\n',
                        'echo "Editing IP tables..."\n',
                        'iptables -t nat -A POSTROUTING -s 192.168.70.0/24 ! -d 192.168.70.0/24 -j MASQUERADE\n',

                        '# Bring up uap0 interface. Commented out line may be a possible alternative to using dhcpcd.conf to set up the IP address.\n',
                        '#ifconfig uap0 192.168.70.1 netmask 255.255.255.0 broadcast 192.168.70.255\n',
                        'ifconfig uap0 up\n',

                        '# Start hostapd. 10-second sleep avoids some race condition, apparently. It may not need to be that long. (?) \n',
                        'echo "Starting hostapd service..."\n',
                        'systemctl start hostapd.service\n',
                        'sleep 10\n',

                        '#Start dhcpcd. Again, a 5-second sleep\n',
                        'echo "Starting dhcpcd service..."\n',
                        'systemctl start dhcpcd.service\n',
                        'sleep 5\n',

                        'echo "Starting dnsmasq service..."\n',
                        'systemctl start dnsmasq.service\n',
                        'echo "wifistart DONE"\n']
startUpScript.writelines(startUpScriptToWrite)
startUpScript.close()
print("startup script created")

# edit /etc/rc.local
os.chdir('/etc')
pwd = os.getcwd()
pathToRcLocal = pwd + '/rc.local'
print("editing rc.local")
rcLocalOriginal = open(pathToRcLocal, "r+")
modifiedRcLocal = rcLocalOriginal.readlines()
modifiedRcLocal.insert(-1, "/bin/bash /usr/local/bin/wifistart\n")
rcLocalOriginal.seek(0)
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

os.system("sudo systemctl unmask hostapd && sudo systemctl enable hostapd")

# start custom script
os.system("sudo sh /usr/local/bin/wifistart")
