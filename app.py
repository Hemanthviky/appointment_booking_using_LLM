import re
import spacy
import pyodbc
import streamlit as st
from datetime import datetime, timedelta
from connection import Conn
from langchain_ollama import OllamaLLM

model = OllamaLLM(model="llama3")


import spacy

def extract_name(text):
    # Load the English NLP model
    nlp = spacy.load("en_core_web_sm")
    # Process the text
    doc = nlp(text)
    # Try to extract a named entity labeled as 'PERSON'
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            return ent.text
    # If no 'PERSON' entity found, look for the first proper noun (PROPN)
    for token in doc:
        if token.pos_ == 'PROPN':
            return token.text
    # If no name found, return an empty string
    return ""


# Generate response using LLaMA
def generate_question(context, user_data=None):
    prompt = f"""
    You are a friendly chatbot designed to help users book appointments for Yaavar company. 
    Your goal is to ask the user relevant questions based on the current context, 
    currently, the goal is to gather user input based on the following context: '{context}'.
    """
    if user_data:
        prompt += f"\nThe following details have already been provided by the user: {user_data}."
    
    prompt += "\nBased on this context, ask the next appropriate question without displaying unnecessary details. Only provide the specific question."
    
    try:
        response = model.invoke(prompt)
        return response.strip()
    except Exception as e:
        print(f"Error generating question: {str(e)}")
        return "Error generating question."

# NLP validation for various fields
def nlp_validate(input_text, question):
    nlp = spacy.load("en_core_web_sm")
    
    if question == "name":
        return input_text.isalpha()
    elif question == "email":
        return re.match(r"[^@]+@[^@]+\.[^@]+", input_text)
    elif question == "phone":
        return re.match(r"\+?\d{10,15}", input_text)
    elif question == "age":
        return input_text.isdigit() and 0 < int(input_text) < 120
    elif question == "appointment_date":
        try:
            date = datetime.strptime(input_text, "%Y-%m-%d")
            return date >= datetime.now()
        except ValueError:
            return False
    return False

# Database setup
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

# Check if a slot is available on a specific date
def check_available_slot(date, slot, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE appointment_date = ? AND slot = ?", (date, slot))
    return cursor.fetchone() is None

# Get available slots for a specific date
def get_available_slots(date, conn):
    slots = ['10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00']
    available_slots = []

    for slot in slots:
        if check_available_slot(date, slot, conn):
            available_slots.append(slot)

    return available_slots

# Suggest the next available date
def suggest_next_available_date(start_date, conn):
    date = start_date
    while True:
        date += timedelta(days=1)
        if date.weekday() < 5:  # Monday to Friday
            if get_available_slots(date, conn):
                return date
    return None

# Book the appointment into the database
def book_appointment(name, email, phone, age, date, slot, conn):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (name, email, phone, age, appointment_date, slot)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, age, date, slot))
    conn.commit()

# Streamlit-based chatbot
def chatbot():
    # Setup database connection
    conn = setup_database()
    if not conn:
        st.error("Failed to connect to the database.")
        return
    
    # Initialize session state
    if 'context' not in st.session_state:
        st.session_state.context = 'start'
        st.session_state.user_data = {}
        st.session_state.conversation_history = []
        st.session_state.current_question = None

    # Display conversation history
    for entry in st.session_state.conversation_history:
        if entry['type'] == 'assistant':
            st.chat_message(name="assistant").write(entry['message'])
        elif entry['type'] == 'user':
            st.chat_message(name="user").write(entry['message'])

    # Process based on context
    if st.session_state.context == 'start':
        handle_start_context()
    elif st.session_state.context == 'email':
        handle_email_context()
    elif st.session_state.context == 'phone':
        handle_phone_context()
    elif st.session_state.context == 'age':
        handle_age_context()
    elif st.session_state.context == 'appointment_date':
        handle_appointment_date_context(conn)
    elif st.session_state.context == 'slot_selection':
        handle_slot_selection_context(conn)
    elif st.session_state.context == 'done':
        st.chat_message(name="assistant").write("Thank you for using the appointment booking system!")

def handle_start_context():
    if 'name' not in st.session_state.user_data:
        if st.session_state.current_question is None:
            question = generate_question("ask the name of the user")
            st.session_state.current_question = question
            st.chat_message(name="assistant").write(question)
        
        prompt = st.chat_input("Enter your name:")
        if prompt:
            if nlp_validate(prompt, "name"):
                st.session_state.user_data['name'] = prompt
                st.session_state.conversation_history.append({'type': 'assistant', 'message': st.session_state.current_question})
                st.session_state.conversation_history.append({'type': 'user', 'message': prompt})
                st.session_state.context = 'email'
                st.session_state.current_question = None
                st.rerun()
            else:
                st.chat_message(name="assistant").write("Invalid name. Please try again.")
    else:
        st.session_state.context = 'email'
        st.rerun()

