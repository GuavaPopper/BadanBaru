from flask import Flask, render_template, Response, redirect, url_for
import cv2
import mediapipe as mp
import time
import math
import numpy as np
import os
import threading
import pyttsx3

app = Flask(__name__)

# Global variables
camera = None
face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
button_clicked = False
is_measuring_height = False

# Constants for face distance detection
Known_distance = 500  # centimeter
Known_width = 15.5    # centimeter
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (255, 0, 0)

# MediaPipe setup for body detection
mpPose = mp.solutions.pose
mpDraw = mp.solutions.drawing_utils
pose = mpPose.Pose()

# Text-to-speech function
def speak(audio):
    def speak_thread(text):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('rate', 150)
        engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
    
    # Start in a separate thread to not block the main thread
    threading.Thread(target=speak_thread, args=(audio,)).start()

# Face width calculation function
def face_data(image):
    face_width = 0
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)
    
    for (x, y, h, w) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), GREEN, 2)
        face_width = w
        
    return face_width

# Focal length finder function
def Focal_Length_Finder(measured_distance, real_width, width_in_rf_image):
    focal_length = (width_in_rf_image * measured_distance) / real_width
    return focal_length

# Distance estimation function
def Distance_finder(Focal_Length, real_face_width, face_width_in_frame):
    distance = (real_face_width * Focal_Length) / face_width_in_frame
    return distance

# Face detection generator function (from ex.py)
def generate_face_frames():
    global camera, button_clicked, is_measuring_height
    
    # Get focal length from reference image
    ref_image = cv2.imread("Ref_image.jpg")
    ref_image_face_width = face_data(ref_image)
    Focal_length_found = Focal_Length_Finder(Known_distance, Known_width, ref_image_face_width)
    
    camera = cv2.VideoCapture(0)
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Draw the button on frame
        cv2.rectangle(frame, (400, 30), (650, 70), BLUE, -1)
        cv2.rectangle(frame, (400, 30), (650, 70), BLACK, 2)
        cv2.putText(frame, "Lakukan Ukur Badan", (410, 55),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, WHITE, 2)

        # Face distance detection
        face_width_in_frame = face_data(frame)
        
        if face_width_in_frame != 0:
            Distance = Distance_finder(Focal_length_found, Known_width, face_width_in_frame)
            
            cv2.line(frame, (30, 30), (230, 30), RED, 32)
            cv2.line(frame, (30, 30), (230, 30), BLACK, 28)
            
            Distance = round(Distance)
            
            # Check if person is at correct distance
            if 330 <= Distance <= 360:
                cv2.putText(frame, "Perfect distance for measurement!", (30, 90),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, GREEN, 2)
            
            # Drawing Text on the screen
            cv2.putText(frame, f"Distance: {round(Distance,2)} cms", (30, 35),
                       cv2.FONT_HERSHEY_COMPLEX, 0.6, GREEN, 2)
        
        # Check if button was clicked (this will be handled via web interface)
        if button_clicked or is_measuring_height:
            # Release current stream
            if camera.isOpened():
                camera.release()
            break
            
        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Body detection generator function (from Body_Detection.py)
def generate_body_frames():
    global camera
    
    # Initialize camera if not already open
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
    
    ptime = 0
    
    while True:
        success, img = camera.read()
        if not success:
            break
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = pose.process(img_rgb)

        if result.pose_landmarks:
            mpDraw.draw_landmarks(img, result.pose_landmarks, mpPose.POSE_CONNECTIONS)
            h, w, c = img.shape
            cx1, cy1, cx2, cy2 = 0, 0, 0, 0

            for id, lm in enumerate(result.pose_landmarks.landmark):
                if id == 32 or id == 31:
                    cx1, cy1 = int(lm.x * w), int(lm.y * h)
                    cv2.circle(img, (cx1, cy1), 15, (0, 0, 0), cv2.FILLED)
                if id == 6:
                    cx2, cy2 = int(lm.x * w), int(lm.y * h)
                    cy2 += 20
                    cv2.circle(img, (cx2, cy2), 15, (0, 0, 0), cv2.FILLED)

            if cx1 and cy1 and cx2 and cy2:
                d = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
                di = round(d * 0.5)
                
                cv2.putText(img, "Height : ", (40, 70), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), thickness=2)
                cv2.putText(img, str(di), (180, 70), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 0), thickness=2)
                cv2.putText(img, "cms", (240, 70), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), thickness=2)

        # Add button to return to face detection
        cv2.rectangle(img, (400, 30), (650, 70), RED, -1)
        cv2.rectangle(img, (400, 30), (650, 70), BLACK, 2)
        cv2.putText(img, "Return to Face Detection", (410, 55),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, WHITE, 2)

        img = cv2.resize(img, (700, 500))
        ctime = time.time()
        fps = 1 / (ctime - ptime)
        ptime = ctime
        cv2.putText(img, "FPS : ", (40, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), thickness=2)
        cv2.putText(img, str(int(fps)), (160, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), thickness=2)
        
        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/face_detection')
def face_detection():
    global is_measuring_height, button_clicked
    button_clicked = False
    is_measuring_height = False
    return render_template('face_detection.html')

@app.route('/body_detection')
def body_detection():
    global is_measuring_height
    is_measuring_height = True
    speak("Starting body measurement")
    return render_template('body_detection.html')

@app.route('/video_feed_face')
def video_feed_face():
    return Response(generate_face_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_body')
def video_feed_body():
    return Response(generate_body_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/switch_to_body')
def switch_to_body():
    global button_clicked
    button_clicked = True
    return redirect(url_for('body_detection'))

@app.route('/switch_to_face')
def switch_to_face():
    return redirect(url_for('face_detection'))

if __name__ == '__main__':
    app.run(debug=True) 