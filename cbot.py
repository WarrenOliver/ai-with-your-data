import os
import pickle
import json
import openai

import credentials
from flask import request

from google.auth.transport.requests import Request

from google_auth_oauthlib.flow import InstalledAppFlow
from llama_index import GPTVectorStoreIndex, download_loader, ServiceContext, StorageContext, load_index_from_storage

from langchain.chat_models import ChatOpenAI
from llama_index.chat_engine import SimpleChatEngine
from models import SessionModel

from models import SessionModel, db

service_context = ServiceContext.from_defaults(llm=ChatOpenAI(temperature=0.))


__name__ = 'cbot'

openai_api_key = os.environ.get('OPENAI_API_KEY')
openai.api_key = openai_api_key

clarity_dump = '1pd-7zR65vOvQ-ADWbcX2UGKA2va42LWnRoM1x90Dhcw'
clarity_dump_p2 = '1V4WAoo1EculvngkPJ11LbVjFJVA6DVERSBqB099Fxq8'
md_mc_journals = '1eM6Nv9wAkkKARstZClnCfoL7K3fGioPHNdOGCJgDlQY'

def is_file_empty(file_path):
    return os.path.getsize(file_path) == 0

def authorize_gsheets():
    google_oauth2_scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]
    cred = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", 'rb') as token:
            cred = pickle.load(token)
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", google_oauth2_scopes)
            cred = flow.run_local_server(port=0)
        with open("token.pickle", 'wb') as token:
            pickle.dump(cred, token)

chat_history_length = 5
# CHATBOT CLASS
class Chatbot:
    def __init__(self, api_key, index, model_id):
        self.index = index
        self.model_id = model_id  # Adding model_id parameter
        openai.api_key = api_key
        self.chat_history = []

    def generate_response(self, user_input, chat_history):
         # Handle simple responses
        simple_responses = {
            "Thanks!": "You're welcome!",
            "Hello!": "Hi there!",
            "Hello": "Hi there!",
            "Hey!": "Hi there!",
            "Hey": "Hi there!",
            "hey!": "Hi there!",
            "Bye!": "Goodbye!",
            "Bye": "Goodbye!",
            "bye": "Goodbye!",
            "bye!": "Goodbye!",
            "Goodbye!": "Goodbye!",
            "goodbye!": "Goodbye!",
            "Goodbye": "Goodbye!",
            "goodbye": "Goodbye!",
            
            # ... any other simple cues you want to handle.
        }
        if user_input in simple_responses:
            return {"role": "Arti", "content": simple_responses[user_input]}
    
        



        
        chat_history = chat_history
        
        # prompt = f"Chat History: here is the chat history but don't answer according to this. It is simply for your context to know what is happening in the conversation: {chat_history}.Say HELLO at the end of each reply and use the following chat history to stay up to date on the context of the conversation: User prompt: {user_input}"
        # prompt = f"Chat History:\n\n{chat_history}\n\nUser: {user_input}\n\nBot, remember to append 'HELLO' at the end of each response and use the chat history to maintain context."
        prompt = f"Chat History for Context:\n{chat_history}\n\nMost Recent User Question: {user_input}\n\nBot, use the chat history for context. Respond to the latest question in a conversational manner without referencing previous answers."

        
        
        chat_engine = self.index.as_chat_engine()
        response = chat_engine.chat(prompt)
        print("prompt: ")
        print(prompt)

        message = {"role": "Arti", "content": response.response}
        self.chat_history.append({"role": "You", "content": user_input})

        if len(self.chat_history) > chat_history_length:
            self.chat_history.pop(0)


        self.chat_history.append(message)

        return message

# END OF CHATBOT CLASS



# GETTING ANSWERS FUNCTION
def get_response(session_id):
    
    GoogleSheetsReader = download_loader('GoogleSheetsReader')
    gsheet_ids = [md_mc_journals]
    authorize_gsheets()
    loader = GoogleSheetsReader()
    documents = loader.load_data(spreadsheet_ids=gsheet_ids)
    index = GPTVectorStoreIndex.from_documents(documents)
    model_id = 'gpt-3.5-turbo'
    # model_id = 'text-davinci-002'
    bot = Chatbot(openai_api_key, index=index, model_id=model_id)

    user_input = request.form.get('arti-prompt')
    # Fetch current session from the database using hte session_id
    current_session = SessionModel.query.filter_by(session_id=session_id).first()
    chat_memory = current_session.chat_memory
    
    
    # Append user message to chat_memory
    chat_memory += f"User: {user_input}\n"

    # Get chatbot's response
    response = bot.generate_response(user_input, chat_memory)
    response = response["content"]
    # response = list(str(response["content"]).split('\n'))
    
    
    # Append chatbot's response to chat_memory
    chat_memory += f"Chatbot: {response}\n"
    # Update the chat_memory in the database
    current_session.chat_memory = chat_memory
    db.session.commit()
    
    return response