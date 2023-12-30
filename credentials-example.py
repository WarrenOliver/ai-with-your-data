import os

# rename file to credentials.py
# you will also need Google Oauth2 credentials. These you should rename to credentials.json -- A token.json and token.pickle file will be generated once your key is present and verified.

# OpenAI API Key
os.environ['OPENAI_API_KEY'] = '<your openai API key>'

# Login Password
os.environ['LOGIN_PASSWORD'] = '<login password of your choosing>'