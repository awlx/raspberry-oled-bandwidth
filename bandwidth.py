#
# Inspired by https://github.com/DarrenBeck/rpi-oled-bandwidth and https://photochirp.com/r-pi/use-raspberry-pi-oled-bandwidth-monitor/
#
# Maintained by awlnx - aw@awlnx.space
#

import subprocess
import time
import re
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Adjust to your needs
wifi = 'wlan0'
vpn = 'fastd-welt'
batman = 'bat-welt'
primary_mac = 'dc:a6:32:00:6b:59'
snmp_secret = 'secret'

# We assume 100mbit/s max bandwidth
maxRateIn = 10000000
maxRateOut = 10000000
PImaxRateIn = 100000000
PImaxRateOut = 100000000

### DO NOT EDIT BELOW THIS POINT ###

# Trying to find ifIndex of interface
try:
    ifIndexData = subprocess.check_output("snmpwalk -v2c -c " + snmp_secret + " 127.0.0.1 1.3.6.1.2.1.31.1.1.1", shell=True)

    for ifIndex in ifIndexData.decode('UTF-8').split('\n'):
        if wifi in ifIndex:
            wifiIndex = re.search('[0-9]+$',ifIndex.split()[0]).group(0)
        elif vpn in ifIndex:
            vpnIndex = re.search('[0-9]+$',ifIndex.split()[0]).group(0)
except subprocess.CalledProcessError as e:
    print("Getting interfaces failed " + e)
    raise SystemExit

# Raspberry Pi pin configuration:
RST = 24

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 12)
fontsmall = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 10)
fontverysmall = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 8)
fontmedium = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 12)

#Display Image
disp.image(image)
disp.display()

#OIDs to poll
oidInWan = 'IF-MIB::ifInOctets.' + vpnIndex
oidOutWan = 'IF-MIB::ifOutOctets.' + vpnIndex
oidInPI = 'IF-MIB::ifInOctets.' + wifiIndex
oidOutPI = 'IF-MIB::ifOutOctets.' + wifiIndex



#functions
def getSnmpData (oid):

    try:
        data = subprocess.check_output("snmpget -v2c -c " + snmp_secret + " 127.0.0.1 " + oid, shell = True)
    except subprocess.CalledProcessError as e:
        data = e
    else:
        data = "unhandled error"
    return data;

def getSnmpInt (oid):

    try:
        data = subprocess.check_output("snmpget -v2c -c " + snmp_secret + " 127.0.0.1 " + oid, shell = True)
        data = data.split()
        data = data.pop()
    except:
        data = "0"
    return int(data)

def getSnmpPIData (PIoid):

        try:
                PIdata = subprocess.check_output("snmpget -v2c -c " + snmp_secret + " 127.0.0.1 " + PIoid, shell = True)
        except subprocess.CalledProcessError as f:
                PIdata = f
        else:
                PIdata = "unhandled error"
        return PIdata;

def getSnmpPIInt (PIoid):

        try:
                PIdata = subprocess.check_output("snmpget -v2c -c " + snmp_secret + " 127.0.0.1 " + PIoid, shell = True)
                PIdata = PIdata.split()
                PIdata = PIdata.pop()
        except:
                PIdata = "0"
        return int(PIdata)

def drawBar (x, barHeight):
    # parameters are x, y, end x, end y
    # draw.rectangle ((x, height - barHeight, x + 10, height -1), outline=255, fill=255)
    draw.rectangle ((x, 32 - barHeight, x + 10, height - 32), outline=255, fill=255)

def drawBarLOW (x, barLOWHeight):
        # parameters are x, y, end x, end y
        draw.rectangle ((x, 32 + barLOWHeight, x + 10, height - 32), outline=255, fill=255)

def textRate (rate):
    rate = rate * 8 / 1000
    if rate < 1000:
        result = str(round(rate,1)) + 'kb/s'
    else:
        result = str(round(rate/1000,1)) + 'mb/s'
    return result


lastInBytes = getSnmpInt (oidInWan);
lastOutBytes = getSnmpInt (oidOutWan);
lastPIInBytes = getSnmpPIInt (oidInPI);
lastPIOutBytes = getSnmpPIInt (oidOutPI);
lastTime = time.time()

#timed array vars
timerTime = time.time()
highestSpeedIn = 0
highestSpeedOut = 0
PIhighestSpeedIn = 0
PIhighestSpeedOut = 0
speedArrayIn = []
speedArrayOut = []
PIspeedArrayIn = []
PIspeedArrayOut = []
inMax = 0
outMax = 0
PIinMax = 0
PIoutMax = 0

