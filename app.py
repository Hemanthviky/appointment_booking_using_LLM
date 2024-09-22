import re
import spacy
import pyodbc
import streamlit as st
from datetime import datetime, timedelta
from connection import Conn
from langchain_ollama import OllamaLLM

model = OllamaLLM(model="llama3")

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
        return input_text.replace(" ", "").isalpha()
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
# Streamlit-based chatbot
def chatbot():
    # Setup database connection
    conn = setup_database()
    if not conn:
        st.error("Failed to connect to the database.")
        return
    
    # Session state to store conversation context and user data
    if 'context' not in st.session_state:
        st.session_state.context = 'start'
        st.session_state.user_data = {}
        st.session_state.conversation_history = []

    context = st.session_state.context
    user_data = st.session_state.user_data

    # Helper function to move to the next question only after successful submission
    def move_to_next_context():
        if st.session_state.context == 'start':
            st.session_state.context = 'email'
        elif st.session_state.context == 'email':
            st.session_state.context = 'phone'
        elif st.session_state.context == 'phone':
            st.session_state.context = 'age'
        elif st.session_state.context == 'age':
            st.session_state.context = 'appointment_date'
        elif st.session_state.context == 'appointment_date':
            st.session_state.context = 'slot_selection'

    # Display conversation history
    for entry in st.session_state.conversation_history:
        st.write(entry)

    # Process based on context
    if context == 'start':
        if 'name' not in user_data:
            question = generate_question("ask the name of the user")
            st.write(question)
            name = st.text_input("Enter your name:", key="name_input")
            if st.button("Submit Name") and name:
                if nlp_validate(name, "name"):
                    st.session_state.user_data['name'] = name
                    st.session_state.conversation_history.append(f"Bot: {question}")
                    st.session_state.conversation_history.append(f"You: {name}")
                    move_to_next_context()
                else:
                    st.write(generate_question("Invalid name. Please try again."))
        else:
            move_to_next_context()  # This prevents the question from being repeated

    if context == 'email':
        if 'email' not in user_data:
            question = generate_question("Ask the user's email", user_data)
            st.write(question)
            email = st.text_input("Enter your email:", key="email_input")
            if st.button("Submit Email") and email:
                if nlp_validate(email, "email"):
                    st.session_state.user_data['email'] = email
                    st.session_state.conversation_history.append(f"Bot: {question}")
                    st.session_state.conversation_history.append(f"You: {email}")
                    move_to_next_context()
                else:
                    st.write(generate_question("Invalid email. Please try again."))
        else:
            move_to_next_context()

    if context == 'phone':
        if 'phone' not in user_data:
            question = generate_question("Ask the user's phone number", user_data)
            st.write(question)
            phone = st.text_input("Enter your phone number:", key="phone_input")
            if st.button("Submit Phone") and phone:
                if nlp_validate(phone, "phone"):
                    st.session_state.user_data['phone'] = phone
                    st.session_state.conversation_history.append(f"Bot: {question}")
                    st.session_state.conversation_history.append(f"You: {phone}")
                    move_to_next_context()
                else:
                    st.write(generate_question("Invalid phone number. Please try again."))
        else:
            move_to_next_context()

    if context == 'age':
        if 'age' not in user_data:
            question = generate_question("Ask the user's age", user_data)
            st.write(question)
            age = st.text_input("Enter your age:", key="age_input")
            if st.button("Submit Age") and age:
                if nlp_validate(age, "age"):
                    st.session_state.user_data['age'] = age
                    st.session_state.conversation_history.append(f"Bot: {question}")
                    st.session_state.conversation_history.append(f"You: {age}")
                    move_to_next_context()
                else:
                    st.write(generate_question("Invalid age. Please enter a valid age."))
        else:
            move_to_next_context()

    if context == 'appointment_date':
        if 'appointment_date' not in user_data:
            question = generate_question("Ask the user's appointment date", user_data)
            st.write(question)
            
            appointment_date = st.date_input("Select appointment date:", 
                                             min_value=datetime.now().date(), 
                                             key="date_input")
            if st.button("Submit Date"):
                st.session_state.user_data['appointment_date'] = appointment_date.strftime("%Y-%m-%d")
                st.session_state.conversation_history.append(f"Bot: {question}")
                st.session_state.conversation_history.append(f"You: {appointment_date}")
                move_to_next_context()
        else:
            move_to_next_context()

    if context == 'slot_selection':
        if 'slot' not in user_data:
            available_slots = get_available_slots(st.session_state.user_data['appointment_date'], conn)
            if not available_slots:
                st.write(f"No available slots on {st.session_state.user_data['appointment_date']}.")
                
                # Suggest next available date
                next_date = suggest_next_available_date(datetime.strptime(st.session_state.user_data['appointment_date'], "%Y-%m-%d"), conn)
                if next_date:
                    st.write(f"The next available date is {next_date.strftime('%Y-%m-%d')} with slots: {', '.join(get_available_slots(next_date.strftime('%Y-%m-%d'), conn))}")
                else:
                    st.write("No available slots in the upcoming days.")
                
                # Prompt the user to select a new date
                question = "Please select a new date for your appointment:"
                st.write(question)
                new_date = st.date_input("Select a new appointment date:", 
                                         min_value=datetime.now().date(), 
                                         key="new_date_input")
                if st.button("Submit New Date"):
                    st.session_state.user_data['appointment_date'] = new_date.strftime("%Y-%m-%d")
                    st.session_state.conversation_history.append(f"Bot: {question}")
                    st.session_state.conversation_history.append(f"You: {new_date}")
                    st.session_state.context = 'slot_selection'
            else:
                question = "Please select a slot from the available options:"
                st.write(question)
                slot = st.selectbox("Select a slot:", available_slots, key="slot_selection")
                if st.button("Confirm Appointment"):
                    book_appointment(st.session_state.user_data['name'], st.session_state.user_data['email'], st.session_state.user_data['phone'], st.session_state.user_data['age'], st.session_state.user_data['appointment_date'], slot, conn)
                    st.session_state.conversation_history.append(f"Bot: {question}")
                    st.session_state.conversation_history.append(f"You: {slot}")
                    st.write("Your appointment is confirmed! for this date and time with user information")
                    st.session_state.context = 'done'

    if context == 'done':
        st.write("Thank you for using the appointment booking system!")

# Run the bot
if __name__ == "__main__":
    st.title("Appointment Booking Chatbot")
    chatbot()
