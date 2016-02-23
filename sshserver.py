###############
import RPi.GPIO as gpio
import time
from time import gmtime, strftime
import metroGPIO as io
import os
import select
###############
import paramiko
import getopt
import threading
from threading import Timer
import sys
import socket
###############
import subprocess
###############
io.initMetroPins()
gpio.output(io.OUT1, True)	#enable motor 1
gpio.output(io.OUT3, True)	#enable motor 2

p = gpio.PWM(io.OUT1,100)
p2 = gpio.PWM(io.OUT3,100)

p.start(100)
p2.start(100)

gpio.output(io.OUT7, False)
gpio.output(io.OUT8, False)
gpio.output(io.OUT5, False)
gpio.output(io.OUT6, False)

'''servo'''
gpio.output(io.OUT2, False) #?
gpio.output(io.OUT4, False)
servopwm = gpio.PWM(io.OUT4, 100)
servopwm.ChangeFrequency(60)
servopwm.start(0)
'''servo'''


host_key = paramiko.RSAKey(filename='test_rsa.key')

firstTime = True

keys = [0,0,0,0,0,0,0]

class ConnectionInfo:
	server = '10.112.214.116' #10.90.83.163   10.112.103.252   100.101.194.15  85.76.139.202 10.112.219.16   192.168.43.33
	ssh_port = 2200
	username = 'pi'
	password = 'robotti'

class Server(paramiko.ServerInterface):
    sock = 0
    def __init__(self):
        self.event = threading.Event()
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    def check_auth_password(self, username, password):
        if (username == ConnectionInfo.username) and (password == ConnectionInfo.password):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED
    
class Client:
    chan = 0
    client = 0

class timers:
    timer1 = 0
    timer2 = 0
    timer3 = 0

class connectionInfo:
    timer = 0
    stop = False
    checks = 0

def checkConnection():
    if (time.time() - connectionInfo.timer) >= 5.0:
        print(strftime('[%H:%M:%S] ') + '[-] Client timed out!')
        stop()
        Client.Session.close()
        Client.client.close()
    else:
        connectionInfo.checks += 1
        timers.timer3 = Timer(1, checkConnection, ())
        timers.timer3.start()

        if connectionInfo.checks == 5 and (time.time() - connectionInfo.timer) <= 1.0:
            print(strftime('[%H:%M:%S] ') + '[+] Connection OK.')
            connectionInfo.checks = 0

        if (time.time() - connectionInfo.timer) >= 1.0: #asiakkaalta ei ole saapunut dataa yli sekuntiin
            print(strftime('[%H:%M:%S] ') + '[-] Client is idle! Shutting down motors.')
            stop()
            keys[0] = 0
            keys[1] = 0
            keys[2] = 0
            keys[3] = 0
            keys[4] = 0
            keys[5] = 0
            keys[6] = 0


def main():
    # creating a socket object
    stop = False
    try:
        Server.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Server.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        Server.sock.bind((ConnectionInfo.server, ConnectionInfo.ssh_port))
        Server.sock.listen(100)
        print (strftime('[%H:%M:%S] ') + '[+] Listening for connection...')
        Client.client, addr = Server.sock.accept()
    except Exception as e:
        print (strftime('[%H:%M:%S] ') + '[-] Connection failed: ') + str(e)
        sys.exit(1)

    print(strftime('[%H:%M:%S] ') + '[+] Client connected!')

    # creating a paramiko object
    try:
        Client.Session = paramiko.Transport(Client.client)
        Client.Session.add_server_key(host_key)
        paramiko.util.log_to_file("filename.log")
        server = Server()
        try:
            Client.Session.start_server(server=server)
        except paramiko.SSHException as x:
            print (strftime('[%H:%M:%S] ') + '[-] SSH negotiation failed.')

        
        Client.chan = Client.Session.accept(10)
        
        if Client.chan is None:
            print(strftime('[%H:%M:%S] ') + '[-] No channel.')
            quit()

        print (strftime('[%H:%M:%S] ') + '[+] Authenticated!')

        Client.chan.send('Tervetuloa ohjaamaan robottia! Robottia ohjataan WASD-nappaimista.')

        timers.timer2 = time.time()
        timers.timer3 = Timer(1, checkConnection, ())
        timers.timer3.start()
        connectionInfo.timer = time.time()

        while (1):
            if (buttons() == 0 and connectionInfo.stop == False):
                print(strftime('[%H:%M:%S] ') + '[-] Client disconnected!')
                break

    except Exception as e:
        print (strftime('[%H:%M:%S] ') + '[-] Caught exception: ') + str(e)
        try:
            print()
        except:
            pass
    quit()


