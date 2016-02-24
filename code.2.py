from json import json
from datetime import datetime
from datetime import timedelta
from datetime import date
from collections import deque
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)  #GPIO pin setup, this is test code and must be rewritten with the raspberry
StepPins = [2,3,4,14,15] #2 = Enable, 3 = DIR, 4 = MS1, 14 = MS2, 15 = Step, this is for disk motor only other motors will have other pin names and declerations
for pin in StepPins:
    GPIO.setup(pin,GPIO.OUT)
    GPIO.output(pin, False)
Seq = [[0,1,0,0,0],      #used to move forwards a step
       [0,1,0,0,1]]
ISeq = [[0,0,0,0,0],     #used to move backwards a step
        [0,0,0,0,1]]
Seq8th = [[0,1,1,1,0],   #used to move forwards in 1/8 step
          [0,1,1,1,1]]
ISeq8th = [[0,0,1,1,0],  #used to move backwards in 1/8 step
           [0,0,1,1,1]]
RisePins = [17,27,22,23,24] #17 = Enable, 27 = DIR, 22 = MS1, 23 = MS2, 24 = Step, this is for up/down probe control
for rpin in RisePins:   #Will be using Seq and ISeq for control, since this is up/down, similar to forward/backward movement
    GPIO.setup(rpin,GPIO.OUT)
    GPIO.output(rpin, False)
LenPins = [10,9,11,25,8] # 10 = Enable, 9 = DIR, 11 = MS1, 25 = MS2, 8 = Step, this is for forward/backward probe control
for lpin in LenPins:    #Will be using Seq and ISeq for control, exact step control can be defined in function
    GPIO.setup(lpin,GPIO.OUT)#have to be explicit in forward/backward since it has 33.33 steps per location may have to define 1/8th step control
    GPIO.output(lpin, False)
RotPins = [5,6,13,19,26] # 5 = Enable, 6 = DIR, 13 = MS1, 19 = MS2, 26 = Step, this is for rotational movement of the probe
for cpin in RotPins:    #Will be usign Seq and ISeq for control, exact step control can be defined in function
    GPIO.setup(cpin,GPIO.OUT)
    GPIO.output(cpin, False)
GPIO.setup(18,GPIO.IN) #will be used for pill infrared sensor, hopefully it's a digital sensor that can be adjusted
probesensor = GPIO.input(18) #will be used to refer to the input

pillarr = [[None for i in range(13)]for i in range(8)] #creating the global arrays
user1 = [None for i in range(4)]
user2 = [None for i in range(4)]
user3 = [None for i in range(4)]
user4 = [None for i in range(4)]
user5 = [None for i in range(4)]
pilluser1 = [[None for i in range(13)]for i in range(219)]
pilluser2 = [[None for i in range(13)]for i in range(219)]
pilluser3 = [[None for i in range(13)]for i in range(219)]
pilluser4 = [[None for i in range(13)]for i in range(219)]
pilluser5 = [[None for i in range(13)]for i in range(219)]
for amnt in range(len(pillarr[0])):     #creates the first list with the numbers 0 - 13 for the columns
    pillarr[0][amnt] = amnt
    pilluser1[0][amnt] = amnt
    pilluser2[0][amnt] = amnt
    pilluser3[0][amnt] = amnt
    pilluser4[0][amnt] = amnt
    pilluser5[0][amnt] = amnt
for amnt in range(len(pillarr[0])):     #setting up the probe location information, will initiate to none, and be overwritten when the information is recalled
    pillarr[3][amnt] = None
for amnt in range(len(pillarr[0])):     #setting up the pill slot location, this will basically be as before, where the index or pillarr[0] would have the same slot location, but had to change due to slot 13 (index 12) since it's empty 
    pillarr[4][amnt] = amnt
pillarr[4][12] = 13                     #this forces the last pill to be put into the last slot, skipping the previous slot since that will be empty to deposit pills into the bottom disk
        
pillqueue = deque()  #setting up the pillqueue as a list format, allows for 2D array manipulation with .append command #CHANGED TO DEQUE FOR TIME EFFICIENCY,KEEPING SAME MANIPULATION,JUST QUICKER
lowdiscurrpos = 0   #keep track of low disk pill container facing the probe
updiscurrpos = 0    #keep track of high disk pill container facing the probe
lowdisstndpos = 0   #keep a standard position location that the low disk will move back to when done dispensing
updisstndpos = 7    #keep a standard position location that the high disk will move back to when done dispensing
probelevel = 0  # 0 for down, 1 for up
proberotstnd = 0 # out of possible 21, will be used to return probe to smallest pill drop facing upwards
probecurrpos = 0 # the current position of the probe, can be treated as a 2D array with rotation being rows and drops and columns
lenpos = [None, None] #length position that will be used to attempt to retrieve a single pill from the storage, set as steps and 8th steps



