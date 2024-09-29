from flask import Flask
from flask_cors import CORS
import pymysql
import schedule
import time
from threading import Thread

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='flask_app',
        cursorclass=pymysql.cursors.DictCursor
    )

# Create the database tables
def create_tables():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Patient (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                age INT,
                gender VARCHAR(10),
                contact VARCHAR(100),
                heart_rate INT,
                blood_pressure VARCHAR(20)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Reminder (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT,
                medication VARCHAR(100),
                dosage VARCHAR(100),
                time VARCHAR(10),
                FOREIGN KEY (patient_id) REFERENCES Patient(id)
            )
        """)
    connection.commit()
    connection.close()

create_tables()

def send_reminder(patient_id, medication, dosage, contact):
    # Logic to send reminder (e.g., via email, SMS, etc.)
    print(f"Reminder: Patient {patient_id} should take {dosage} of {medication}")
    # Example: send_telegram_message(contact, f"Reminder: Please take {dosage} of {medication}")

# Example: send_telegram_message(contact, f"Reminder: Please take {dosage} of {medication}")

def schedule_reminders():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT patient_id, medication, dosage, time FROM reminder")
        reminders = cursor.fetchall()
        for reminder in reminders:
            patient_id, medication, dosage, reminder_time = reminder['patient_id'], reminder['medication'], reminder['dosage'], reminder['time']
            cursor.execute("SELECT contact FROM Patient WHERE id = %s", (patient_id,))
            patient_contact = cursor.fetchone()
            if patient_contact:
                print(f"Scheduling reminder for patient {patient_id} at {reminder_time}")
                schedule.every().day.at(reminder_time).do(send_reminder, patient_id, medication, dosage, patient_contact['contact'])
            else:
                print(f"No contact found for patient {patient_id}")
    connection.close()

    # Start a thread to run the scheduler
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

schedule_reminders()


def send_telegram_message(contact, message):
    # Logic to send message via Telegram
    print(f"Telegram message sent to {contact}: {message}")

# Routes
@app.route('/api/patients', methods=['POST'])
def create_patient():
    data = request.get_json()
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Patient (name, age, gender, contact, heart_rate, blood_pressure, temperature, symptoms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['name'], data['age'], data['gender'], data['contact'], data['heart_rate'], data['blood_pressure'], data['temperature'], data['symptoms']))
    connection.commit()
    connection.close()
    return jsonify({"message": "Patient added successfully!"}), 201

@app.route('/api/patients', methods=['GET'])
def get_patients():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Patient")
        patients = cursor.fetchall()
    connection.close()
    return jsonify(patients), 200

@app.route('/api/reminders', methods=['POST'])
def create_reminder():
    data = request.get_json()
    patient_id = data.get('patient_id')
    medication = data.get('medication')
    dosage = data.get('dosage')
    time = data.get('time')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Check if patient_id exists
            cursor.execute("SELECT id FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            if not patient:
                return jsonify({'error': 'Patient ID does not exist'}), 400

            # Insert reminder
            sql = "INSERT INTO reminder (patient_id, medication, dosage, time) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (patient_id, medication, dosage, time))
            connection.commit()
            return jsonify({'message': 'Reminder created successfully'}), 201
    except pymysql.MySQLError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/sos', methods=['POST'])
def send_sos():
    data = request.get_json()
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Patient WHERE id = %s", (data['patient_id'],))
        patient = cursor.fetchone()
    connection.close()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    # Send SOS alert via Telegram
    send_telegram_message(patient['contact'], f"SOS Alert: {data['message']}")
    return jsonify({"message": "SOS alert sent!"}), 200

@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json()
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Appointment (patient_id, doctor_id, date, time)
            VALUES (%s, %s, %s, %s)
        """, (data['patient_id'], data['doctor_id'], data['date'], data['time']))
    connection.commit()
    connection.close()
    return jsonify({"message": "Appointment booked successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True)