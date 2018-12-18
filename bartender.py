import os
import time
import sys
import RPi.GPIO as GPIO
import json
import threading
import traceback
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306


from subprocess import * 
from subprocess import call

#imports for email
# import imaplib 
# import smtplib 
# import email 
# from email.mime.text import MIMEText 
# from email.parser import HeaderParser 
# from email.MIMEMultipart import MIMEMultipart 
# from email.MIMEBase import MIMEBase 
# from email.Utils import COMMASPACE, formatdate
# from email import Encoders

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
#from dotstar import Adafruit_DotStar
from menu import MenuItem, Menu, Back, MenuContext, MenuDelegate

GPIO.setmode(GPIO.BCM)

USERNAME = "michaelpocta30@gmail.com"
PASSWORD = "H3anover0"

stopprogram = False

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32

CLK_PIN = 13
DT_PIN = 19

LEFT_BTN_PIN = 13
LEFT_PIN_BOUNCE = 1000

RIGHT_BTN_PIN = 5
RIGHT_PIN_BOUNCE = 2000

MAKE_DRINK = True

OLED_RESET_PIN = 15
OLED_DC_PIN = 16

NUMBER_NEOPIXELS = 45
NEOPIXEL_DATA_PIN = 26
NEOPIXEL_CLOCK_PIN = 6
NEOPIXEL_BRIGHTNESS = 64

FLOW_RATE = 60.0/100.0