retrieveinf = open('pillarrinfo', 'r') #loading any saved info into the arrays
pillarr = json.load(retrieveinf)        #done here to avoid possible overwriting
retrieveinf.close()                     #can be moved into a function, but must
retrieveinf = open('user1info', 'r')   #make sure function is run first
user1 = json.load(rerieveinf)
retrieveinf.close()
retrieveinf = open('user2info', 'r')
user2 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('user3info', 'r')
user3 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('user4info', 'r')
user4 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('user5info', 'r')
user5 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('pilluser1info', 'r')
pilluser1 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('pilluser2info', 'r')
pilluser2 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('pilluser3info', 'r')
pilluser3 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('pilluser4info', 'r')
pilluser4 = json.load(retrieveinf)
retrieveinf.close()
retrieveinf = open('pilluser5info', 'r')
pilluser5 = json.load(retrieveinf)
retrieveinf.close()
retrieveing = open('pillqueueinfo', 'r')
pillqueue = json.load(retrieveinf)
retrieveinf.close()

def search(pillarr, user1, user2, user3, user4, user5, pilluser1, pilluser2, pilluser3, pilluser4, pilluser5): #pass the actual arrays so that they can be read
    for searchlen in range(5):          #created to loop 5 times for 5 possible users
        if(seachlen == 0):               #each loop it will set the temp variable to one of the users
            tempuser = user1            #and the use the temp value to search through the schedule
            temppilluser = pilluser1    #allowing for shorter code as only on search loop is needed
        elif(searchlen == 1):            #which will repeat 5 times for the different users
            tempuser = user2            
            temppilluser = pilluser2
        elif(searchlen == 2):
            tempuser = user3
            temppilluser = pilluser3
        elif(searchlen == 3):
            tempuser = user4
            temppilluser = pilluser4
        elif(searchlen == 4):
            tempuser = user5
            temppilluser = pilluser5

        if(date.today().weekday() == 0): # Checks for the day, Monday, before reading from the pill array, allows the system to be more efficient, and split the days into blocks
            for col in range(len(temppilluser[0])):
                for row in range(3,32,3):
                    if (datetime.now() - datetime.timedelta(minutes=3) <= temppilluser[row][col] <= datetime.now() + datetime.timedelta(minutes=3) and (temppilluser[row+2][col] != True or temppilluser[row+2][col] != "waiting")):#checks time and if dispensed or if waiting in queue
                        tempqueue = [tempuser[0],pillarr[4][col],pillarr[1][col],pillarr[3][col],temppilluser[row+1][col],row+2] #gathering all the information necessary for the queue system, (username, pill location, pill name, probe position,user amount,dispense index number)
                        global pillqueue
                        pillqueue.append(tempqueue)
                        temppilluser[row+2][col] = "waiting"
        elif(date.today().weekday() == 1):#Tuesday
            for col in range(len(temppilluser[0])):
                for row in range(34,63,3):
                    if (datetime.now() - datetime.timedelta(minutes=3) <= temppilluser[row][col] <= datetime.now() + datetime.timedelta(minutes=3) and (temppilluser[row+2][col] != True or temppilluser[row+2][col] != "waiting")):
                        tempqueue = [tempuser[0],pillarr[4][col],pillarr[1][col],pillarr[3][col],temppilluser[row+1][col],row+2]
                        global pillqueue
                        pillqueue.append(tempqueue)
                        temppilluser[row+2][col] = "waiting"
        elif(date.today().weekday() == 2):#Wednesday
            for col in range(len(temppilluser[0])):
                for row in range(65,94,3):
                    if (datetime.now() - datetime.timedelta(minutes=3) <= temppilluser[row][col] <= datetime.now() + datetime.timedelta(minutes=3) and (temppilluser[row+2][col] != True or temppilluser[row+2][col] != "waiting")):
                        tempqueue = [tempuser[0],pillarr[4][col],pillarr[1][col],pillarr[3][col],temppilluser[row+1][col],row+2]
                        global pillqueue
                        pillqueue.append(tempqueue)
                        temppilluser[row+2][col] = "waiting"
        elif(date.today().weekday() == 3):#Thursday
            for col in range(len(temppilluser[0])):
                for row in range(96,125,3):
                    if (datetime.now() - datetime.timedelta(minutes=3) <= temppilluser[row][col] <= datetime.now() + datetime.timedelta(minutes=3) and (temppilluser[row+2][col] != True or temppilluser[row+2][col] != "waiting")):
                        tempqueue = [tempuser[0],pillarr[4][col],pillarr[1][col],pillarr[3][col],temppilluser[row+1][col],row+2]
                        global pillqueue
                        pillqueue.append(tempqueue)
                        temppilluser[row+2][col] = "waiting"
        elif(date.today().weekday() == 4):#Friday
            for col in range(len(temppilluser[0])):
                for row in range(127,156,3):
                    if (datetime.now() - datetime.timedelta(minutes=3) <= temppilluser[row][col] <= datetime.now() + datetime.timedelta(minutes=3) and (temppilluser[row+2][col] != True or temppilluser[row+2][col] != "waiting")):
                        tempqueue = [tempuser[0],pillarr[4][col],pillarr[1][col],pillarr[3][col],temppilluser[row+1][col],row+2]
                        global pillqueue
                        pillqueue.append(tempqueue)
                        temppilluser[row+2][col] = "waiting"
        elif(date.today().weekday() == 5):#Saturday
            for col in range(len(temppilluser[0])):
                for row in range(158,187,3):
                    if (datetime.now() - datetime.timedelta(minutes=3) <= temppilluser[row][col] <= datetime.now() + datetime.timedelta(minutes=3) and (temppilluser[row+2][col] != True or temppilluser[row+2][col] != "waiting")):
                        tempqueue = [tempuser[0],pillarr[4][col],pillarr[1][col],pillarr[3][col],temppilluser[row+1][col],row+2]
                        global pillqueue
                        pillqueue.append(tempqueue)
                        temppilluser[row+2][col] = "waiting"
        elif(date.today().weekday() == 6):#Sunday
            for col in range(len(temppilluser[0])):
                for row in range(189,218,3):
                    if (datetime.now() - datetime.timedelta(minutes=3) <= temppilluser[row][col] <= datetime.now() + datetime.timedelta(minutes=3) and (temppilluser[row+2][col] != True or temppilluser[row+2][col] != "waiting")):
                        tempqueue = [tempuser[0],pillarr[4][col],pillarr[1][col],pillarr[3][col],temppilluser[row+1][col],row+2]
                        global pillqueue
                        pillqueue.append(tempqueue)
                        temppilluser[row+2][col] = "waiting"
                        
        if(searchlen == 0): # using this to update the pilluser information, to put the dispensed information into the user schedule
            global pilluser1
            pilluser1 = temppilluser
        elif(searchlen == 1):
            global pilluser2
            pilluser2 = temppilluser
        elif(searchlen == 2):
            global pilluser3
            pilluser3 = temppilluser
        elif(searchlen == 3):
            global pilluser4
            pilluser4 = temppilluser
        elif(searchlen == 4):
            global pilluser5
            pilluser5 = temppilluser

    Userschedulebackup() #hardbackup of the user schedule
    Queuebackup(pillqueue)#hardbackup of the pillqueue


