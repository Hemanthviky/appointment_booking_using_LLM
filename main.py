from datetime import datetime, timedelta,date
from question_generation import generate_question
from validation import nlp_validate,get_available_slots,suggest_next_available_date
from database import setup_database,book_appointment

# Main chatbot logic for console
def chatbot():
    # Setup database connection
    conn = setup_database()
    if not conn:
        print("Failed to connect to the database.")
        return
    
    context = 'start'
    user_data = {}

    while context != 'done':
        if context == 'start':
            context = "Weclomes the user/customer to the Yaavar booking chat Bot and ask the name of the user"
            question = generate_question(context)
            print(f"Bot: {question}")
            while True:
                name = input("User: ")
                if nlp_validate(name, "name"):
                    user_data['name'] = name
                    context = 'email'
                    break
                else:
                    context = "The user has entered invalid name ask the user to enter the correct name"
                    question = generate_question(context)
                    print(f"Bot: {question}")

        elif context == 'email':
            context = "Ask the user's email"
            question = generate_question(context, user_data)
            print(f"Bot: {question}")
            while True:
                email = input("User: ")
                if nlp_validate(email, "email"):
                    user_data['email'] = email
                    context = 'phone'
                    break
                else:
                    context = "invalid email"
                    print(f"Bot: {generate_question(context)}")

        elif context == "phone":
            question = generate_question("Ask the user's phone number", user_data)
            print(f"Bot: {question}")
            while True:
                phone = input("User: ")
                if nlp_validate(phone, "phone"):
                    user_data['phone'] = phone
                    context = 'age'
                    break
                else:
                    context = "invalid phone number.ask user a valid phone number"
                    print(f"Bot: {generate_question(context)}")

        elif context == "age":
            question = generate_question("ask the user's age", user_data)
            print(f"Bot: {question}")
            while True:
                age = input("User: ")
                if nlp_validate(age, "age"):
                    user_data['age'] = age
                    context = 'a_date'
                    break
                else:
                    context = "invalid age and ask for valid age and in digits"
                    print(f"Bot: {generate_question(context)}")

        elif context == 'appointment_date':
            context = "ask the user to enter the appointment date in this format(YYYY-MM-DD)"
            question = generate_question(context, user_data)
            print(f"Bot: {question}")
            while True:
                appointment_date_input = input("User: ")
                if nlp_validate(appointment_date_input, "appointment_date") and datetime.strptime(appointment_date_input, "%Y-%m-%d").weekday() <= 5:
                    user_data['appointment_date'] = appointment_date_input
                    context = 'slot_selection'
                    break
                else:
                    today = date.today()
                    print(generate_question(f"""if the entered date {appointment_date_input} is lesser than today's date {today} ask the user to enter a future date 
                    else if the entered date is not as per the format required, ask the user to re-enter the date as per the format (YYYY-MM-DD)"""))

        elif context == 'slot_selection':
            available_slots = get_available_slots(user_data['appointment_date'], conn)
            if not available_slots:
                print(f"Bot: No available slots on {user_data['appointment_date']}. Suggesting the next available date...")
                next_date = suggest_next_available_date(datetime.strptime(user_data['appointment_date'], "%Y-%m-%d"), conn)
                if next_date:
                    print(f"Bot: The next available date is {next_date.strftime('%Y-%m-%d')} with slots: {', '.join(get_available_slots(next_date.strftime('%Y-%m-%d'), conn))}")
                else:
                    print("Bot: No available slots in the upcoming days.")
                continue
            
            print("Bot: Available slots: " + ", ".join(available_slots))
            while True:
                print("     Select a slot (format HH:MM)")
                slot = input("User: ")
                if slot in available_slots:
                    print(f"Bot: A slot is available at {slot} on {user_data['appointment_date']}. Would you like to confirm? (yes/no)")
                    confirm = input("User: ")
                    if confirm.lower() == 'yes':
                        book_appointment(user_data['name'], user_data['email'], user_data['phone'], user_data['age'], user_data['appointment_date'], slot, conn)
                        print("Bot: Your appointment is confirmed!")
                        context = 'done'
                    else:
                        context = 'done'
                    break
                else:
                    print("Bot: The selected slot is not available. Please choose another.")

# Run the bot
if __name__ == "__main__":
    chatbot()
