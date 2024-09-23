# Appointment Booking System Using LLM

## Overview

This project is an appointment booking system that uses a Large Language Model (LLM) LLama3 for natural language interaction, allowing users to schedule appointments seamlessly. The system handles user inputs, manages availability, and confirms bookings. And used StreamLit for the the User Interface.

## Features

- **Natural Language Interaction**: Allows users to book appointments through conversational input.
- **Database Management**: Stores user data and manages schedules.
- **Dynamic Question Generation**: Collects information needed for bookings.

## File Structure

- `app.py`: Main application.
- `database.py`: Handles database operations.
- `question_generation.py`: Generates relevant questions for user interaction.
- `connection.py`: Used to create connection with MySQL.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Hemanthviky/appointment_booking_using_LLM.git
    ```
2. Navigate to the project folder:
    ```bash
    cd appointment_booking_using_LLM
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

Start the application using:
```bash
python app.py
```
![image](https://github.com/user-attachments/assets/cf7f93b7-8820-48f7-99a9-91db258ba76e)


## Future Improvements
- **Integration with real-world calendar services.
- **Multilingual support.
- **Enhanced natural language processing for more complex queries.
