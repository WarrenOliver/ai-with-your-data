import os
import pickle

import json
import openai

from flask import request

from google.auth.transport.requests import Request

from google_auth_oauthlib.flow import InstalledAppFlow
from llama_index import GPTVectorStoreIndex, download_loader

__name__ = 'cbot'

airtable_api_key = os.environ.get('AIRTABLE_API_KEY')

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


#BOT CLASS
def get_response():
    class Chatbot:
        def __init__(self, api_key, index):
            self.index = index
            openai.api_key = api_key
            self.chat_history = []

        def generate_response(self, user_input):
            prompt = "\n".join([f"{message['role']}: {message['content']}" for message in self.chat_history[-5:]])
            prompt += f"\nUser: {user_input}"
            query_engine = index.as_query_engine()
            response = query_engine.query(user_input)

            message = {"role": "assistant", "content": response.response}
            self.chat_history.append({"role": "user", "content": user_input})
            self.chat_history.append(message)            
            return message
        
        def load_chat_history(self, filename):
            try:
                with open(filename, 'r') as f:
                    self.chat_history = json.load(f)
            except FileNotFoundError:
                pass

        def save_chat_history(self, filename):
            with open(filename, 'w') as f:
                json.dump(self.chat_history, f)
    #EOS

    GoogleSheetsReader = download_loader('GoogleSheetsReader')
    gsheet_ids = ['1uUixE53C1hsNgrZXbxI5JTvuseRQtkXQ7G6D_qj23Yw']
    authorize_gsheets()
    loader = GoogleSheetsReader()
    documents = loader.load_data(spreadsheet_ids=gsheet_ids)
    index = GPTVectorStoreIndex.from_documents(documents)
    bot = Chatbot("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", index=index)


    if __name__ == 'cbot':
        GoogleSheetsReader = download_loader('GoogleSheetsReader')
        gsheet_ids = ['1uUixE53C1hsNgrZXbxI5JTvuseRQtkXQ7G6D_qj23Yw']
        authorize_gsheets()
        loader = GoogleSheetsReader()
        documents = loader.load_data(spreadsheet_ids=gsheet_ids)
        index = GPTVectorStoreIndex.from_documents(documents)
        bot = Chatbot("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", index=index)

        while True:
            bot.load_chat_history("chat_history.json")
            # prompt = input("Type prompt: ")
            prompt = request.form.get('arti-prompt')

            query_engine = index.as_query_engine()
            response = query_engine.query(prompt)
            response = str(response)
            response = list(response.split('\n'))
            
            return response

    GoogleSheetsReader = download_loader('GoogleSheetsReader')