def Motorcontroldisk(pillqueue, lowdiscurrpos, updiscurrpos): #only part of the motor control system     #need to learn gpio control in order to
    if(pillqueue[0][1] <= 6):                                                                #send signals, probably a second loop for that
        lowdisnewpos = pillqueue[0][1]                                                 #so far this gives the the position difference
        lowdisdelta = abs(lowdisnewpos - lowdiscurrpos)                                   #between where it is and where it needs to be
        for amntstep in range(28*lowdisdelta):              #not even sure this works, I need to actually play with the thing, but that is not possible at the moment
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq[0][xpin])
                GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)                      #time delay for the chip to read and process correctly
        for amntstep in range(4*lowdisdelta):   #fixing the .571 to approximate .5, for every 28 steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq8th[0][xpin])
                GPIO.output(xpin, Seq8th[1][xpin])
            time.sleep(.01)
    elif(pillqueue[0][1] >=7):
        updisnewpos = pillqueue[0][1]
        updisdelta = abs(updisnewpos - updiscurrpos)
        for amntstep in range(28*updisdelta):
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq[0][xpin])
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*updisdelta):
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq8th[0][xpin])
                GPIO.output(xpin, ISeq8th[1][xpin])
            time.sleep(.01)
    return(lowdisnewpos,updisnewpos)        #this returns a tuple, to be unpacked into two seperate variables, lowdiscurrpos and updiscurrpos, respectively, CAN CHANGE TO AFFECT GLOBAL VARIABLES AND NO NEED TO RETURN

