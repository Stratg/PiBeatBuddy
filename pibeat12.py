# coding: utf-8
import os,time,pygame,configparser,sys,RPi.GPIO as GPIO
from numpy import zeros,array
from timeit import default_timer as timer
from threading import Thread
from random import seed,randint
#import I2C_LCD_driver

import lcddriver

# seed random number generator
seed(1)

WORKING_PATH = os.path.dirname(os.path.abspath( __file__ )) + "/"
KITS_FOLDER = WORKING_PATH + "kits/"
RHYTHM_FOLDER = WORKING_PATH + "rythms/"
RHYTHM_PATH = RHYTHM_FOLDER + "shuffle.rythm"

BPM = 120

SWITCH_1 = 37
SWITCH_2 = 35
SWITCH_3 = 33
SWITCH_4 = 31
ROTARY_1_C = 12
ROTARY_1_D = 10
ROTARY_1_S = 8
LED0 = 19
LED1 = 7 
LED2 = 11
LED3 = 13
LED4 = 15


global curseur
global StepTracker
global LCD_Message

global SWITCH_1_PRESSED
global SWITCH_2_PRESSED
global SWITCH_3_PRESSED
global SWITCH_4_PRESSED
global SWITCH_1_LONG_PRESSED
global SWITCH_4_LONG_PRESSED
global ROTARY_1_LEFT
global ROTARY_1_RIGHT
global ROTARY_1_CLICK

SWITCH_1_PRESSED = False
SWITCH_2_PRESSED = False
SWITCH_3_PRESSED = False
SWITCH_4_PRESSED = False
SWITCH_1_LONG_PRESSED = False	
SWITCH_3_LONG_PRESSED = False
SWITCH_4_LONG_PRESSED = False
ROTARY_1_LEFT = False	
ROTARY_1_RIGHT = False	
ROTARY_1_CLICK = False	

####Classe lecture des GPIO ####
class GPIOReader(Thread):

    def __init__(self):
        Thread.__init__(self)

    def run(self):
		global SWITCH_1_PRESSED
		global SWITCH_2_PRESSED
		global SWITCH_3_PRESSED
		global SWITCH_4_PRESSED
		global SWITCH_1_LONG_PRESSED
		global SWITCH_3_LONG_PRESSED
		global SWITCH_4_LONG_PRESSED
		global ROTARY_1_LEFT
		global ROTARY_1_RIGHT
		global ROTARY_1_CLICK
		
		clkLastState = GPIO.input(ROTARY_1_C)
		flag = False
		SwitchReleaseTime = 0.3
		while True:
			
			# lecture de l'encodeur rotatif  
			clkState = GPIO.input(ROTARY_1_C) 
			if clkState != clkLastState:
				dtState = GPIO.input(ROTARY_1_D)
				if flag==True: flag = False
				else: flag = True
				#print ("clkState = "+str(clkState)+" | clkState = " + str(dtState)) 
				if dtState != clkState:  
					if flag==True:	ROTARY_1_LEFT = True
				else: 
					if flag==True: ROTARY_1_RIGHT = True
			clkLastState = clkState

			# lecture du bouton de l'encodeur rotatif
			if GPIO.input(ROTARY_1_S) == 0: 	
				ROTARY_1_CLICK = True	
				time.sleep(SwitchReleaseTime)	
			
			# lecture du bouton 1
			if GPIO.input(SWITCH_1) == 0: 	
				PwButtonStart = timer()
				while GPIO.input(SWITCH_1) == 0:
					time.sleep(0.1)
					duree = timer() - PwButtonStart
					if duree > 1: 
						SWITCH_1_LONG_PRESSED = True
						time.sleep(SwitchReleaseTime)	
					else: 
						SWITCH_1_PRESSED = True
						time.sleep(SwitchReleaseTime)
						
			# lecture du bouton 2
			if GPIO.input(SWITCH_2) == 0: 	
				SWITCH_2_PRESSED = True	
				time.sleep(SwitchReleaseTime)
				
			# lecture du bouton 3	
			if GPIO.input(SWITCH_3) == 0: 	
				PwButtonStart = timer()
				while GPIO.input(SWITCH_3) == 0:
					time.sleep(0.1)
					duree = timer() - PwButtonStart
					if duree > 1: 
						SWITCH_3_PRESSED = False
						SWITCH_3_LONG_PRESSED = True
						time.sleep(SwitchReleaseTime)
						break; # sortie du process
					else: 
						SWITCH_3_PRESSED = True
						time.sleep(SwitchReleaseTime)	
						
			# lecture du bouton 4	
			if GPIO.input(SWITCH_4) == 0: 	
				PwButtonStart = timer()
				while GPIO.input(SWITCH_4) == 0:
					time.sleep(0.1)
					duree = timer() - PwButtonStart
					if duree > 1: 
						SWITCH_4_LONG_PRESSED = True
						time.sleep(SwitchReleaseTime)
					else: 
						SWITCH_4_PRESSED = True
						time.sleep(SwitchReleaseTime)
						
				time.sleep(SwitchReleaseTime)
			time.sleep(0.001)