def quit(force = False):
    print(strftime('[%H:%M:%S] ') + '[-] Closing all connections!')
    timers.timer3.cancel()
    if Client.Session.active is True:
        Client.Session.close()
        Client.client.close()
    #gpio.cleanup()
    #p.stop()
    #p2.stop()
    if force is False:
        main()
    print(strftime('[%H:%M:%S] ') + '[-] Shutting down!')
    sys.exit(0)

def buttons():
    try:
        keyPress = Client.chan.recv(7) #vastaanotetaan seitseman kirjainta asiakkaalta
    except KeyboardInterrupt:
        print(strftime('[%H:%M:%S] ') + '[-] Ctrl-C pressed!')
        quit(True)

    if Client.Session.active is False:
        return 0

    connectionInfo.timer = time.time()

    if keyPress[0] is 'q': #asiakas painoi ESC:ia tai sulki ohjelmansa: suljetaan yhteys!
        stop()
        print(strftime('[%H:%M:%S] ') + '[-] Client closed the program!')
        return 0

    if keyPress[0] is '1':
        keys[0] = 1
        timers.timer1 = time.time()
        #print('[+] Client is holding W.')
    if keyPress[0] is '0':
        keys[0] = 0
        timers.timer1 = time.time()
        #print('[+] Client is not holding W.')

    if keyPress[1] is '1':
        keys[1] = 1
        timers.timer1 = time.time()
        #print('[+] Client is holding S.')
    if keyPress[1] is '0':
        keys[1] = 0
        timers.timer1 = time.time()
        #print('[+] Client is not holding S.')

    if keyPress[2] is '1':
        keys[2] = 1
        timers.timer1 = time.time()
        #print('[+] Client is holding A.')
    if keyPress[2] is '0':
        keys[2] = 0
        timers.timer1 = time.time()
        #print('[+] Client is not holding A.')

    if keyPress[3] is '1':
        keys[3] = 1
        timers.timer1 = time.time()
        #print('[+] Client is holding D.')
    if keyPress[3] is '0':
        keys[3] = 0
        timers.timer1 = time.time()
        #print('[+] Client is not holding D.')

    if keyPress[4] is '1':
        keys[4] = 1
        timers.timer1 = time.time()
    if keyPress[4] is '0':
        keys[4] = 0
        timers.timer1 = time.time()
    if keyPress[5] is '1':
        keys[5] = 1
        timers.timer1 = time.time()
    if keyPress[5] is '0':
        keys[5] = 0
        timers.timer1 = time.time()

    if keyPress[6] is '1':
        keys[6] = 1
        timers.timer1 = time.time()
    if keyPress[6] is '0':
        keys[6] = 0
        timers.timer1 = time.time()

    if keys[4] == 1 and servo.angle > 0:
        update(1)
    elif keys[5] == 1 and servo.angle < 125:
        update(0)
    else:
        servopwm.ChangeDutyCycle(0)
        gpio.output(io.OUT4, False)

    if keys[6] == 1:
        print("soi")
        subprocess.Popen(["aplay", "sireeni.wav"])

    if keys[0] == 1 and keys[2] == 1:
        eteenjavasemmalle()
    elif keys[0] == 1 and keys[3] == 1:
        eteenjaoikealle()
    elif keys[1] == 1 and keys[2] == 1:
        taaksejavasemmalle()
    elif keys[1] == 1 and keys[3] == 1:
        taaksejaoikealle()
    elif keys[0] == 1:
        eteenpain()
    elif keys[1] == 1:
        taaksepain()
    elif keys[0] == 0 and keys[1] == 0: #W ja S ovat ylhaalla
        stop()

    return 1 #jatketaan normaalisti!