def Motorcontroldiskreturn(lowdiscurrpos, updiscurrpos): #returns disk to the home position
    if(lowdiscurrpos != 0): #checks the bottom disk to makes sure it's at home
        if(lowdiscurrpos == 1): #assigning values based on how far away from home position
            lowdisdelta = 6
        elif(lowdiscurrpos == 2):
            lowdisdelta = 5
        elif(lowdiscurrpos == 3):
            lowdisdelta = 4
        elif(lowdiscurrpos == 4):
            lowdisdelta = 3
        elif(lowdiscurrpos == 5):
            lowdisdelta = 2
        elif(lowdiscurrpos == 6):
            lowdisdelta = 1
        for amntstep in range(28*lowdisdelta): #moving the 28 full steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq[0][xpin])
                GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*lowdisdelta): #approximate the movement of 0.571 for every 28 steps, rounded to .5
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq8th[0][xpin])
                GPIO.output(xpin, Seq8th[1][xpin])
            time.sleep(.01)
        global lowdiscurrpos #setting the lower disk value position to 0, after it has finished moving to position 0
        lowdiscurrpos = 0
    if(updiscurrpos != 7): #checks the top disk current position to make sure it's at home
        if(updiscurrpos == 8): #assigning values based on how far away from home position
            updisdelta = 6
        elif(updiscurrpos == 9):
            updisdelta = 5
        elif(updiscurrpos == 10):
            updisdelta = 4
        elif(updiscurrpos == 11):
            updisdelta = 3
        elif(updiscurrpos == 12):
            updisdelta = 2
        elif(updiscurrpos == 13):
            updisdelta = 1
        for amntstep in range(28*updisdelta): #moving the 28 full steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq[0][xpin])
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*updisdelta): #moving .5 to approximate .571 for every 28 steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq8th[0][xpin])
                GPIO.output(xpin, ISeq8th[1][xpin])
            time.sleep(.01)
        global updiscurrpos #setting the up disk value position to 7, after it has finished moving to position 7
        updiscurrpos = 7

def Motorcontrolprobelength(lenpos): #extends the probe in order to collect a pill, LENPOS IS BASICALLY PROBE POSITION FROM PILLARR, IT'S USED LATER, MAKE SURE TO COLLECT THE PROBE POSITION INFORMATION SO THAT IT DOESN'T CONFLICT!!!!!!
    if(lenpos[0] == 0):
        # This will need to be re-written to either have sensors, or the code will have to be able to move from any position to another
    for amntstep in range(lenpos[0]):
        for pin in range(5):
            xpin = LenPins[pin]
            GPIO.output(xpin, Seq[0][xpin])
            GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)
    for amntstep in range(lenpos[1]):
        for pin in range(5):
            xpin = LenPins[pin]
            GPIO.output(xpin, Seq8th[0][xpin])
            GPIO.output(xpin, Seq8th[1][xpin])
            time.sleep(.01)
    time.sleep(.02) #holds the probe out for 20ms before allowing movement again, will adjust as necessary in order to control pill dropping into probe
        

def Motorcontrolprobelengthretract(lenpos): #Similar to Motorcontrolprobelength, but to retract the probe instead of extend
    if(lenpos[0] == 0):
        # This will need to be re-written to either have sensors, or the code will have to be able to move from any position to another
    for amntstep in range(lenpos[0]):
        for pin in range(5):
            xpin = LenPins[pin]
            GPIO.output(xpin, ISeq[0][xpin])
            GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
    for amntstep in range(lenpos[1]):
        for pin in range(5):
            xpin = LenPins[pin]
            GPIO.output(xpin, ISeq8th[0][xpin])
            GPIO.output(xpin, ISeq8th[1][xpin])
            time.sleep(.01)

def Motorcontrolprobedrop(): #final part in order to drop the pill and move to "home" face position
    for amntstep in range(100): #rotates to drop the pill
        for pin in range(5):
            xpin = RotPins[pin]
            GPIO.output(xpin, Seq[0][xpin])
            GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)
    time.sleep(.1)
    for amntstep in range(100): #rotates to return the hole to face up
        for pin in range(5):
            xpin = RotPins[pin]
            GPIO.output(xpin, ISeq[0][xpin])
            GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)



def Motorcontrolprobe(pillqueue):  #This will extend and retract the probe to make a pill fall into the probe, or make the system learn the position so that it occurs
    probenewpos = pillqueue[0][3]  #THIS MAY AVOID HAVING TO CHANGE THE IF STATEMENT LOCATION, MUST REFERENCE
    if(pillqueue[0][1] >= 0 and pillqueue[0][1] <= 6 and probelevel == 0): #checks to assure that the probe is at the bottom before acting, CAN ADD THE COMMAND TO MOVE INTO POSITION HERE AS WELL, ALREADY USED BEFORE THIS COMMAND THOUGH LOOK OVER IT TO MAKE SURE
        if(probenewpos[0] == None): #MAY HAVE TO CHANGE LOCATION SO THAT IF IT CHANGES probenewpos IT WON'T LOOP INTO THE NEXT ELIF AND BREAK INSTEAD
            Motorprobelearning()#Here goes the a function call to the learning mechanism that will learn the location and apply it to the array to remember
        elif(probenewpos[0] != None):
            Motorcontrolprobelength(probenewpos)
            Motorcontrolprobelengthretract(probenewpos)
    if(pillqueue[0][1] >= 7 and pillqueue[0][1] <= 13 and probelevel == 1): #checks to make sure the probe is up before acting
        if(probenewpos == None):
            Motorprobelearning()#Here goes the a function call to the learning mechanism that will learn the location and apply it to the array to remember
        elif(probenewpos != None):
            Motorcontrolprobelength(probenewpos)
            Motorcontrolprobelengthretract(probenewpos)

