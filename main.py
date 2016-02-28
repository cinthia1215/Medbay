from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.config import Config
from kivy.uix.vkeyboard import VKeyboard
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.loader import Loader
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.popup import Popup
import os
import urllib
import json 
from datetime import datetime
from datetime import timedelta
from datetime import date
from collections import deque
from RPi import GPIO
import time
from kivy.network.urlrequest import UrlRequest
Window.clearcolor = (1,1, 1, 0)

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
user1 = [None for i in range(5)] #name, pass, phone, emergency,fingerprint
user2 = [None for i in range(5)]
user3 = [None for i in range(5)]
user4 = [None for i in range(5)]
user5 = [None for i in range(5)]
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
namecheck = None #for screen 2
passcheck = None
dynamicassign = [None, None, None, None, None] #for screen 3
currentuser = None

try:
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
    retrieveinf.c
except:
    pass

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

#user1[0] = 'asdf' #forcing user to a certain name/password
#user1[1] = 'jkl'    #no longer need this definition as of feb.26
#user2[0] = 'cinthia1215'
#user2[1] = 'password'


class Manager(ScreenManager): #allows transitions of different screens on python
    start_screen = ObjectProperty(None)
    screen_2 = ObjectProperty(None)
    screen_3 = ObjectProperty(None)
    screen_4 = ObjectProperty(None)
    screen_5 = ObjectProperty(None)
    screen_6 = ObjectProperty(None)
    screen_7 = ObjectProperty(None)
    screen_8 = ObjectProperty(None)
    pass_popup = ObjectProperty(None)

class StartScreen(Screen):
    def movescreenSto2(self):
        self.manager.current = 'screen_2'
    def movescreenSto3(self):
        self.manager.current = 'screen_3'

class Screen2(Screen): #comparison systenm from screen2,
    name_input = ObjectProperty()#name of variable from kivy
    pass_input = ObjectProperty()
    #fingercheck
    
    def usernamepass(self,name_input): #runs on button press to assign user info to var, to allow movescreen2to4 to be dynamic
        if(self.name_input.text == user1[0]):
            global namecheck
            namecheck = user1[0]
            global passcheck
            passcheck = user1[1]
        elif(self.name_input.text == user2[0]):
            global namecheck
            namecheck = user2[0]
            global passcheck
            passcheck = user2[1]
        elif(self.name_input.text == user3[0]):
            global namecheck
            namecheck = user3[0]
            global passcheck
            passcheck = user3[1]
        elif(self.name_input.text == user4[0]):
            global namecheck
            namecheck = user4[0]
            global passcheck
            passcheck = user4[1]
        elif(self.name_input.text == user5[0]):
            global namecheck
            namecheck = user5[0]
            global passcheck
            passcheck = user5[1]
        else:
            self.manager.current = 'pass_popup'
        
    def movescreen2to4(self,name_input,pass_input):#function of screen movement on succesful comparison
        if(self.name_input.text == namecheck and self.pass_input.text == passcheck):
            currentuser = namecheck
            self.manager.current = 'screen_4'   
        else: 
            self.manager.current = 'pass_popup'
        return currentuser
    

class PassPopup(Screen):
    def movetoscreen2(self):
        self.manager.current = 'screen_2'

class Screen3(Screen):
    add_name1 = ObjectProperty()
    add_pass1 = ObjectProperty()
    chk_pass1 = ObjectProperty()
    add_num1 = ObjectProperty()
    add_cont1 = ObjectProperty()

    def moveinfo(self,add_name1,add_pass1,chk_pass1,add_num1,add_cont1):
        if(self.chk_pass1.text == self.add_pass1.text):
            dynamicassign[0] = self.add_name1.text
            dynamicassign[1] = self.add_pass1.text
            dynamicassign[2] = self.add_num1.text
            dynamicassign[3] = self.add_cont1.text
        elif(self.chk_pass1.text != self.add_pass1.text):
            self.manager.current = 'addinfo_popup'

    def userempty(self):
        if(user1[0] == None):
            global user1
            user1 = dynamicassign
            Userinfobackup()
            self.manager.current = 'start_screen'
        elif(user2[0] == None and user1[0] != None):
            global user2
            user2 = dynamicassign
            Userinfobackup()
            self.manager.current = 'start_screen'
        elif(user3[0] == None and user2[0] != None):
            global user3
            user3 = dynamicassign
            Userinfobackup()
            self.manager.current = 'start_screen'
        elif(user4[0] == None and user3[0] != None):
            global user4
            user4 = dynamicassign
            Userinfobackup()
            self.manager.current = 'start_screen'
        elif(user5[0] == None and user4[0] != None):
            global user5
            user5 = dynamicassign
            Userinfobackup()
            self.manager.current = 'start_screen'
        elif(user1[0] != None and user2[0] != None and user3[0] != None and user4[0] != None and user5[0] != None):
            self.manager.current = 'noinfoempty_popup'

class AddInfopop(Screen):
    def movetoscreen3(self):
        self.manager.current = 'screen_3'

class NoInfo(Screen):
    def movetoscreen3(self):
        self.manager.curent = 'screen_3'

class Screen4(Screen):
    def movescreen4to5(self):
        self.manager.current = 'screen_5'
    def movescreen4to8(self):
        self.manager.current = 'screen_8'
    def movescreen4to7(self):
        self.manager.current = 'screen_7'
    #def movescreen4to #THIS IS PLACEHOLDER FOR VIEWING SCHEDULE

    def movescreen4toS(self):
        global currentuser
        currentuser = None
        self.manager.current = 'start_screen'

class MedbayRoot(BoxLayout):
    def __init__(self,**kwargs):
       super(MedbayRoot, self).__init__(**kwargs)
       
class MedbayApp(App):

    def __init__(self,**kwargs):
       super(MedbayApp, self).__init__(**kwargs)
    def build(self):
        return MedbayRoot()
    pill1 = str(pillarr[0][0])
    pill2 = str(pillarr[0][1])
    pill3 = str(pillarr[0][2])
    pill4 = str(pillarr[0][3])
    pill5 = str(pillarr[0][4])
    pill6 = str(pillarr[0][5])
    pill7 = str(pillarr[0][6])
    pill8 = str(pillarr[0][7])
    pill9 = str(pillarr[0][8])
    pill10 = str(pillarr[0][9])
    pill11 = str(pillarr[0][10])
    pill12 = str(pillarr[0][11])
    pill13 = str(pillarr[0][12])
    greeting = "Hello, " + str(currentuser)

       
if __name__ == "__main__":
    MedbayApp().run()