class Bartender(MenuDelegate): 
        
	def __init__(self):
		self.running = False

		# set the oled screen height
		self.screen_width = SCREEN_WIDTH
		self.screen_height = SCREEN_HEIGHT
		
		self.make_drink = MAKE_DRINK

		self.btn1Pin = LEFT_BTN_PIN
		self.btn2Pin = RIGHT_BTN_PIN

		self.clk = CLK_PIN
		self.dt = DT_PIN

	 	# configure interrupts for buttons
		#GPIO.setup(self.btn1Pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup(self.btn2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  

		# configure interrupts for encoder
		GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
		GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

		#Pi config
		RST = 21
		DC = 20
		SPI_PORT = 0
		SPI_DEVICE = 0

		# configure screen
		self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
		self.disp.begin()
		self.disp.clear()
		self.disp.display()

		#draw
		self.image = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT))
		self.draw = ImageDraw.Draw(self.image)
		self.draw.rectangle((0,0,SCREEN_WIDTH,SCREEN_HEIGHT), outline=0, fill=0)
		self.font = ImageFont.load_default()

		# Very important... This lets py-gaugette 'know' what pins to use in order to reset the display
 		# Change rows & cols values depending on your display dimensions.

		# load the pump configuration from file
		self.pump_configuration = Bartender.readJson('static/json/pump_config.json')
		for pump in self.pump_configuration.keys():
			GPIO.setup(self.pump_configuration[pump]["pin"], GPIO.OUT, initial=GPIO.HIGH)

		# load the current drink list
		self.drink_list = Bartender.readJson('static/json/drink_list.json')
		self.drink_list = self.drink_list["drink_list"]

		# load the current drink options
		self.drink_options = Bartender.readJson('static/json/drink_options.json')
		self.drink_options = self.drink_options["drink_options"]

		# setup pixels:
		#self.numpixels = NUMBER_NEOPIXELS # Number of LEDs in strip

		# Here's how to control the strip from any two GPIO pins:
		#datapin  = NEOPIXEL_DATA_PIN
		#clockpin = NEOPIXEL_CLOCK_PIN
		#self.strip = Adafruit_DotStar(self.numpixels, datapin, clockpin)
		#self.strip.begin()           # Initialize pins for output
		#self.strip.setBrightness(NEOPIXEL_BRIGHTNESS) # Limit brightness to ~1/4 duty cycle

		# turn everything off
		#for i in range(0, self.numpixels):
		#	self.strip.setPixelColor(i, 0)
		#self.strip.show() 

		print('Done initializing')


	# def check_email(self):
	# 	status, email_ids = self.imap_server.search(None, '(UNSEEN)')
	# 	if email_ids == ['']:
	# 		mail_list = []
	# 	else:
	# 		mail_list = self.get_subjects(email_ids) #FYI when calling the get_subjects function, the email is marked as 'read'
	# 	self.imap_server.close()
	# 	return mail_list

	# def get_subjects(self, email_ids):
	# 	subjects_list = []
	# 	for e_id in email_ids[0].split():
	# 		resp, data = self.imap_server.fetch(e_id, '(RFC822)')
	# 		perf = HeaderParser().parsestr(data[0][1])
	# 		subjects_list.append(perf['Subject'])

	# 	return subjects_list

	def voice_command(self, mail_list):
		for mail in mail_list:
			found = False
			while(found == False):
				currmen = self.menuContext.currentMenu.getSelection()
				if(currmen.name == mail):
					self.makeDrink(currmen.name, currmen.attributes["ingredients"])
					self.make_drink = False
					found = True
				else:
					self.menuContext.currentMenu.nextSelection()
			found = False

	@staticmethod
	def readJson(file):
		return json.load(open(file))

	@staticmethod
	def writePumpConfiguration(configuration):
		with open("static/json/pump_config.json", "w") as jsonFile:
			json.dump(configuration, jsonFile)

	def startInterrupts(self):
		#GPIO.add_event_detect(self.btn1Pin, GPIO.FALLING, callback=self.left_btn, bouncetime=LEFT_PIN_BOUNCE)  
		GPIO.add_event_detect(self.btn2Pin, GPIO.FALLING, callback=self.right_btn, bouncetime=RIGHT_PIN_BOUNCE)  
		GPIO.add_event_detect(self.clk, GPIO.BOTH, callback=self.rotary_on_change, bouncetime=1000)  

	def stopInterrupts(self):
		#GPIO.remove_event_detect(self.btn1Pin)
		GPIO.remove_event_detect(self.btn2Pin)
		GPIO.remove_event_detect(self.clk)

	def buildMenu(self):
		# create a new main menu
		m = Menu("Main Menu")

		# add drink options
		drink_opts = []
		for d in self.drink_list:
			drink_opts.append(MenuItem('drink', d["name"], {"ingredients": d["ingredients"]}))

		configuration_menu = Menu("Configure")

		# add pump configuration options
		pump_opts = []
		for p in sorted(self.pump_configuration.keys()):
			config = Menu(self.pump_configuration[p]["name"])
			# add fluid options for each pump
			for opt in self.drink_options:
				# star the selected option
				selected = "*" if opt["value"] == self.pump_configuration[p]["value"] else ""
				config.addOption(MenuItem('pump_selection', opt["name"], {"key": p, "value": opt["value"], "name": opt["name"]}))
			# add a back button so the user can return without modifying
			config.addOption(Back("Back"))
			config.setParent(configuration_menu)
			pump_opts.append(config)

		# add pump menus to the configuration menu
		configuration_menu.addOptions(pump_opts)
		# add a back button to the configuration menu
		configuration_menu.addOption(Back("Back"))
		# adds an option that cleans all pumps to the configuration menu
		configuration_menu.addOption(MenuItem('clean', 'Clean'))
		configuration_menu.setParent(m)

		m.addOptions(drink_opts)
		m.addOption(configuration_menu)
		# create a menu context
		self.menuContext = MenuContext(m, self)

	def filterDrinks(self, menu):
		"""
		Removes any drinks that can't be handled by the pump configuration
		"""
		for i in menu.options:
			if (i.type == "drink"):
				i.visible = False
				ingredients = i.attributes["ingredients"]
				presentIng = 0
				for ing in ingredients.keys():
					for p in self.pump_configuration.keys():
						if (ing == self.pump_configuration[p]["value"]):
							presentIng += 1
				if (presentIng == len(ingredients.keys())): 
					i.visible = True
			elif (i.type == "menu"):
				self.filterDrinks(i)

	def selectConfigurations(self, menu):
		"""
		Adds a selection star to the pump configuration option
		"""
		for i in menu.options:
			if (i.type == "pump_selection"):
				key = i.attributes["key"]
				if (self.pump_configuration[key]["value"] == i.attributes["value"]):
					i.name = "%s %s" % (i.attributes["name"], "*")
				else:
					i.name = i.attributes["name"]
			elif (i.type == "menu"):
				self.selectConfigurations(i)

	def prepareForRender(self, menu):
		self.filterDrinks(menu)
		self.selectConfigurations(menu)
		return True

	def menuItemClicked(self, menuItem):
		if (menuItem.type == "drink"):
			if self.make_drink:
				self.makeDrink(menuItem.name, menuItem.attributes["ingredients"])
				self.make_drink = False
			return True
		elif(menuItem.type == "pump_selection"):
			self.pump_configuration[menuItem.attributes["key"]]["value"] = menuItem.attributes["value"]
			Bartender.writePumpConfiguration(self.pump_configuration)
			return True
		elif(menuItem.type == "clean"):
			if self.make_drink:
				self.clean()
				self.make_drink = False
			return True
		return False

	def changeConfiguration(self, pumps):
		# Change configuration of every pump
		for i in range(1, 7):
			self.pump_configuration["pump_"+str(i)]["value"] = pumps[i-1]

		Bartender.writePumpConfiguration(self.pump_configuration)

	def clean(self):
		waitTime = 30
		pumpProcesses = []

		# cancel any button presses while the drink is being made
		# self.stopInterrupts()
		self.running = True

		for pump in self.pump_configuration.keys():
			pump_p = threading.Thread(target=self.pour, args=(self.pump_configuration[pump]["pin"], waitTime,))
			pumpProcesses.append(pump_p)

		disp_process = threading.Thread(target=self.progressBar, args=(waitTime,))
		pumpProcesses.append(disp_process) 

		# start the pump threads
		for process in pumpProcesses:
			process.start()

		# wait for threads to finish
		for process in pumpProcesses:
			process.join()

		# sleep for a couple seconds to make sure the interrupts don't get triggered
		time.sleep(2)

		# reenable interrupts
		# self.startInterrupts()
		self.running = False
		self.make_drink = True

		self.menuContext.showMenu()

	def displayMenuItem(self, menuItem):
		#Clear display
		self.draw.rectangle((0,0,SCREEN_WIDTH, SCREEN_HEIGHT),outline=0,fill=0)
		self.draw.text((20,10), menuItem.name, font=self.font, fill=255)
		self.disp.image(self.image)
		self.disp.display()

	def cycleLights(self):
		t = threading.currentThread()
		head  = 0               # Index of first 'on' pixel
		tail  = -10             # Index of last 'off' pixel
		color = 0xFF0000        # 'On' color (starts red)

		while getattr(t, "do_run", True):
			self.strip.setPixelColor(head, color) # Turn on 'head' pixel
			self.strip.setPixelColor(tail, 0)     # Turn off 'tail'
			self.strip.show()                     # Refresh strip
			time.sleep(1.0 / 50)             # Pause 20 milliseconds (~50 fps)

			head += 1                        # Advance head position
			if(head >= self.numpixels):           # Off end of strip?
				head    = 0              # Reset to start
				color >>= 8              # Red->green->blue->black
				if(color == 0): color = 0xFF0000 # If black, reset to red

			tail += 1                        # Advance tail position
			if(tail >= self.numpixels): tail = 0  # Off end? Reset

	def lightsEndingSequence(self):
		# make lights green
		for i in range(0, self.numpixels):
			self.strip.setPixelColor(i, 0xFF0000)
		self.strip.show()

		time.sleep(5)

		# turn lights off
		for i in range(0, self.numpixels):
			self.strip.setPixelColor(i, 0)
		self.strip.show() 

	def pour(self, pin, waitTime):
		GPIO.output(pin, GPIO.LOW)
		time.sleep(waitTime)
		GPIO.output(pin, GPIO.HIGH)

	def progressBar(self, waitTime):
		interval = waitTime / 116.3
        
		for x in range(1, 101):		
			# Clear display
			self.draw.rectangle((0,0,SCREEN_WIDTH, SCREEN_HEIGHT),outline=0,fill=0)
			#self.draw.text((55,20), str(x) + '%', font = self.font, fill=255)
			self.updateProgressBar(x, y=10)
			self.disp.image(self.image)
			self.disp.display()
			time.sleep(interval)
		# 	# self.disp.clear()
		# 	# self.disp.display()

               # self.image = Image.open('happycat_oled_32.ppm').convert('1')

               # self.disp.image(self.image)
               # self.disp.display()

	def makeDrink(self, drink, ingredients):
		if self.running:
			return

		# cancel any button presses while the drink is being made
		# self.stopInterrupts()
		print('Making a ' + drink)
		self.running = True

		# launch a thread to control lighting
	#	lightsThread = threading.Thread(target=self.cycleLights)
	#	lightsThread.start()

		# Make a list for each potential time

		maxTime = 0
		pumpProcesses = []
		for ing in ingredients.keys():
			for pump in self.pump_configuration.keys():
				if ing == self.pump_configuration[pump]["value"]:
					waitTime = ingredients[ing] * FLOW_RATE
					if (waitTime > maxTime):
						maxTime = waitTime
					pump_p = threading.Thread(target=self.pour, args=(self.pump_configuration[pump]["pin"], waitTime))
					pumpProcesses.append(pump_p)

                
		disp_process = threading.Thread(target=self.progressBar, args=(maxTime,))
		pumpProcesses.append(disp_process) 

                # start the pump threads
		for process in pumpProcesses:
			process.start()

		# wait for threads to finish
		for process in pumpProcesses:
			process.join()

		# stop the light thread
	    #	lightsThread.do_run = False
	#	lightsThread.join()

		# show the ending sequence lights
		#self.lightsEndingSequence()


		# reenable interrupts
		# sleep for a couple seconds to make sure the interrupts don't get triggered
		time.sleep(2)
		# self.startInterrupts()
		self.running = False
		print('Finished making ' + drink)
		self.make_drink = True


		# show the main menu
		self.menuContext.showMenu()

	def left_btn(self, ctx):
		if not self.running:
			self.menuContext.advance()

	def right_btn(self, ctx):
		if not self.running:
			self.menuContext.select()

	def rotary_on_change(self, ctx):
		if not self.running:
			if GPIO.input(self.dt):
				self.menuContext.retreat()
			else:
				self.menuContext.advance()

	def get_ingredients_time(self, drink):
		# Get the ingredients for the specified drink
		found = False
		while(found == False):
			currmen = self.menuContext.currentMenu.getSelection()
			if(currmen.name == drink):
				ingredients = currmen.attributes["ingredients"]
				self.make_drink = False
				found = True
			else:
				self.menuContext.currentMenu.nextSelection()

		# Get the drink making time
		maxTime = 0
		for ing in ingredients.keys():
			for pump in self.pump_configuration.keys():
				if ing == self.pump_configuration[pump]["value"]:
					waitTime = ingredients[ing] * FLOW_RATE
					if (waitTime > maxTime):
						maxTime = waitTime

		# Return making time and ingredients for drink
		return ingredients, maxTime


	def updateProgressBar(self, percent, x=15, y=10):
	   
		height = 10
		width = self.screen_width-2*x

		for w in range(0, width):
			self.draw.point((w + x, y),fill=255)
			self.draw.point((w + x, y + height),fill=255)
		for h in range(0, height):
			self.draw.point((x, h + y),fill=255)
			self.draw.point((self.screen_width-x, h + y),fill=255)
			for p in range(0, percent):
				p_loc = int(p/100.0*width)
				self.draw.point((x + p_loc, h + y),fill=255)
				self.draw.text((55,20), str(percent) + '%', font = self.font, fill=255)
				#self.disp.image(self.image)
			#self.disp.display()

	
	def endprogram(self):
		global stopprogram

		stopprogram = True

		# Goodbye message
		self.draw.rectangle((0,0,SCREEN_WIDTH, SCREEN_HEIGHT),outline=0,fill=0)
		self.draw.text((20,10), "Goodbye...", font=self.font, fill=255)
		self.disp.image(self.image)
		self.disp.display()
		time.sleep(3)

		self.draw.rectangle((0,0,SCREEN_WIDTH, SCREEN_HEIGHT),outline=0,fill=0)
		self.draw.text((15,10), "Have a great day!", font=self.font, fill=255)
		self.disp.image(self.image)
		self.disp.display()

		time.sleep(3)
		self.disp.clear()
		self.disp.display()

	def run(self):
		self.startInterrupts()
		# main loop
		try:  
			while True:
				if stopprogram:
					return
				# self.imap_server = imaplib.IMAP4_SSL("imap.gmail.com",993)
				# self.imap_server.login(USERNAME, PASSWORD)
				# self.imap_server.select('INBOX')
				# mail_list = self.check_email()
				# if mail_list and not self.running:
				# 	self.voice_command(mail_list)
				time.sleep(0.1)
		  
		except KeyboardInterrupt:  
			GPIO.cleanup()       # clean up GPIO on CTRL+C exit 
			sys.exit(0)
			
		GPIO.cleanup()           # clean up GPIO on normal exit 

		traceback.print_exc()


# bartender = Bartender()
# bartender.buildMenu()
# bartender.run()




