#(I didn't have time to test this code with the raspberry pi due to too many assignments)


import cv2
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import pygame
import time
import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD


#Live Streaming


from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)
camera = cv2.VideoCapture(0)  # Initialize the camera

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Generate image frames

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
# Check if mobile device is connected to the same network as the Raspberry Pi. Open a web browser on your
# mobile device and enter the IP address of the Raspberry Pi followed by :5000 (e.g., http://192.168.0.10:5000).




#Facial Recognition, Alarm, Email, LCD Screen.



# Face recognition parameters
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer.yml')  # Load the trained model

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_USERNAME = ''#ENTER YOUR SENDER EMAIL  
EMAIL_PASSWORD = ''#ENTER YOUR EMAIL PASSWORD
RECIPIENT_EMAIL = ''#ENTER YOUR RECIEVING EMAIL
#TO SEND ALERTS TO MYSELF I USED TO OF MY EMAILS

# Pygame initialization for sound
pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("alarm_sound.mp3")

# LCD screen configuration
lcd_rs = 25
lcd_en = 24
lcd_d4 = 23
lcd_d5 = 17
lcd_d6 = 18
lcd_d7 = 22
lcd_columns = 16
lcd_rows = 2

# Initializing the LCD screen
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

# GPIO configuration for motion detection
pir_pin = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(pir_pin, GPIO.IN)

def send_email(image, message):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = message

    body = MIMEText(message)
    msg.attach(body)

    img = MIMEImage(image)
    msg.attach(img)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    server.sendmail(EMAIL_USERNAME, RECIPIENT_EMAIL, msg.as_string())
    server.quit()

def sound_alarm():
    pygame.mixer.music.play()

def recognize_face(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]
        id_, confidence = recognizer.predict(roi_gray)

        if confidence < 100:
            # Recognized face, do something with it
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, 'Person ID: {}'.format(id_), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Display on LCD screen
            lcd.clear()
            lcd.message('Motion detected,\nFace Recognized')
            lcd.message('\nPerson ID: {}'.format(id_))

            # Email notification
            if motion_detected:
                send_email('', 'Motion detected, Face Recognized')
        else:
            # Unrecognized face, send email and sound alarm
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, 'Unrecognized', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            # Display on LCD screen
            lcd.clear()
            lcd.message('Motion detected,\nFace Not Recognized')

            # Email notification
            if motion_detected:
                image_data = cv2.imencode('.jpg', frame)[1].tobytes()
                send_email(image_data, 'Unrecognized Person Detected')
                sound_alarm()

    return frame


def main():
    camera = cv2.VideoCapture(0)
    motion_detected = False

    while True:
        # Check for motion using PIR sensor
        if GPIO.input(pir_pin):
            motion_detected = True
            time.sleep(0.1)  # Debounce delay

        if motion_detected:
            ret, frame = camera.read()
            if not ret:
                break

            frame = recognize_face(frame)

            cv2.imshow('Face Recognition', frame)

            # Send email and display message on LCD screen if motion detected
            if cv2.waitKey(1) & 0xFF == ord('q'):
                image_data = cv2.imencode('.jpg', frame)[1].tobytes()
                if motion_detected:
                    if len(faces) > 0:
                        send_email(image_data, 'Motion detected, Face Recognized')
                    else:
                        send_email(image_data, 'Motion detected, Face Not Recognized')

                # Clear LCD screen
                lcd.clear()
                break

        else:
            # Display default message on LCD screen when no motion detected
            lcd.clear()
            lcd.message('No motion')

    camera.release()
    cv2.destroyAllWindows()
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd.clear()
        GPIO.cleanup()