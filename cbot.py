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

service_context = ServiceContext.from_defaults(llm=ChatOpenAI(temperature=0.))


__name__ = 'cbot'

openai_api_key = os.environ.get('OPENAI_API_KEY')

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

    def generate_response(self, user_input):
        prompt = "\n".join([f"{message['role']}: {message['content']}" for message in self.chat_history[:-1]])
        prompt += "\nPlease refer to the project details mentioned earlier in our conversation to provide accurate answers. " \
              "If you have any questions regarding those project details, feel free to ask. Be as succint as you can be:  " \
              f"User: {user_input}"
        
        chat_engine = self.index.as_chat_engine()
        response = chat_engine.chat(prompt)

        message = {"role": "Arti", "content": response.response}
        self.chat_history.append({"role": "You", "content": user_input})

        if len(self.chat_history) > chat_history_length:
            self.chat_history.pop(0)


        self.chat_history.append(message)

        return message
    

    # # load_chat_history function
    # def load_chat_history(self, filename):
    #     try:
    #         with open(filename, 'r') as f:
    #             self.chat_history = json.load(f)
    #     except FileNotFoundError:
    #         pass

    # # save_chat_history function
    # def save_chat_history(self, filename):
    #     with open(filename, 'w') as f:
    #         json.dump(self.chat_history, f)

# END OF CHATBOT CLASS


GoogleSheetsReader = download_loader('GoogleSheetsReader')
gsheet_ids = [md_mc_journals]
authorize_gsheets()
loader = GoogleSheetsReader()
documents = loader.load_data(spreadsheet_ids=gsheet_ids)
index = GPTVectorStoreIndex.from_documents(documents)
model_id = 'gpt-3.5-turbo'
bot = Chatbot(openai_api_key, index=index, model_id=model_id)

# GETTING ANSWERS FUNCTION
def get_response():
    while True:
        prompt = request.form.get('arti-prompt')
        response = bot.generate_response(prompt)
        response = list(str(response["content"]).split('\n'))   
        
        print("printing chat history: ")
        print(bot.chat_history)
        return bot.chat_history

        