def Motorcontrolprobelevel(): #move the probe to the correct level position, down, or up
    if(pillqueue[0][1] >= 0 and pillqueue[0][1] <= 6 and probelevel == 0):
        global probelevel
        probelevel = 0
    elif(pillqueue[0][1] >= 0 and pillqueue[0][1] <= 6 and probelevel == 1):
        for amntstep in range(100): #don't know the range have to experiment to find the correct range
            for pin in range(5):
                xpin = RisePins[pin]
                GPIO.output(xpin, ISeq[0][xpin]) #move down from being in the up position
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        global probelevel
        probelevel = 0
    elif(pillqueue[0][1] >= 7 and pillqueue[0][1] <= 13 and probelevel == 0):
        for amntstep in range(100): #don't know the range have to experiment to find the correct range
            for pin in range(5):
                xpin = RisePins[pin]
                GPIO.output(xpin, Seq[0][xpin]) #move up from being in the down position
                GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)
        global probelevel
        probelevel = 1
    elif(pillqueue[0][1] >= 7 and pillqueue[0][1] <= 13 and probelevel == 1):
        global probelevel
        probelevel = 1

def Motorprobelearning(): #"learning" code that is used when the pill array doesn't know which probe drop is big enough to collect a pill from container
    probeforward = [1,0] #used to move the probe one full step at a time
    probeforward8th = [0,1] #used to move the probe one 8th step at a time
    probetrack = [0,0]  #used to keep track of the current amount of steps necessary for obtaining a pill
    done = False    #used as a check when moving in 8th steps to see if the pill was finally sucessfuly retrieved
    while(probesensor != 1): #moves the probe forward in full steps until it detects a pill is in or partially inside the probe
        Motorcontrolprobelength(probeforward)
        probetrack[0] =+ 1  #keeps track of how far forward in steps the probe has moved
    Motorcontrolprobelengthretract(probetrack) #moves the probe back to "home" when the sensor detects a pill
    if(probesensor1 == 1):  #if a pill is still detected, updates the pill array with the information on how far the probe has to move to retrieve a pill
        global pillarr
        pillarr[3][pillqueue[0][1]] = probetrack
    elif(probesensor1 != 1): #if a pill is not detected begins moving the probe in 8th steps to assure that a pill can be retreived without having a cascade of pills collect in the probe
        while(done != True): #will check with a true condition as sensor may go on and off during this time
            Motorcontrolprobelength(probetrack)
            Motorcontrolprobelength(probeforward8th)
            probetrack[1] =+ 1
            Motorcontrolprobelengthretract(probetrack)
            if(probetrack[1] == 8): #checks to see when 8 8th steps have occurred so that it can count that as a full step, and resets the 8 step count
                probetrack[0] = probetrack[0] + 1
                probetrack[1] = 0
            if(probesensor == 1):   #checks the probe after the system has fully retracted, if it has a pill in the probe, it is done
                done = True
                global pillarr
                pillarr[3][pillqueue[0][1]] = probetrack
            elif(probesensor != 1): #check to make sure that if nothing is found, that it will keep looping until it was successful
                done = False
            if(probetrack[0] == 200): # 200 steps is the max that a motor should move HAVE TO CHECK TO MAKE SURE THIS IS TRUE, PROBABLY NOT, IT JUST MEANS 200 STEPS IS A 360 ROTATION BY THE MOTOR
                done = True
                eso = "Pill not found/too big"
            elif(probetrack[0] < 200):
                eso = "Done"

        
    Pillarrbackup() #backs up the pill array to make sure information is not lost
    return eso #probably don't have to return this, since it would make the action give something, ESO should probably be an error check if nothing else, or only given at the extreme of the probe movement

def Queuebackup(pillqueue): # To be used for each iteration of the dispense command, as to make sure that no queue position is lost, and so if power goes out, can be retrieved from last known queue position
    loadinfo = open('pillqueueinfo', 'w')
    json.dump(pillqueue, loadinfo)
    loadinfo.close()

def Userschedulebackup():   #user pill schedule backup procedure
    loadinfo = open('pilluser1info', 'w')
    json.dump(pilluser1, loadinfo)
    loadinfo.close()
    loadinfo = open('pilluser2info', 'w')
    json.dump(pilluser2, loadinfo)
    loadinfo.close()
    loadinfo = open('pilluser3info', 'w')
    json.dump(pilluser3, loadinfo)
    loadinfo.close()
    loadinfo = open('pilluser4info', 'w')
    json.dump(pilluser4, loadinfo)
    loadinfo.close()
    loadinfo = open('pilluser5info', 'w')
    json.dump(pillsuer5, loadinfo)
    loadinfo.close()