def AllLEDOff():
	GPIO.output(LED1, GPIO.LOW)
	GPIO.output(LED2, GPIO.LOW)
	GPIO.output(LED3, GPIO.LOW)
	GPIO.output(LED4, GPIO.LOW)
	GPIO.output(LED0, GPIO.LOW)


#### Fonction qui convertit une chaine en tableau
def StrToTrack(chaine):
	Track = []
	for i in chaine:
		if i == 'x':
			Track.append(1)
		if i == '-':
			Track.append(0)	
		if i == 'o':
			Track.append(2)					
	return Track

### Classe permettant de créer un objet son WAV en memoire et définir son volume	
class Sample:
	def __init__(self,path,track):
		self.Samples = []
		cfg = configparser.SafeConfigParser()
		cfg.read(path) 
		wavPath = KITS_FOLDER + cfg.get('kit','kit')  + "/" + cfg.get('kit',track) + "/"
		volume = cfg.getfloat('volume',track)
		wavList = os.listdir(wavPath) 
		for wav in wavList:
			sound = pygame.mixer.Sound(wavPath + wav)
			sound.set_volume(volume)
			self.Samples.append(sound)	
		self.nbSamples = len(self.Samples)
	def getsample(self):
		return self.Samples[randint(0, self.nbSamples -1)]
	def Play(self,Channel):
		pygame.mixer.Channel(Channel).play(self.getsample())

### Classe Pattern	
class Pattern:
	def __init__(self,path,PatternName):
		self.Name = PatternName
		self.Tracks = []
		self.NbMesure = 0
		cfg = configparser.SafeConfigParser()
		cfg.read(path) 
		for trck in cfg.options(PatternName):
			self.Tracks.append(StrToTrack(cfg.get(PatternName, trck)))
		self.NbMesure = len(self.Tracks[0])
	def getHit(self,trackID,curseur):
		return self.Tracks[trackID-1][curseur-1]
	def getNbMesure (self):
		return self.NbMesure 
	def getName(self):
		return self.Name

## Classe LCD
class LCD_Display(Thread):

	def __init__(self):
		Thread.__init__(self)

		self.LCD = lcddriver.lcd()
		self.current_message1 =""
		self.last_message1 =""
		self.current_message2 =""
		self.last_message2 =""
		self.row1 = 1
		self.row2 = 1
		self.empty = "                "
	
	def run(self):
		global curseur
		self.display()

	def display(self):
		global curseur
		while True:
			if self.current_message1 != self.last_message1:
				self.LCD.lcd_display_string(self.current_message1 + self.empty, 1)
				self.last_message1 = self.current_message1
				
			if self.current_message2 != self.last_message2:
				self.LCD.lcd_display_string(self.current_message2 + self.empty, 2)
				self.last_message2 = self.current_message2		

			time.sleep(0.1)
		
	def SetMessage(self,Message,Row):
		if Row == 1 : self.current_message1 = Message
		if Row == 2 : self.current_message2 = Message
		
	def Clear(self):
		self.LCD.lcd_clear()
		
def GetPatternName(ID):
	if ID == 0 : return "Introduction"
	if ID == 1 : return "Pattern 1"
	if ID == 2 : return "Pattern 2"
	if ID == 3 : return "Pattern 3"
	if ID == 4 : return "Outro"

		
