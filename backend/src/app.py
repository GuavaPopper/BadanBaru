from flask import Flask, render_template, Response, redirect, url_for, jsonify, request, flash
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO
import cv2
import mediapipe as mp
import time
import math
import numpy as np
import os
import threading
import pyttsx3
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, 
    template_folder='../../templates',  # Adjust template path
    static_folder='../../static'        # Adjust static path
)

# Email configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Get the absolute path to the database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'measurements.db')

print(f"Using database at: {DB_PATH}")  # Debug print to verify path

# Database functions
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_measurements():
    conn = get_db_connection()
    measurements = conn.execute('SELECT * FROM measurements ORDER BY timestamp DESC').fetchall()
    conn.close()
    return [dict(row) for row in measurements]

def get_latest_measurement():
    conn = get_db_connection()
    measurement = conn.execute('SELECT * FROM measurements ORDER BY timestamp DESC LIMIT 1').fetchone()
    conn.close()
    return dict(measurement) if measurement else None

# Global variables
camera = None
cascade_path = os.path.join(os.path.dirname(BASE_DIR), "config", "haarcascade_frontalface_default.xml")
print(f"Loading cascade classifier from: {cascade_path}")  # Debug print

if not os.path.exists(cascade_path):
    raise FileNotFoundError(f"Cascade classifier file not found at: {cascade_path}")

face_detector = cv2.CascadeClassifier(cascade_path)
if face_detector.empty():
    raise ValueError("Error loading cascade classifier")

button_clicked = False
is_measuring_height = False

# Constants for face distance detection
Known_distance = 500  # centimeter
Known_width = 15.5    # centimeter
DEFAULT_FOCAL_LENGTH = 500  # Default focal length when no reference image is available
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
    
    # Use default focal length since reference image might not be available
    Focal_length_found = DEFAULT_FOCAL_LENGTH
    
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Could not open camera")
        return
    
    while True:
        success, frame = camera.read()
        if not success:
            print("Error: Could not read frame")
            break
        
        # Face distance detection
        face_width_in_frame = face_data(frame)
        
        if face_width_in_frame != 0:
            Distance = Distance_finder(Focal_length_found, Known_width, face_width_in_frame)
            Distance = round(Distance)
            
            # Draw distance indicator
            cv2.line(frame, (30, 30), (230, 30), RED, 32)
            cv2.line(frame, (30, 30), (230, 30), BLACK, 28)
            
            # Check if person is at correct distance
            if 330 <= Distance <= 360:
                cv2.putText(frame, "Perfect distance for measurement!", (30, 90),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, GREEN, 2)
            
            # Drawing Text on the screen
            cv2.putText(frame, f"Distance: {Distance} cms", (30, 35),
                       cv2.FONT_HERSHEY_COMPLEX, 0.6, GREEN, 2)
        
        # Check if button was clicked
        if button_clicked or is_measuring_height:
            if camera.isOpened():
                camera.release()
            break
        
        try:
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Error: Could not encode frame")
                continue
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error in frame processing: {e}")
            continue

