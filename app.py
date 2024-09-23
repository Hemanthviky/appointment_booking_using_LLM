import streamlit as st
from datetime import datetime
from langchain_ollama import OllamaLLM
from question_generation import generate_question
from database import setup_database,book_appointment
from validation import nlp_validate,get_available_slots,suggest_next_available_date

model = OllamaLLM(model="llama3")

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