def Pillarrbackup():    #pill array backup procedure
    loadinfo = open('pillarrinfo', 'w')
    json.dump(pillarr, loadinfo)
    loadinfo.close()

def Userinfobackup():   #user information backup procedure, this should only change when being entered at the very beginning of using the machine, not expected to change often
    loadinfo = open('user1info', 'w')
    json.dump(user1, loadinfo)
    loadinfo.close()
    loadinfo = open('user2info', 'w')
    json.dump(user2, loadinfo)
    loadinfo.close()
    loadinfo = open('user3info', 'w')
    json.dump(user3, loadinfo)
    loadinfo.close()
    loadinfo = open('user4info', 'w')
    json.dump(user4, loadinfo)
    loadinfo.close()
    loadinfo = open('user5info', 'w')
    json.dump(user5, loadinfo)
    loadinfo.close()

def Dispense():#Dispensing procedure, basic control of the dispensing process, will be run as long as pillqueue is not empty, but not while waiting for a new user, if previous user hasn't cleared pills
    Queuebackup(pillqueue)#hard backup of pillqueue, just in case
    pillcurrent = pillqueue[0]#variable for only the first item in queue, don't want to be manipulating entire queue yet
    tempqueue = pillqueue#used for manipulating queue without changing it globally, will change later
    Motorcontroldisk(pillqueue, lowdiscurrpos, updiscurrpos)#moves disk into position for probe to pull pill
    for amount in range(pillcurrent[4]):#loops for the amount of pills to be dispensed of that kind
        Motorcontrolprobelevel()
        Motorcontrolprobe(pillqueue)
        if(probesensor == 0):
            while(probesensor != 1):#This assumses the probe is in the correct position, and a pill should be here, it loops forever if a pill is never detected, HAVE TO INLCUDE BREAK CONDITIONS
                Motorcontrolprobelength(pillcurrent[3]) 
                Motorcontrolprobelengthretract(pillcurrent[3])
        elif(probesensor == 1):
            Motorcontrolprobdrop()#to make sure the system knows something was dispensed correctly
    Motorcontroldiskreturn(lowdiscurrpos, updiscurrpos)#resets disk back to "home" position when done with that pill
    tempqueue.popleft()#removing the oldest entry in the tempqueue, copied from the pill queue
    global pillqueue#updating pillqueue now that the oldest entry is done dispensing
    pillqueue = tempqueue
    Queuebackup(pillqueue)#hardback up of pillqueue
    if(pillcurrent[0] == user1[0]):#updating dispense condition for the user schedule, so that the dispense condition is correct
        global pilluser1
        pilluser1[pillcurrent[5]][pillcurrent[1]] = 1
    elif(pillcurrent[0] == user2[0]):
        global pilluser2
        pilluser2[pillcurrent[5]][pillcurrent[1]] = 1
    elif(pillcurrent[0] == user3[0]):
        global pilluser3
        pilluser3[pillcurrent[5]][pillcurrent[1]] = 1
    elif(pillcurrent[0] == user4[0]):
        global pilluser4
        pilluser4[pillcurrent[5]][pillcurrent[1]] = 1
    elif(pillcurrent[0] == user5[0]):
        global pilluser 5
        pilluser5[pillcurrent[5]][pillcurrent[1]] = 1
    Userschedulebackup()#hardbackup of the user data
    global pillarr#updating the remaining amount of pills in the pillarr, will be used to skip dispense and send warning when low on pills
    pillarr[2][pillcurrent[1]] = pillarr[2][pillcurrent[1]] - pillcurrent[4]
    Pillarrbackup()#hardbackup of pillarr
    

def Lowamountcheck():#can be used to mark pills that are low, or just warn the user, NOT SURE WHERE TO TAKE IT FROM HERE
    for amnt in range(len(pillarr[0])):
        if(pillarr[2][amnt] <= 20):
            pillarr[7][amnt] = "low"
            print("Low on", pillarr[1][amnt])

def Queuenopillclear():#This is to check the pillqueue versus the amount of pills actually left in storage, if there is less than the amount left, it will dispense the amount left in the container
    if(pillarr[2][pillqueue[0][5]] <= pillqueue[0][4]):#if there is none left in the container, it will remove the current check from the queue
        global pillqueue#THIS CAN BE INTEGRATED INTO THE SCHEDULE SEARCH TO REMOVE THIS IF WANTED
        pillqueue[0][4] = pillarr[2][pillqueue[0][5]]
    elif(pillarr[2][pillqueue[0][5]] == 0):
        global pillqueue
        pillqueue.popleft()

def Storageemptycheck():#Checking for a "name" under the pill array, if none is found it will give the index number, from smallest to largest, of this empty index,THIS MEANS THAT THE NAME OF THE PILL MUST
    col = 0#BE ENTERED AND SAVED INTO THE ARRAY AS THE FIRST THING BY THE USER IN ORDER TO PROPERLY IDENTIFY WHICH STORAGE UNIT WILL BE USED
    while(pillarr[1][col] != None and col < len(pillarr[0])):#used solely as a check, in order to keep the storage being used in increasing order
        col += 1
    return col

