#Basic IP Failover script.
#A lot more work needs to be added, but its a start.

import socket
import time
from subprocess import PIPE, Popen
from threading import Thread
from time import gmtime, strftime

#Master/Slave
ACTIVE=False

#UDP Communication
UDP_IP = "192.168.88.51"
UDP_PORT = 5005

#Virtual IP
VIP="192.168.88.60"

#Failover Nodes
FN_ONE="192.168.88.50"

#Check
CHECK_DELAY=0.5
MISSED_PONG=1
TIME_OUT=5000

#TIMES
LAST_SEND=0
LAST_RECV=0

#ACTIVE NOTIFICATION
ACTIVE_NOTIFI=False

def cmdline(command):
    process = Popen(args=command,stdout=PIPE,shell=True,universal_newlines=True)
    return process.communicate()[0]
	
def udpcheck():
	print("UDP CHECK")
	global LAST_SEND
	while True:
		if (ACTIVE==False):
			udpsend(FN_ONE, "PING")
			LAST_SEND=int(time.time())
			time.sleep(float(CHECK_DELAY))
			
def viptimeout():
	global LAST_SEND
	global LAST_RECV
	global TIME_OUT
	global ACTIVE_NOTIFI
	time.sleep(2)
	while True:
		timeout=int(LAST_RECV)-int(LAST_SEND)
		if (1 <= TIME_OUT) and (timeout <= TIME_OUT):
			if (ACTIVE_NOTIFI==False):
				ACTIVE_NOTIFI=True
				print("VIP TAKE OVER!")
				setVIP()

def udpserver():
	print("Starting VIP UDP socket.")
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT))
	print("Bind UDP socket " + str(UDP_PORT))
	
	while True:
		data, addr = sock.recvfrom(1024)
		udpreceive(addr, data)
		
def udpsend(rip, msg):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.sendto(msg, (FN_ONE, UDP_PORT))

def udpreceive(addr, data):
	#Receive | Giveup, Ping, Pong
	if (data == "GIVE_UP"):
		print(data)
		cmdline("ifconfig eth0:0 down")
		ACTIVE_NOTIFI=False
	elif (data == "PING"):
		print(data)
		udpsend(addr, "PONG")
	elif (data == "PONG"):
		print(data)
		global LAST_RECV
		LAST_RECV=int(time.time())
	else:
		print("UNKNOWN:" + str(data))

def setVIP():
	print("Setting VIP")
	udpsend(FN_ONE, "GIVE_UP")
	cmdline("ifconfig eth0:0 " + str(VIP))
	

def main():
	print("Starting VIP")
	thread_udpserver = Thread(target=udpserver)
	thread_udpserver.daemon = True
	thread_udpserver.start()
	
	thread_udpcheck = Thread(target=udpcheck)
	thread_udpcheck.daemon = True
	thread_udpcheck.start()
	
	thread_viptimeout = Thread(target=viptimeout)
	thread_viptimeout.daemon = True
	thread_viptimeout.start()
	
	if (ACTIVE==True):
		setVIP()
	
	while True:
		continue

if __name__ == '__main__':
    main()