#########################################################################################	
#########################################################################################
if __name__ == '__main__':
	os.system("/opt/vc/bin/vcgencmd measure_temp")
	
	# Initialise le lecteur de fichier Rhytm
	cfg = configparser.SafeConfigParser()
	
	# Initialise les GPIO
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False) #On désactive les messages d'alerte
	GPIO.setup(SWITCH_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(SWITCH_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(SWITCH_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(SWITCH_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(ROTARY_1_C, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(ROTARY_1_D, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(ROTARY_1_S, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(LED0, GPIO.OUT)
	GPIO.setup(LED1, GPIO.OUT)
	GPIO.setup(LED2, GPIO.OUT)
	GPIO.setup(LED3, GPIO.OUT)
	GPIO.setup(LED4, GPIO.OUT)
	
	#Initialise l'ecran lcd
	#LCD = I2C_LCD_driver.lcd()
	
	# Lancement des sous processus
	GPIOThread = GPIOReader()
	GPIOThread.start()
	LCD = LCD_Display()
	LCD.start()
	curseur = 1
	Rhythm = ""
	Running = False
	RhythmID = 0
	LCD.Clear()
	#LCD.SetMessage("  PiBeatBuddy   ",1,)
	#LCD.SetMessage("  Pi zero inside ",2,)

	os.system("amixer set 'PCM' 95%   >/dev/null 2>&1")	
	
	################################  BOUCLE PRINCIPALE   ###################################	
	while True: # Boucle principale du programme
		print ("Presser le bouton 4 pour démarrer la lecture")
		# si la lecture est en pause, attente de la reprise
		####################### BOUCLE DE CHARGEMENT  ##############################	
		# Parcours le répertoire Rythmes pour trovuer les fichiers
		RhythmList = os.listdir(RHYTHM_FOLDER)
		Rhythms = []
		for File in RhythmList:
			cfg.read(RHYTHM_FOLDER + File)
			Rhythms.append([cfg.get('default', 'title'),cfg.get('default', 'bpm'),File])
	
		# Affichage du premier rythme trouvé
		LCD.SetMessage(Rhythms[RhythmID][0],1,)
		LCD.SetMessage("Tempo: " + Rhythms[RhythmID][1],2,)
		
		while Running == False:
			if SWITCH_4_PRESSED: Running = True 
			# si on tourne le bouton, navigation entre les rythmes
			if ROTARY_1_LEFT : 
				ROTARY_1_LEFT = False 
				RhythmID += 1
				if RhythmID > len(Rhythms) - 1 : RhythmID = 0
				LCD.SetMessage(Rhythms[RhythmID][0],1,)
				LCD.SetMessage("Tempo: " + Rhythms[RhythmID][1],2,)
			if ROTARY_1_RIGHT : 
				ROTARY_1_RIGHT = False
				RhythmID -= 1
				if RhythmID < 0 : RhythmID = len(Rhythms) - 1
				LCD.SetMessage(Rhythms[RhythmID][0],1,)
				LCD.SetMessage("Tempo: " + Rhythms[RhythmID][1],2,)
			# si on clique sur le bouton, demarrage de la lecture
			if ROTARY_1_CLICK :
				ROTARY_1_CLICK = False
				Running = True
			
			time.sleep(0.2)
			
		RHYTHM_PATH = RHYTHM_FOLDER + Rhythms[RhythmID][2]
		print ("Lancement de " + Rhythms[RhythmID][0])
		
		LCD.SetMessage("C'est parti !",2,)
		############################################################################
		# Initialise le moteur audio
		pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
		pygame.mixer.set_num_channels(16)
	
		#LCD.lcd_clear()
		AllLEDOff()	
		cfg.read(RHYTHM_PATH)
		# Contruit le tempo
		tempo = 60.0 / int(cfg.get('default', 'bpm')) / 4
		# Compte le nombre de temps dans une mesure
		StepByMesure = len((cfg.get('transition', 'Track1')).replace('|',''))
		print ("Temps par mesure: " + str(StepByMesure))
		
		# Charge les Pattern en memoire		
		P_intro = Pattern(RHYTHM_PATH,"intro")
		P_pattern1 = Pattern(RHYTHM_PATH,"pattern1")
		P_pattern2 = Pattern(RHYTHM_PATH,"pattern2")
		P_pattern3 = Pattern(RHYTHM_PATH,"pattern3")
		P_outtro = Pattern(RHYTHM_PATH,"outtro")
		P_transition = Pattern(RHYTHM_PATH,"transition")
		PatternList = [P_intro,P_pattern1,P_pattern2,P_pattern3,P_outtro,P_transition]
		
		# Charge les samples WAV en memoire		
		kick 		= Sample(RHYTHM_PATH,"Track1")
		snare 		= Sample(RHYTHM_PATH,"Track2")
		hihat_foot 	= Sample(RHYTHM_PATH,"Track3")
		hihat_open 	= Sample(RHYTHM_PATH,"Track4")
		hihat_closed= Sample(RHYTHM_PATH,"Track5")
		hitom 		= Sample(RHYTHM_PATH,"Track6")
		mitom 		= Sample(RHYTHM_PATH,"Track7")
		lotom 		= Sample(RHYTHM_PATH,"Track8")
		crash 		= Sample(RHYTHM_PATH,"Track9")
		ride 		= Sample(RHYTHM_PATH,"Track10")
		
		# Reinitialise les valeurs des boutons
		SWITCH_1_PRESSED = False	
		SWITCH_2_PRESSED = False
		SWITCH_3_PRESSED = False
		SWITCH_4_PRESSED = False
		SWITCH_1_LONG_PRESSED = False
		SWITCH_3_LONG_PRESSED = False
		SWITCH_4_LONG_PRESSED = False
		
		#initialise les variables
		ActivePatternID = 0
		NextPatternID = 1
		curseur = 1
		StepTracker = 1
		WaitForTransition = False
		WaitForPause = False 
		WaitForPlayback = False
		PlayCymbalAfterTransition = False
		TempoLedState = False
		Playing = True
		####################### BOUCLE DE LECTURE  #########################
		while Running:
			################# Gestion des Led  #################
			
			if ((StepTracker-1) % 2) == 0 : 
				if TempoLedState == True : 
					GPIO.output(LED0, GPIO.LOW)
					TempoLedState = False	
				else:
					GPIO.output(LED0, GPIO.HIGH)
					TempoLedState = True

			if StepTracker == 1: GPIO.output(LED1, GPIO.HIGH)
			if StepTracker == StepByMesure / 4 + 1 : GPIO.output(LED2, GPIO.HIGH)
			if StepTracker == StepByMesure / 2 + 1 : GPIO.output(LED3, GPIO.HIGH)
			if StepTracker == StepByMesure / 4 * 3 + 1 : GPIO.output(LED4, GPIO.HIGH)
			if StepTracker == StepByMesure - 1 : AllLEDOff()
			
			################  Gestion du Tempo ##################
			if ROTARY_1_LEFT: 
				BPM += 5
				ROTARY_1_LEFT = False
			if ROTARY_1_RIGHT: 
				BPM -= 5
				ROTARY_1_RIGHT = False
			print BPM


			#tempo = 60.0 / BPM / 4








			#####################################################

			#print str(curseur)
			if Playing:
				if PatternList[ActivePatternID].getHit(1,StepTracker):  kick.Play(1) #pygame.mixer.Channel(0).play(kick.getsample())
				if PatternList[ActivePatternID].getHit(2,StepTracker):  snare.Play(2)
				if PatternList[ActivePatternID].getHit(3,StepTracker):  hihat_foot.Play(3)
				if PatternList[ActivePatternID].getHit(4,StepTracker):  hihat_open.Play(3)
				if PatternList[ActivePatternID].getHit(5,StepTracker):  hihat_closed.Play(3)
				if PatternList[ActivePatternID].getHit(6,StepTracker):  hitom.Play(4)
				if PatternList[ActivePatternID].getHit(7,StepTracker):  mitom.Play(5)
				if PatternList[ActivePatternID].getHit(8,StepTracker):  lotom.Play(6)
				if PatternList[ActivePatternID].getHit(9,StepTracker):  crash.Play(7)
				if PatternList[ActivePatternID].getHit(10,StepTracker): ride.Play(8)
				
				if PlayCymbalAfterTransition==True and StepTracker == 1 : 
					crash.Play(7)
					print ("crash cymbal")
					PlayCymbalAfterTransition = False		
				#curseur +=1
							
			################################################				
			
			if StepTracker == 1: LCD.SetMessage(GetPatternName(ActivePatternID),2)
			StepTracker +=1
			
			######### Si fin de mesure est atteinte ##########

			
			if StepTracker > StepByMesure:  #Si fin de mesure atteinte
				StepTracker = 1 # retour au début
				
				if WaitForPause == True :# Pause en fin de mesure
					WaitForPause = False
					Playing = False # mute le playback
					print ("Mise en pause")
				if ActivePatternID == 4: #Fin de lecture -Outtro
					print ("Fin du morceau")
					Playing = False
					Running = False 
					WaitForTransition = False
				ActivePatternID = NextPatternID 
				
			####### Si une transition est en attente #########
			
			if WaitForTransition and StepTracker > StepByMesure / 4 * 3 :
				print ("Début de transition")
				WaitForTransition = False
				ActivePatternID = 5 # active la Pattern transition
				PlayCymbalAfterTransition = True
				
			### Si une reprise de la lecture est en attente ####
			
			if WaitForPlayback and StepTracker > StepByMesure / 4 * 3:
				print ("Début de reprise de la lecture")
				WaitForPlayback = False
				WaitForTransition = True
				Playing = True
				
			########## Si le bouton 1 est pressé ############
			
			if SWITCH_1_PRESSED: 
				print ("Pattern 1 en attente")
				SWITCH_1_PRESSED = False
				NextPatternID = 1	
				LCD.SetMessage("> " + GetPatternName(NextPatternID) + "...",2,)
				if Playing : WaitForTransition = True # Si en playback
				else : WaitForPlayback = True # Si en pause
				
			if SWITCH_1_LONG_PRESSED and ActivePatternID != 4 :
				print ("Outtro en attente")
				SWITCH_1_LONG_PRESSED = False
				SWITCH_1_PRESSED = False
				WaitForTransition = True
				NextPatternID = 4 # Enregistre l'outtro	
				LCD.SetMessage("> " + GetPatternName(NextPatternID)+ "...",2,)
				
			
			########## Si le bouton 2 est pressé ############
			
			if SWITCH_2_PRESSED: 
				print ("Pattern 2 en attente")

				SWITCH_2_PRESSED = False
				NextPatternID = 2
				if Playing : WaitForTransition = True # Si en playback
				else : WaitForPlayback = True # Si en pause
				LCD.SetMessage("> " + GetPatternName(NextPatternID)+ "...",2,)

				
			########## Si le bouton 3 est pressé ############
			
			if SWITCH_3_PRESSED: 
				print ("Pattern 3 en attente")
				LCD.SetMessage("Pattern 3",2,)
				SWITCH_3_PRESSED = False
				NextPatternID = 3
				if Playing : WaitForTransition = True # Si en playback
				else : WaitForPlayback = True # Si en pause
				LCD.SetMessage("> " + GetPatternName(NextPatternID)+ "...",2,)

						
			if SWITCH_3_LONG_PRESSED:
				print ("!!EXIT!!")
				LCD.SetMessage(" Arghhhh !!     ",2,)
				#LCD.lcd_clear()
				AllLEDOff()
				GPIO.output(LED1, GPIO.LOW)
				pygame.quit()
				os.system("killall python")	
				sys.exit()				

			########## Si le bouton 4 est pressé ############
			
			if SWITCH_4_PRESSED:
				SWITCH_4_PRESSED = False
				WaitForTransition = True
				if Playing :  # Si le playback est actif
					if WaitForPause == False: 
						print ("Pause enregistrée")	
						LCD.SetMessage("> Pause...",2,)
						WaitForPause = True 
					else: 
						print ("Enregistrement de pause annulé")
						LCD.SetMessage("Pause annulee",2,)
						WaitForPause = False
				else:  # Si le playback est inactif
					print ("Reprise de la lecture enregistrée")
					LCD.SetMessage("> Reprise...",2,)
					WaitForPlayback = True
			
			if SWITCH_4_LONG_PRESSED:
				print ("Arrêt de la lecture")
				LCD.SetMessage(" STOP !",2,)
				SWITCH_4_LONG_PRESSED = False
				SWITCH_4_PRESSED = False
				AllLEDOff()
				Playing = False
				Running = False
				
			################################################
			time.sleep(tempo)
			
		pygame.quit() # Libère le moteur audio
		AllLEDOff()

		
		
		
		
	
	
	
	
	