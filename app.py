from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import schedule

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/flask_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

# Models
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    contact = db.Column(db.String(100))
    heart_rate = db.Column(db.Integer)
    blood_pressure = db.Column(db.String(20))
    temperature = db.Column(db.Float)
    symptoms = db.Column(db.String(200))

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    medication = db.Column(db.String(100))
    dosage = db.Column(db.String(50))
    time = db.Column(db.String(50))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    doctor_id = db.Column(db.Integer)
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))

# Create the database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/api/patients', methods=['POST'])
def create_patient():
    data = request.get_json()
    new_patient = Patient(
        name=data['name'],
        age=data['age'],
        gender=data['gender'],
        contact=data['contact'],
        heart_rate=data['heart_rate'],
        blood_pressure=data['blood_pressure'],
        temperature=data['temperature'],
        symptoms=data['symptoms']
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify({"message": "Patient added successfully!"}), 201

@app.route('/api/patients', methods=['GET'])
def get_patients():
    patients = Patient.query.all()
    return jsonify([{
        'id': patient.id,
        'name': patient.name,
        'age': patient.age,
        'gender': patient.gender,
        'contact': patient.contact,
        'heart_rate': patient.heart_rate,
        'blood_pressure': patient.blood_pressure,
        'temperature': patient.temperature,
        'symptoms': patient.symptoms,
    } for patient in patients]), 200

@app.route('/api/reminders', methods=['POST'])
def create_reminder():
    data = request.get_json()
    new_reminder = Reminder(
        patient_id=data['patient_id'],
        medication=data['medication'],
        dosage=data['dosage'],
        time=data['time']
    )
    db.session.add(new_reminder)
    db.session.commit()
    # Schedule the reminder (using schedule library)
    schedule_reminder(data['patient_id'], data['medication'], data['dosage'], data['time'])
    return jsonify({"message": "Reminder set successfully!"}), 201

@app.route('/api/sos', methods=['POST'])
def send_sos():
    data = request.get_json()
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    # Send SOS alert via Telegram
    send_telegram_message(patient.contact, f"SOS Alert: {data['message']}")
    return jsonify({"message": "SOS alert sent!"}), 200

@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json()
    new_appointment = Appointment(
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        date=data['date'],
        time=data['time']
    )
    db.session.add(new_appointment)
    db.session.commit()
    return jsonify({"message": "Appointment booked successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True)

import time
from threading import Thread

def send_reminder(patient_id, medication, dosage):
    # Logic to send reminder (e.g., via email, SMS, etc.)
    print(f"Reminder: Patient {patient_id} should take {dosage} of {medication}")

def schedule_reminder(patient_id, medication, dosage, reminder_time):
    # Schedule the reminder
    schedule.every().day.at(reminder_time).do(send_reminder, patient_id, medication, dosage)

    # Start a thread to run the scheduler
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.start()