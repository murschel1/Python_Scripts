import requests
import time
import numpy as np

#MRU\
#import matplotlib.pyplot as plt
from scipy import interpolate as intp
#MRU/

import RPi.GPIO as GPIO
import Stepper as st
from subprocess import call

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(14, GPIO.OUT) #LED
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #START
#GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #STOP


def Get_SPD(IntTime):
	RS = requests.get('http://192.168.42.1/cgi-bin/setintegration.php?time='+str(IntTime))	# Read Light SPD
	print RS.text
	SPD = requests.get('http://192.168.42.1/cgi-bin/getspectrum.php')	# Read Light SPD
	data1 = SPD.text
	data2 = np.asarray(data1.split(' '))
	data3 = data2.astype(float)
	return data3.astype(int)

#def STOP(channel):
#	print "Pressed Stop Button" #18
#	call("sudo shutdown -h now", shell=True)

def START(channel):
	print "Pressed Start Button" #15
	ReadSPDs()

GPIO.add_event_detect(15, GPIO.RISING, callback=START, bouncetime=1000)
#GPIO.add_event_detect(18, GPIO.FALLING, callback=STOP, bouncetime=1000)

def ReadSPDs():
  IntTime = 100000 # 0.1 sec
  MAX_count = 15000
  MIN_count = 5000
  Delay = 1
  max_val = 10000
  collection_area_m2 = 0.119459/100 #cm2*(1 m2/100 cm2)

  GPIO.output(14, GPIO.LOW)

  #MRU\
  #Load STS calibration data
  caldata = np.loadtxt('STScalibration.txt',delimiter = '\t',dtype='str')

  #Convert STS calibration data to float
  caldata = caldata.astype(float)

  #Perform cubic spline interpolation on calibration data
  cubsp = intp.CubicSpline([x[0] for x in caldata],[x[1] for x in caldata],bc_type='natural')

  #Load STS spectrum wavelengths
  calwl = np.loadtxt('wavelengths.txt',dtype='float')

  #Calculate count conversion constants for STS spectrum wavelengths 
  CountConversionConstants = cubsp(calwl)
  #MRU/


  while 1:
	if (max_val > 15000):
		if (IntTime > 100000):
			IntTime = IntTime - 50000
	else:
		if (IntTime < 9900000):
			IntTime = IntTime + 50000
	st.Open()	# Open shutter
	time.sleep(1)
	data_SPD = Get_SPD(IntTime)
	max_val = np.max(data_SPD)
	print ('max val = %d'%max_val)
	print ('Int time = %d'%IntTime)

	st.Close()
	time.sleep(1)
	data_DARK = Get_SPD(IntTime)
	print ('max val_dark = %d'%np.max(data_DARK))

	FinalSPD = np.subtract(data_SPD, data_DARK)
	
	#MRU\

	#############################
	### Start conversion code ###
        #############################

	
	#Convert counts to uJ
	FinalSPDWattsm2 = np.multiply(FinalSPD,CountConversionConstants)
	print FinalSPDWattsm2

	#Convert uJ to uJ/s (= microwatts)
        FinalSPDWattsm2 = np.divide(FinalSPDWattsm2, np.divide(float(IntTime),1000000)) #1 sec = 1000000 microsecs
	print FinalSPDWattsm2

	#Convert microwatts to watts
        FinalSPDWattsm2 = np.divide(FinalSPDWattsm2, 1000000) 
	print FinalSPDWattsm2
        
	#Divide by collection area to get W/m2
	FinalSPDWattsm2 = np.divide(FinalSPDWattsm2, collection_area_m2)
	print FinalSPDWattsm2

        ###########################
	### End conversion code ###
        ###########################

        #MRU/

	CurrentTime = time.localtime()

	FileName = str(CurrentTime.tm_year) + '-' + str(CurrentTime.tm_mon) + '-' + \
		str(CurrentTime.tm_mday) + '->' + str(CurrentTime.tm_hour) + '-' + \
		str(CurrentTime.tm_min) + '-' + str(CurrentTime.tm_sec)+'.txt'
	print FileName
	FinalSPD[0] = IntTime
	np.savetxt('/mnt/SPDs/'+ FileName, FinalSPD)
	time.sleep(Delay)


	#MRU\

        #Save file with counts converted to Watts per m2
	FileNameWattsm2 = str(CurrentTime.tm_year) + '-' + str(CurrentTime.tm_mon) + '-' + \
		str(CurrentTime.tm_mday) + '->' + str(CurrentTime.tm_hour) + '-' + \
		str(CurrentTime.tm_min) + '-' + str(CurrentTime.tm_sec)+'-Wattsm2.txt'
	print FileNameWattsm2

	np.savetxt('/mnt/SPDs/'+ FileNameWattsm2, FinalSPDWattsm2)
	time.sleep(Delay)

	#MRU/

def main():
	GPIO.output(14, GPIO.HIGH)
#	ReadSPDs()
	while 1:
		time.sleep(10)



if __name__ == "__main__":
	main()
