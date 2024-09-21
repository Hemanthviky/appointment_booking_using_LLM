from langchain_ollama import OllamaLLM

model = OllamaLLM(model="llama3")

def generate_question(context, user_data=None):
    prompt = f"""
    You are a friendly chatbot designed to help users book appointments. 
    Your goal is to ask the user relevant questions based on the current context, 
    guide them through the appointment process, and collect the necessary details in a clear and concise manner.
    If the user asks a question or makes a request unrelated to the booking process, 
    respond with: "I don't know, I can only assist you with appointment booking."
    Currently, the goal is to gather user input based on the following context: '{context}'.
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