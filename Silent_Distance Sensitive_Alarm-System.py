import RPi.GPIO as GPIO
import time
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
import math
from email.message import EmailMessage
import ssl
import smtplib


from time import sleep, strftime
from datetime import datetime

trigPin = 16
echoPin = 18
MAX_DISTANCE = 220          
timeOut = MAX_DISTANCE*60
ledPin = 11



def pulseIn(pin,level,timeOut):
    t0 = time.time()
    while(GPIO.input(pin) != level):
        if((time.time() - t0) > timeOut*0.000001):
            return 0;
    t0 = time.time()
    while(GPIO.input(pin) == level):
        if((time.time() - t0) > timeOut*0.000001):
            return 0;
    pulseTime = (time.time() - t0)*1000000
    return pulseTime
   
def getSonar():    
    GPIO.output(trigPin,GPIO.HIGH)  
    time.sleep(0.00001)    
    GPIO.output(trigPin,GPIO.LOW)
    pingTime = pulseIn(echoPin,GPIO.HIGH,timeOut)  
    distance = pingTime * 340.0 / 2.0 / 10000.0    
    return distance
   
def setup():
    GPIO.setmode(GPIO.BOARD)    
    GPIO.setup(trigPin, GPIO.OUT)  
    GPIO.setup(echoPin, GPIO.IN)
    GPIO.setup(ledPin, GPIO.OUT)
    GPIO.output(ledPin, GPIO.LOW)
    print ('using pin%d'%ledPin)
       

def get_time_now():    
    return datetime.now().strftime('    %H:%M:%S')


               

def loop():
   
    mcp.output(3,1)  
    lcd.begin(16,2)    
    while(True):        
        distance = getSonar()
        lcd.clear()
        lcd.message( 'DISTANCE: ')
        lcd.setCursor(0,1)
        lcd.message(f"{distance} cm")
        lcd.message( get_time_now() )
        time.sleep(1)
        if(distance > 0.1< distance <= 35):
            email_sender = "SENDING_EMAIL"
            email_password = "EMAILPASSWORD"
            email_reciever = "RECIEVING_EMAIL"
            #I used two of my emails
            subject = "Security System Alert!"
            body = """ Movement detected """
           
            em = EmailMessage()
            em["From"] = email_sender
            em["To"] = email_reciever
            em["Subject"] = subject
            em.set_content(body)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context = context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_reciever,em.as_string())
                GPIO.output(ledPin, GPIO.HIGH)
                print ('led turned on >>>')  
                time.sleep(0.2)                  
                GPIO.output(ledPin, GPIO.LOW)  
                print ('led turned off <<<')
                time.sleep(0.2)    
               
       
             

       
def destroy():
    lcd.clear()
    GPIO.cleanup()
   
PCF8574_address = 0x27  
PCF8574A_address = 0x3F  

try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print ('I2C Address Error !')
        exit(1)

lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

if __name__ == '__main__':
    print ('Program is starting ... ')
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
