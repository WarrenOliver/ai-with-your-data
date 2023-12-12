import os
import json
import credentials

from flask import request
import openai

from typing import List
from llama_index import download_loader, GPTVectorStoreIndex
from llama_index.readers.base import BaseReader
from llama_index.readers.schema.base import Document

__name__ = 'cbot'

# Airtable credentials
airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
airtable_personal_token = os.environ.get('AIRTABLE_PERSONAL_TOKEN')
airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')

# ChatGPT Key
openai_api_key = os.environ.get('OPENAI_API_KEY')

airtable_team_table_id = os.environ.get('AIRTABLE_TEAM_TABLE_ID')


AirtableReader = download_loader('AirtableReader')



# table_id="tbltg7F4TelpCwULT"
table_id = airtable_team_table_id

base_id = os.environ.get('AIRTABLE_BASE_ID')



class AirtableReader(BaseReader):

    
    def __init__(self, api_key: str) -> None:
        

        self.api_key = api_key

    def load_data(self, base_id: str,table_id: str) -> List[Document]:

        from pyairtable import Table
        table = Table(self.api_key, base_id, table_id)
        all_records=table.all()
        return [Document(f"{all_records}", extra_info={})]

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


reader = AirtableReader(airtable_personal_token)
documents = reader.load_data(base_id=base_id, table_id=table_id)
index = GPTVectorStoreIndex.from_documents(documents)


bot = Chatbot(openai_api_key, index=index)

def get_response():
    if __name__ == 'cbot':
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