def Pilltostorage(): # will act by checking the lowest index location, has to kind of act as an initial set up, but can be incorporated into a complete function for initial pill deposition
    check = storageemptycheck() #THIS CAN BE TURNED INTO THE STORAGE LOCATION, PILLARR[4], IN ORDER TO CREATE A SYSTEM THAT CAN MOVE AROUND FROM ANY POSITION
    if(check <= 6):             #RATHER THAN ACT AS AN INITIAL SETUP SYSTEM, FOR THAT MUST INCLUDE CURRENT POSITION IN ORDER TO MOVE AROUND FREELY
        if(check == 0):
            distance = 5
        elif(check == 1):   #this is all relative to home, disk must start at home position, the lowest index empty check is ran, then it is moved that distance into the pill deposit position
            distance = 6    #IF SYSTEM DOESN'T START FROM BOTH DISK AT HOME, MAKE SURE TO SET THEM TO HOME FIRST
        elif(check == 2):
            distance = 0
        elif(check == 3):
            distance = 1
        elif(check == 4):
            distance = 2
        elif(check == 5):
            distance = 3
        elif(check == 6):
            distance = 4
        for amntstep in range(28*distance): #moving the 28 full steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq[0][xpin])
                GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*distance): #approximate the movement of 0.571 for every 28 steps, rounded to .5
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq8th[0][xpin])
                GPIO.output(xpin, Seq8th[1][xpin])
            time.sleep(.01)
    if(check >= 7):
        if(check == 7):
            distance = 2
        elif(check == 8):
            distance = 3
        elif(check == 9):
            distance = 4
        elif(check == 10):
            distance = 5
        elif(check == 11):
            distance = 6
        elif(check == 12): #supposed to be number 13, but has to be 12, since storage empty check returns the index of the pillarr, not the storage position
            distance = 1
        for amntstep in range(28*updisdelta): #moving the 28 full steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq[0][xpin])
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*updisdelta): #moving .5 to approximate .571 for every 28 steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq8th[0][xpin])
                GPIO.output(xpin, ISeq8th[1][xpin])
            time.sleep(.01)
    return check #this will be used to move the disk back to the home position from the deposit position

def Pilltostoragereturn(check):#Make sure to pass "check" from the pilltostorage function, will be used to move back to home
    if(check <= 6):             #THIS CAN BE MODIFIED IF I USE A MOVE CURRPOS WITH THE PILL TO STORAGE FUNCTION ABOVE,
        if(check == 0):         #MODIFICATION WOULD SIMPLY BE TO CHECK CURRPOS AND THEN MOVE TO "HOME", WOULD ONLY HAVE TO
            distance = 2        #RENAME "distance" AND MAKE SURE THE IF STATEMENTS HAVE THE CORRECT NUMBERS
        elif(check == 1):
            distance = 1
        elif(check == 2):
            distance = 0
        elif(check == 3):
            distance = 6
        elif(check == 4):
            distance = 5
        elif(check == 5):
            distance = 4
        elif(check == 6):
            distance = 3
        for amntstep in range(28*distance): #moving the 28 full steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq[0][xpin])
                GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*distance): #approximate the movement of 0.571 for every 28 steps, rounded to .5
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq8th[0][xpin])
                GPIO.output(xpin, Seq8th[1][xpin])
            time.sleep(.01)
    if(check >= 7):
        if(check == 7):
            updistance = 5
        elif(check == 8):
            updistance = 4
        elif(check == 9):
            updistance = 3
        elif(check == 10):
            updistance = 2
        elif(check == 11):
            updistance = 1
        elif(check == 12):
            updistance = 6
        for amntstep in range(28*updistance): #moving the 28 full steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq[0][xpin])
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*updistance): #moving .5 to approximate .571 for every 28 steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq8th[0][xpin])
                GPIO.output(xpin, ISeq8th[1][xpin])
            time.sleep(.01)

