import pyodbc
from connection import Conn
import pyodbc
from datetime import datetime,date
def setup_database():
    try:
        conn = Conn.connection
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(15),
                age INT,
                appointment_date DATE,
                slot TIME
            )
        ''')
        conn.commit()
        return conn
    except pyodbc.Error as e:
        print(f"Database error: {str(e)}")
        return None
    
# Book the appointment into the database
def book_appointment(name, email, phone, age, appointment_date, slot, conn):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (name, email, phone, age, appointment_date, slot)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, age, appointment_date, slot))
    conn.commit()

