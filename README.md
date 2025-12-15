The link to the working file is here:

https://github.com/skyl4rk/ai-assistant/blob/master/project/ai-assistant.py

You will need an openrouter api key for this script. You will need to make a payment to openrouter for the non-free models.

https://openrouter.ai

Set up an .env file using the .example.env file as a template.

The script will create a context.txt in the same directory. This file will show the last few queries and responses, 5,000 characters in length. The script sends the context file along with your query to the LLM model.

Modify the system prompt variable to your needs.

Change the models listed in the combobox as you prefer. The format is the same as listed on openrouter.ai.