def Pillmanualdispense(pillstorage,pillamount):#passing the storage location and amount to be manually dispensed, can rename variables,THIS CAN BE MADE TO USE FUNCTION CALLS, IF I MAKE THE FUNCTION CALLS BE ABLE TO TAKE MORE THAN 1 VARIABLE, BASED ON AN IF STATEMENT CHECKING FOR WHICH VARIABLE SHOULD BE USED
    if(pillarr[4][pillstorage] <= 6):                                                                #send signals, probably a second loop for that
        lowdisnewpos = pillarr[4][pillstorage]                                                 #so far this gives the the position difference
        lowdisdelta = abs(lowdisnewpos - lowdiscurrpos)                                   #between where it is and where it needs to be
        for amntstep in range(28*lowdisdelta):              
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq[0][xpin])
                GPIO.output(xpin, Seq[1][xpin])
            time.sleep(.01)                      #time delay for the chip to read and process correctly
        for amntstep in range(4*lowdisdelta):   #fixing the .571 to approximate .5, for every 28 steps
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, Seq8th[0][xpin])
                GPIO.output(xpin, Seq8th[1][xpin])
            time.sleep(.01)
        global lowdiscurrpos
        lowdiscurrpos = lowdisnewpos
    elif(pillarr[4][pillstorage] >=7):
        updisnewpos = pillarr[4][pillstorage]
        updisdelta = abs(updisnewpos - updiscurrpos)    #This is code from the disk movement, just copy/pasted and altered to work with button given variables rather than from the pill queue
        for amntstep in range(28*updisdelta):
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq[0][xpin])
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        for amntstep in range(4*updisdelta):
            for pin in range(5):
                xpin = StepPins[pin]
                GPIO.output(xpin, ISeq8th[0][xpin])
                GPIO.output(xpin, ISeq8th[1][xpin])
            time.sleep(.01)
        global updiscurrpos
        updiscurrpos = updisnewpos
    if(pillarr[4][pillstorage] >= 0 and pillarr[4][pillstorage] <= 6 and probelevel == 0):  #This code is from the probe level, just copy/pasted and altered to work with the button given variables rather than from the pill queue
        global probelevel
        probelevel = 0
    elif(pillarr[4][pillstorage] >= 0 and pillarr[4][pillstorage] <= 6 and probelevel == 1):
        for amntstep in range(100): #don't know the range have to experiment to find the correct range
            for pin in range(5):
                xpin = RisePins[pin]
                GPIO.output(xpin, ISeq[0][xpin]) #move down from being in the up position
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        global probelevel
        probelevel = 0
    elif(pillarr[4][pillstorage] >= 7 and pillarr[4][pillstorage] <= 13 and probelevel == 0):
        for amntstep in range(100): #don't know the range have to experiment to find the correct range
            for pin in range(5):
                xpin = RisePins[pin]
                GPIO.output(xpin, ISeq[0][xpin]) #move up from being in the down position
                GPIO.output(xpin, ISeq[1][xpin])
            time.sleep(.01)
        global probelevel
        probelevel = 1
    elif(pillstorage >= 7 and pillstorage <= 13 and probelevel == 1):
        global probelevel
        probelevel = 1

    for dispamount in range(pillamount):    #THIS IS ALL CODE FROM MOTOR CONTROL PROBE, JUST COPY/PASTED AND ALTERED TO WORK WITH THE GIVEN VARIABLES RATHER THAN FROM THE PILL QUEUE
        probenewpos = pillarr[3][pillstorage]  #THIS MAY AVOID HAVING TO CHANGE THE IF STATEMENT LOCATION, MUST REFERENCE
        if(pillqueue[0][1] >= 0 and pillqueue[0][1] <= 6 and probelevel == 0): #checks to assure that the probe is at the bottom before acting, CAN ADD THE COMMAND TO MOVE INTO POSITION HERE AS WELL, ALREADY USED BEFORE THIS COMMAND THOUGH LOOK OVER IT TO MAKE SURE
            if(probenewpos[0] == None): #MAY HAVE TO CHANGE LOCATION SO THAT IF IT CHANGES probenewpos IT WON'T LOOP INTO THE NEXT ELIF AND BREAK INSTEAD
                Motorprobelearning()#Here goes the a function call to the learning mechanism that will learn the location and apply it to the array to remember
            elif(probenewpos[0] != None):
                Motorcontrolprobelength(probenewpos)
                Motorcontrolprobelengthretract(probenewpos)
        if(pillqueue[0][1] >= 7 and pillqueue[0][1] <= 13 and probelevel == 1): #checks to make sure the probe is up before acting
            if(probenewpos == None):
                Motorprobelearning()#Here goes the a function call to the learning mechanism that will learn the location and apply it to the array to remember
            elif(probenewpos != None):
                Motorcontrolprobelength(probenewpos)
                Motorcontrolprobelengthretract(probenewpos)
        if(probesensor == 0):
            while(probesensor != 1):#This assumses the probe is in the correct position, and a pill should be here, it loops forever if a pill is never detected, HAVE TO INLCUDE BREAK CONDITIONS
                Motorcontrolprobelength(probenewpos)
                Motorcontrolprobelengthretract(probenewpos)
        elif(probesensor == 1):
            Motorcontrolprobdrop()#to make sure the system knows something was dispensed correctly
    Motorcontroldiskreturn(lowdiscurrpos, updiscurrpos)#resets disk back to "home" position when done with that pill
    global pillarr
    pillarr[2][pillstorage] = pillarr[2][pillstorage] - pillamount
    Pillarrbackup()
    