# Body detection generator function (from Body_Detection.py)
def generate_body_frames():
    global camera
    
    # Initialize camera if not already open
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
    
    ptime = 0
    measurements_captured = False
    current_measurements = {
        "height": 0,
        "shoulder_width": 0,
        "chest_circumference": 0,
        "waist_circumference": 0,
        "timestamp": "",
    }
    
    # Calibration factors
    HEIGHT_CALIBRATION_FACTOR = 0.5 + 0.10  # Adjusted to add 7cm
    SHOULDER_CALIBRATION_FACTOR = 0.264
    CHEST_CIRCUMFERENCE_FACTOR = 2.5
    WAIST_CIRCUMFERENCE_FACTOR = 2.5
    
    # Initialize countdown variables
    start_time = time.time()
    countdown_started = False
    countdown_duration = 10  # seconds
    
    # Initialize database connection
    db_conn = sqlite3.connect(DB_PATH)
    cursor = db_conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            height REAL,
            shoulder_width REAL,
            chest_circumference REAL,
            waist_circumference REAL
        )
    ''')
    db_conn.commit()
    
    while True:
        success, img = camera.read()
        if not success:
            break
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = pose.process(img_rgb)

        if result.pose_landmarks:
            mpDraw.draw_landmarks(img, result.pose_landmarks, mpPose.POSE_CONNECTIONS)
            h, w, c = img.shape
            
            # Store landmarks
            landmarks = {}
            for id, lm in enumerate(result.pose_landmarks.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmarks[id] = (cx, cy)
            
            # Measure shoulder width
            if 11 in landmarks and 12 in landmarks:
                shoulder_width = math.sqrt(
                    (landmarks[12][0] - landmarks[11][0]) ** 2 + 
                    (landmarks[12][1] - landmarks[11][1]) ** 2
                )
                shoulder_width_cm = round(shoulder_width * SHOULDER_CALIBRATION_FACTOR)
                cv2.line(img, landmarks[11], landmarks[12], (0, 255, 0), 2)
                cv2.putText(img, f"Shoulder: {shoulder_width_cm}cm", (40, 110), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
                current_measurements["shoulder_width"] = shoulder_width_cm

            # Estimate chest circumference
            if 11 in landmarks and 12 in landmarks:
                chest_width = math.sqrt(
                    (landmarks[12][0] - landmarks[11][0]) ** 2 + 
                    (landmarks[12][1] - landmarks[11][1]) ** 2
                )
                chest_circumference = round(chest_width * SHOULDER_CALIBRATION_FACTOR * CHEST_CIRCUMFERENCE_FACTOR)
                cv2.putText(img, f"Chest: {chest_circumference}cm", (40, 150), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
                current_measurements["chest_circumference"] = chest_circumference

            # Estimate waist circumference
            if 23 in landmarks and 24 in landmarks:
                waist_width = math.sqrt(
                    (landmarks[24][0] - landmarks[23][0]) ** 2 + 
                    (landmarks[24][1] - landmarks[23][1]) ** 2
                )
                waist_circumference = round(waist_width * SHOULDER_CALIBRATION_FACTOR * WAIST_CIRCUMFERENCE_FACTOR)
                cv2.line(img, landmarks[23], landmarks[24], (0, 255, 0), 2)
                cv2.putText(img, f"Waist: {waist_circumference}cm", (40, 190), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
                current_measurements["waist_circumference"] = waist_circumference

            # Measure height
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
                height_cm = round(d * HEIGHT_CALIBRATION_FACTOR)
                cv2.putText(img, "Height : ", (40, 70), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(img, str(height_cm), (180, 70), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)
                cv2.putText(img, "cms", (240, 70), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                current_measurements["height"] = height_cm

            # Handle countdown and measurement capture
            if not countdown_started:
                countdown_started = True
                start_time = time.time()
            
            elapsed_time = time.time() - start_time
            remaining_time = max(0, countdown_duration - int(elapsed_time))
            
            if remaining_time > 0:
                # Display countdown
                cv2.putText(img, f"Capturing in: {remaining_time}s", (40, 400), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
            elif not measurements_captured:
                # Capture measurements
                current_measurements["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO measurements (timestamp, height, shoulder_width, chest_circumference, waist_circumference)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    current_measurements["timestamp"],
                    current_measurements["height"],
                    current_measurements["shoulder_width"],
                    current_measurements["chest_circumference"],
                    current_measurements["waist_circumference"]
                ))
                db_conn.commit()
                measurements_captured = True

            # Display capture status
            if measurements_captured:
                cv2.putText(img, "Measurements saved to database!", (40, 440), 
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)

        img = cv2.resize(img, (700, 500))
        ctime = time.time()
        fps = 1 / (ctime - ptime)
        ptime = ctime
        cv2.putText(img, "FPS : ", (40, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
        cv2.putText(img, str(int(fps)), (160, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
        
        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # Clean up
    db_conn.close()
    if camera.isOpened():
        camera.release()

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'type': 'connection', 'data': 'Connected successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('error')
def handle_error(error):
    print(f'Socket.IO error: {error}')

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
    latest_measurement = get_latest_measurement()
    return render_template('body_detection.html', last_measurement=latest_measurement)

@app.route('/measurements')
def measurements():
    all_measurements = get_all_measurements()
    latest_measurement = get_latest_measurement()
    return render_template('measurements.html', 
                         measurements=all_measurements,
                         latest=latest_measurement)

@app.route('/api/measurements')
def api_measurements():
    measurements = get_all_measurements()
    return jsonify(measurements)

@app.route('/api/latest-measurement')
def api_latest_measurement():
    measurement = get_latest_measurement()
    return jsonify(measurement if measurement else {})

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

def generate_pdf(measurements):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add title
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, 750, "Body Measurements Report")
    
    # Add timestamp
    p.setFont("Helvetica", 12)
    p.drawString(50, 720, f"Generated on: {measurements['timestamp']}")
    
    # Add measurements
    p.setFont("Helvetica-Bold", 14)
    y = 650
    for label, value in [
        ("Height", f"{measurements['height']} cm"),
        ("Shoulder Width", f"{measurements['shoulder_width']} cm"),
        ("Chest Circumference", f"{measurements['chest_circumference']} cm"),
        ("Waist Circumference", f"{measurements['waist_circumference']} cm")
    ]:
        p.drawString(50, y, f"{label}:")
        p.setFont("Helvetica", 14)
        p.drawString(200, y, value)
        p.setFont("Helvetica-Bold", 14)
        y -= 30
    
    p.save()
    buffer.seek(0)
    return buffer

@app.route('/email_form')
def email_form():
    measurements = get_latest_measurement()
    if not measurements:
        flash('No measurements available', 'error')
        return redirect(url_for('measurements'))
    return render_template('email_form.html', measurements=measurements)

@app.route('/send_measurements', methods=['POST'])
def send_measurements():
    email = request.form.get('email')
    if not email:
        flash('Please provide an email address', 'error')
        return redirect(url_for('email_form'))
    
    measurements = get_latest_measurement()
    if not measurements:
        flash('No measurements available', 'error')
        return redirect(url_for('email_form'))
    
    try:
        # Generate PDF
        pdf_buffer = generate_pdf(measurements)
        
        # Create email
        msg = Message(
            'Your Body Measurements Report',
            recipients=[email]
        )
        msg.body = f"""
        Hello,

        Please find attached your body measurements report.

        Height: {measurements['height']} cm
        Shoulder Width: {measurements['shoulder_width']} cm
        Chest Circumference: {measurements['chest_circumference']} cm
        Waist Circumference: {measurements['waist_circumference']} cm

        Measured on: {measurements['timestamp']}

        Best regards,
        Body Measurement System
        """
        
        # Attach PDF
        msg.attach(
            'measurements.pdf',
            'application/pdf',
            pdf_buffer.getvalue()
        )
        
        # Send email
        mail.send(msg)
        
        flash('Measurements sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')
    
    return redirect(url_for('email_form'))

if __name__ == '__main__':
    app.run(debug=True) 