def handle_email_context():
    if 'email' not in st.session_state.user_data:
        if st.session_state.current_question is None:
            question = generate_question("Ask the user's email", st.session_state.user_data)
            st.session_state.current_question = question
            st.chat_message(name="assistant").write(question)
        
        prompt = st.chat_input("Enter your email:")
        if prompt:
            if nlp_validate(prompt, "email"):
                st.session_state.user_data['email'] = prompt
                st.session_state.conversation_history.append({'type': 'assistant', 'message': st.session_state.current_question})
                st.session_state.conversation_history.append({'type': 'user', 'message': prompt})
                st.session_state.context = 'phone'
                st.session_state.current_question = None
                st.rerun()
            else:
                st.chat_message(name="assistant").write("Invalid email. Please try again.")
    else:
        st.session_state.context = 'phone'
        st.rerun()

def handle_phone_context():
    if 'phone' not in st.session_state.user_data:
        if st.session_state.current_question is None:
            question = generate_question("Ask the user's phone number", st.session_state.user_data)
            st.session_state.current_question = question
            st.chat_message(name="assistant").write(question)
        
        prompt = st.chat_input("Enter your phone number:")
        if prompt:
            if nlp_validate(prompt, "phone"):
                st.session_state.user_data['phone'] = prompt
                st.session_state.conversation_history.append({'type': 'assistant', 'message': st.session_state.current_question})
                st.session_state.conversation_history.append({'type': 'user', 'message': prompt})
                st.session_state.context = 'age'
                st.session_state.current_question = None
                st.rerun()
            else:
                st.chat_message(name="assistant").write("Invalid phone number. Please try again.")
    else:
        st.session_state.context = 'age'
        st.rerun()

def handle_age_context():
    if 'age' not in st.session_state.user_data:
        if st.session_state.current_question is None:
            question = generate_question("Ask the user's age", st.session_state.user_data)
            st.session_state.current_question = question
            st.chat_message(name="assistant").write(question)
        
        prompt = st.chat_input("Enter your age:")
        if prompt:
            if nlp_validate(prompt, "age"):
                st.session_state.user_data['age'] = prompt
                st.session_state.conversation_history.append({'type': 'assistant', 'message': st.session_state.current_question})
                st.session_state.conversation_history.append({'type': 'user', 'message': prompt})
                st.session_state.context = 'appointment_date'
                st.session_state.current_question = None
                st.rerun()
            else:
                st.chat_message(name="assistant").write("Invalid age. Please enter a valid age.")
    else:
        st.session_state.context = 'appointment_date'
        st.rerun()

def handle_appointment_date_context(conn):
    if 'appointment_date' not in st.session_state.user_data:
        if st.session_state.current_question is None:
            question = generate_question("Ask the user's appointment date", st.session_state.user_data)
            st.session_state.current_question = question
            st.chat_message(name="assistant").write(question)
        
        appointment_date = st.date_input("Select appointment date:", min_value=datetime.now().date())
        if st.button("Submit Date"):
            st.session_state.user_data['appointment_date'] = appointment_date.strftime("%Y-%m-%d")
            st.session_state.conversation_history.append({'type': 'assistant', 'message': st.session_state.current_question})
            st.session_state.conversation_history.append({'type': 'user', 'message': str(appointment_date)})
            st.session_state.context = 'slot_selection'
            st.session_state.current_question = None
            st.rerun()
    else:
        st.session_state.context = 'slot_selection'
        st.rerun()

def handle_slot_selection_context(conn):
    if 'slot' not in st.session_state.user_data:
        available_slots = get_available_slots(st.session_state.user_data['appointment_date'], conn)
        if not available_slots:
            st.chat_message(name="assistant").write(f"No available slots on {st.session_state.user_data['appointment_date']}.")
            
            next_date = suggest_next_available_date(datetime.strptime(st.session_state.user_data['appointment_date'], "%Y-%m-%d"), conn)
            if next_date:
                st.chat_message(name="assistant").write(f"The next available date is {next_date.strftime('%Y-%m-%d')} with slots: {', '.join(get_available_slots(next_date.strftime('%Y-%m-%d'), conn))}")
            else:
                st.chat_message(name="assistant").write("No available slots in the upcoming days.")
            
            new_date = st.date_input("Select a new appointment date:", min_value=datetime.now().date())
            if st.button("Submit New Date"):
                st.session_state.user_data['appointment_date'] = new_date.strftime("%Y-%m-%d")
                st.session_state.conversation_history.append({'type': 'assistant', 'message': "Please select a new date for your appointment:"})
                st.session_state.conversation_history.append({'type': 'user', 'message': str(new_date)})
                st.rerun()
        else:
            slot = st.selectbox("Select a slot:", available_slots)
            if st.button("Confirm Appointment"):
                book_appointment(st.session_state.user_data['name'], st.session_state.user_data['email'], st.session_state.user_data['phone'], st.session_state.user_data['age'], st.session_state.user_data['appointment_date'], slot, conn)
                st.session_state.conversation_history.append({'type': 'assistant', 'message': "Please select a slot from the available options:"})
                st.session_state.conversation_history.append({'type': 'user', 'message': slot})
                st.chat_message(name="assistant").write("Your appointment is confirmed!")
                st.session_state.context = 'done'
                st.rerun()
    else:
        st.session_state.context = 'done'
        st.rerun()

# Run the bot
if __name__ == "__main__":
    st.title("Appointment Booking Chatbot")
    chatbot()