class servo:
    angle = 0

def update(suunta):
    print ('Suunta: ', suunta, ' angle: ', servo.angle)
    if suunta == 1:
        servo.angle -= 25
    elif suunta == 0:
        servo.angle += 25
    if servo.angle < 0:
        servo.angle = 0
    if servo.angle > 125:
        servo.angle = 125
    duty = float(servo.angle) / 10.0 + 2.5
    gpio.output(io.OUT4, True)
    servopwm.ChangeDutyCycle(duty)

def eteenpain():
    gpio.output(io.OUT7, True)
    gpio.output(io.OUT8, False)
    gpio.output(io.OUT5, False)
    gpio.output(io.OUT6, True)
    for dc2 in range(5, 100, +5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p.ChangeDutyCycle(dc2)
        p2.ChangeDutyCycle(dc2)
        time.sleep(0.0005) #0.0005

def taaksepain():
    gpio.output(io.OUT7, False)
    gpio.output(io.OUT8, True)
    gpio.output(io.OUT5, True)
    gpio.output(io.OUT6, False)
    for dc2 in range(5, 100, +5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p.ChangeDutyCycle(dc2)
        p2.ChangeDutyCycle(dc2)
        time.sleep(0.0005)

def stop():
    gpio.output(io.OUT7, False)
    gpio.output(io.OUT8, False)
    gpio.output(io.OUT5, False)
    gpio.output(io.OUT6, False)
    p.ChangeDutyCycle(0)
    p2.ChangeDutyCycle(0)

def eteenjavasemmalle():
    gpio.output(io.OUT7, True)
    gpio.output(io.OUT8, False)
    gpio.output(io.OUT5, False)
    gpio.output(io.OUT6, True)
    for dc in range(100, 5, -5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p.ChangeDutyCycle(dc)
        time.sleep(0.0005)
    for dc in range(5, 100, +5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p2.ChangeDutyCycle(dc)
        time.sleep(0.0005)

def eteenjaoikealle():
    gpio.output(io.OUT7, True)
    gpio.output(io.OUT8, False)
    gpio.output(io.OUT5, False)
    gpio.output(io.OUT6, True)
    for dc in range(100, 5, -5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p2.ChangeDutyCycle(dc)
        time.sleep(0.0005)
    for dc in range(5, 100, +5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p.ChangeDutyCycle(dc)
        time.sleep(0.0005)

def taaksejavasemmalle():
    gpio.output(io.OUT7, False)
    gpio.output(io.OUT8, True)
    gpio.output(io.OUT5, True)
    gpio.output(io.OUT6, False)
    for dc in range(100, 5, -5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p.ChangeDutyCycle(dc)
        time.sleep(0.0005)
    for dc in range(5, 100, +5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p2.ChangeDutyCycle(dc)
        time.sleep(0.0005)

def taaksejaoikealle():
    gpio.output(io.OUT7, False)
    gpio.output(io.OUT8, True)
    gpio.output(io.OUT5, True)
    gpio.output(io.OUT6, False)
    for dc in range(100, 5, -5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p2.ChangeDutyCycle(dc)
        time.sleep(0.0005)
    for dc in range(5, 100, +5):       # a,b,c  a = alotus b=lopetus c = vahennys
        p.ChangeDutyCycle(dc)
        time.sleep(0.0005)

if __name__ == '__main__':
    main()

