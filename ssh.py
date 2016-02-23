import paramiko
import pygame
import time
from time import gmtime, strftime
import sys
#Joystick
from pygame.locals import *
####################

hostname = '10.90.83.163' #10.112.103.252
port = 2200
username = 'pi' 
password = 'robotti'

pygame.init()
size = width, height = 320, 240
screen = pygame.display.set_mode(size)


##################################
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
########################################

def main():
    joystick_count = pygame.joystick.get_count()
    print ("There is ", joystick_count, "joystick/s")
    if joystick_count == 0:
        print ("Error, I did not find any joysticks")
    else:
        my_joystick = pygame.joystick.Joystick(0)
        my_joystick.init()
        kiinni = True

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)
        ssh_session = client.get_transport().open_session()
    except:
        print(strftime('[%H:%M:%S] ') + '[-] Can not connect. Retrying...')
        time.sleep(1)
        main()

    paramiko.util.log_to_file("filename.log")

    reconnect = True
    error = False
    stop = False
    timer = time.time()
    keys = [0,0,0,0]
    send = False
    debugging = False

    if ssh_session.active:
        print(strftime('[%H:%M:%S] ') + '[+] Connected to server!')
        print(strftime('[%H:%M:%S] ') + ssh_session.recv(1024)) #luetaan tervetuloaviesti palvelimelta
        while (stop == False):
            print keys[0]
            #print keys[1]
            #print keys[2]
            #print keys[3]
            if kiinni == True:
                h_axis_pos = my_joystick.get_axis(0)
                v_axis_pos = my_joystick.get_axis(1)
                print (h_axis_pos, v_axis_pos)
				

                if h_axis_pos <= -0.5 and keys[2] == 0:
					keys[2] = 1
					send = True
                elif keys[2] == 1 and h_axis_pos > -0.5:
                    keys[2] = 0
                    send = True
					
                if h_axis_pos >= 0.5 and keys[3] == 0:
					keys[3] = 1
					send = True
                elif keys[3] == 1 and h_axis_pos < 0.5:
                    keys[3] = 0
                    send = True
                
            if send == True:
			    print "ASDASDASDASDASDASDASDASASDASDASDASDASDASDASDASDASDASDASD"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stop = True
                    reconnect = False
                    break
                elif event.type == pygame.JOYAXISMOTION:
                    if event.axis == 2:
                        if my_joystick.get_axis(2) <= -0.5 and keys[0] == 0:
                            keys[0] = 1
                            send = True
                        elif my_joystick.get_axis(2) > -0.5 and keys[0] == 1:
                            keys[0] = 0
                            send = True
                        elif my_joystick.get_axis(2) >= 0.5 and keys[1] == 0:
                            keys[1] = 1
                            send = True
                        elif my_joystick.get_axis(2) < 0.5 and keys[1] == 1:
                            keys[1] = 0
                            send = True
							
                #elif event.type == pygame.JOYBUTTONDOWN:
                    #if event.button == 11:
                        #print "nollaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        keys[0] = 1
                        send = True
                    if event.key == pygame.K_s:
                        keys[1] = 1
                        send = True
                    if event.key == pygame.K_a:
                        keys[2] = 1
                        send = True
                    if event.key == pygame.K_d:
                        keys[3] = 1
                        send = True
                    if event.key == pygame.K_e: #e:ta painamalla asiakas lopettaa kaiken tiedonsiirron palvelimelle kunnes e:ta painetaan uudelleen
                        if debugging is False:
                            print(strftime('[%H:%M:%S] ') + '[+] Debug mode is ON! Not sending any keystrokes.')
                            debugging = True
                        else:
                            print(strftime('[%H:%M:%S] ') + '[+] Debug mode is OFF! Sending keystrokes.')
                            debugging = False
                    if event.key == pygame.K_ESCAPE:
                        stop = True
                        reconnect = False
                        break
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_w:
                        keys[0] = 0
                        send = True
                    if event.key == pygame.K_s:
                        keys[1] = 0
                        send = True
                    if event.key == pygame.K_a:
                        keys[2] = 0
                        send = True
                    if event.key == pygame.K_d:
                        keys[3] = 0
                        send = True
					    
            if (time.time() - timer) >= 0.25 or send is True: #lahetetaan vahintaan nelja kertaa sekunnissa nappainten tiedot, jotta yhteyden ollessa huono mikaan nappi ei jaa "pohjaan" palvelimen puolella
                if debugging is False:
                    try:
                        ssh_session.send(str(keys[0]) + str(keys[1]) + str(keys[2]) + str(keys[3]))
                    except:
                        stop = True
                        error = True
                        print (strftime('[%H:%M:%S] ') + '[-] Connection closed!')
                        break
                        pass
                    timer = time.time()
                    send = False

    if ssh_session.active is True and error is False:
        try:
            ssh_session.send('quit')
            ssh_session.close()
            client.close()
        except Exception as e:
            print(str(e))
        
    if reconnect is True:
        print(strftime('[%H:%M:%S] ') + '[+] Trying to reconnect!')
        main()

    pygame.quit()
    sys.exit(0)

main()
