from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.config import Config
from kivy.uix.vkeyboard import VKeyboard
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import os
import urllib
from json import json
from datetime import datetime
from datetime import timedelta
from datetime import date
from collections import deque
import RPi.GPIO as GPIO
import time
from kivy.network.urlrequest import UrlRequest

Window.clearcolor = (1,1, 1, 1)


class MedbayRoot(BoxLayout):
    def __init__(self,**kwargs):
       super(MedbayRoot, self).__init__(**kwargs)

#class Screen6(Screen):

    #search_input = ObjectProperty()

  #  def search_gtin(self):
        #api.get_product("078915030900")
        #apikey = api_code
        #url = 'https://api.outpan.com/v2/products/?apikey=' + apikey
        #gtin = query.replace('')
        #final_url = url + "&gtin=" + gtin
        #json_obj = urllib.urlopen(final_urlurl)
        #data = json.load(json_obj)

       # for item in data['name']:
        #    print (item)
        #search_template = 'https://api.outpan.com/v2/products/?apikey=[d56b84efd0ad72262d85e16a5462b75f]'
        #search_url = search_template.format(self.search_input.text)
        #request = UrlRequest(search_url, self.found_gtin)
        #print("The user searched for '{}'".format(self.search_input.text))
        
   # def found_gtin(self,request,data):
    #    product = ["{}".format(d['GTIN'])
     #       for d in data['list']]
      #  print("\n".product)

      
#class Screen7(Screen):
 #    def pill_names(self):
  #       print("The pill chosen is'{}'".format(self.search_pills.text))

class MedbayApp(App):

    def __init__(self,**kwargs):
       super(MedbayApp, self).__init__(**kwargs)

    def build(self):
    
        return MedbayRoot()
       
if __name__ == "__main__":
    MedbayApp().run()