while (1):
    time.sleep(2)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    now = time.time()
    elapsed = now - lastTime
    lastTime = now

    #calculate rates in and out
    inBytes = getSnmpInt (oidInWan)
    currInBytes = (inBytes - lastInBytes) / elapsed
    lastInBytes = inBytes

    outBytes = getSnmpInt (oidOutWan)
    currOutBytes = (outBytes - lastOutBytes) / elapsed
    lastOutBytes = outBytes

    PIinBytes = getSnmpPIInt (oidInPI)
    currPIInBytes = (PIinBytes - lastPIInBytes) / elapsed
    lastPIInBytes = PIinBytes

    PIoutBytes = getSnmpPIInt (oidOutPI)
    currPIOutBytes = (PIoutBytes - lastPIOutBytes) / elapsed
    lastPIOutBytes = PIoutBytes


    # currPIinBytes = 'dog '
    #max rate last 24 hours calculations

    if currInBytes > highestSpeedIn:
        highestSpeedIn = currInBytes
    if currOutBytes > highestSpeedOut:
        highestSpeedOut = currOutBytes
    if currPIInBytes > PIhighestSpeedIn:
        PIhighestSpeedIn = currPIInBytes
    if currPIOutBytes > PIhighestSpeedOut:
        PIhighestSpeedOut = currPIOutBytes

    if now > timerTime + 3600:
        print('-----------------------------------------------------------------  time expired')
        timerTime = now

        speedArrayIn.append (highestSpeedIn)
        if len (speedArrayIn) > 23:
            del speedArrayIn[0]
        inMax = max(speedArrayIn)

        speedArrayOut.append (highestSpeedOut)
        if len (speedArrayOut) > 23:
            del speedArrayOut[0]
        outMax = max(speedArrayOut)

        highestSpeedIn = 0
        highestSpeedOut = 0

        PIspeedArrayIn.append (PIhighestSpeedIn)
        if len (PIspeedArrayIn) > 23:
            del PIspeedArrayIn[0]
        PIinMax = max(PIspeedArrayIn)

        PIspeedArrayOut.append (PIhighestSpeedOut)
        if len (PIspeedArrayOut) > 23:
            del PIspeedArrayOut[0]
        PIoutMax = max(PIspeedArrayOut)

        PIhighestSpeedIn = 0
        PIhighestSpeedOut = 0

    #adjust these in each loop in case we find a faster speed
    inMax = max(inMax, highestSpeedIn)
    outMax = max(outMax, highestSpeedOut)
    PIinMax = max(PIinMax, PIhighestSpeedIn)
    PIoutMax = max(PIoutMax, PIhighestSpeedOut)

    #draw graph
    inHeight = 0.0
    outHeight = 0.0
    PIinHeight = 0.0
    PIoutHeight = 0.0

    if currInBytes > 0:
        inHeight = float(currInBytes / maxRateIn) * 32  #was maxRateIn

    if currOutBytes > 0:
        outHeight = float(currOutBytes / maxRateOut) * 32

    if currPIInBytes > 0:
        PIinHeight = float(currPIInBytes / PImaxRateIn) * 32

    if currPIOutBytes > 0:
        PIoutHeight = float(currPIOutBytes / PImaxRateOut) * 32

    drawBar (0, inHeight)
    drawBar (12, PIinHeight)
    drawBarLOW (0, outHeight)
    drawBarLOW (12, PIoutHeight)
    #write rates
    draw.text((31,38), textRate(currInBytes), font=font, fill=255)
    draw.text((31,50), textRate(currOutBytes), font=font, fill=255)

    draw.text((85,38), textRate(currPIInBytes), font=font, fill=255)
    draw.text((85,50), textRate(currPIOutBytes), font=font, fill=255)

    # Batman Clients
    clients = subprocess.check_output("batctl -m " + batman + " tl | egrep -v '(MainIF|" + primary_mac + ")' | egrep -o '([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})' | wc -l", shell=True).split().pop()
    draw.text((0,48), "Clients", font=fontverysmall, fill=255)
    draw.text((12,55), clients.decode("utf-8"), font=fontverysmall, fill=255)

    #max rates
    draw.text((36,0), "VPN", font=fontsmall, fill=255)
    draw.text((31,10), textRate(inMax), font=fontsmall, fill=255)
    draw.text((31,20), textRate(outMax), font=fontsmall, fill=255)

    draw.text((90,0), "Wifi", font=fontsmall, fill=255)
    draw.text((85,10), textRate(PIinMax), font=fontsmall, fill=255)
    draw.text((85,20), textRate(PIoutMax), font=fontsmall, fill=255)

    disp.image(image)
    disp.display()

