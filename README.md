ai-chat-gui provides a single python file that creates a graphic user interface to chat with various LLM ai models available on openrouter.ai. The system prompt is set up to be a python tutor, but can be modified as needed.

The working file is ai-assistant.py.

You will need an openrouter api key for this script. You will need to make a payment to openrouter for the non-free models.

https://openrouter.ai

Set up an .env file using the .example.env file as a template.

The script will create a context.txt file in the directory where ai-assistant.py is located. This file will show the last few queries and responses, 5,000 characters in length. The script sends the context file along with your query to the LLM model.

Modify the system prompt variable to your needs.

Install packages: openrouter datetime python-dotenv requests

You may also use the requirements.txt file to install packages.

Change the models listed in the combobox as you prefer. The format is the same as listed on openrouter.ai.

Compressed Context Chatbot

This is an experimental version of the ai-assistant. The CCC summarizes older conversation turns and reduces the volume of text that the LLM has to review with each new turn. The hope is that this will lead to more focused responses and higher quality chat, with less hallucination or off topic rambling. It may lead to reduced response times.

The Compressed Contex Chatbot has not been evaluated as to whether its performance is better than the standard ai-assistant.py. 
