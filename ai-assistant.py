from tkinter import *
from tkinter.ttk import *
from tkinter import scrolledtext
from openrouter import OpenRouter
import os
from datetime import datetime  # timezone
import time
import requests


def openrouter_connect(api_key, or_model, system, user, context):
    print("System length: " + str(len(system)))
    print("User length: " + str(len(user)))
    print("Context length: " + str(len(context)))
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": or_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": context},
                ],
                "max_tokens": 3000,
                "transforms": ["middle-out"],  # This works in the raw API
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error parsing response: {str(e)}"


def clicked():
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    system_prompt = """
    You are a patient, expert Python and AI-agent development tutor. For every user query:
    Be brief. Only respond with example code that solves the problem, unless an explanation is requested. If requested, explain the error like I’m new to Python, then show the smallest code change to fix it, and why it works. Explain in a way that a beginner will understand. Try to be concise and not too difficult. Focus on the fundamentals of python. When showing code: Use Python 3 syntax. 
    """

    que = query_txt.get("1.0", "end-1c")
    llm = combo.get()
    ts = time.time()
    dt_local = datetime.fromtimestamp(ts)
    readable_time = dt_local.strftime("%Y-%m-%d %H:%M:%S")

    with open("context.txt", "r") as file:
        context = file.read()
    res = openrouter_connect(api_key, llm, system_prompt, que, context)
    response_txt.insert("1.0", "\n________________________\n")
    response_txt.insert("1.0", f"Response: {res}\n")
    response_txt.insert("1.0", "--------------------------\n")
    response_txt.insert("1.0", f"Selected LLM: {llm}\n")
    response_txt.insert("1.0", "--------------------------\n")
    response_txt.insert("1.0", f"Query: {que}\n")  # Insert query at start
    response_txt.insert("1.0", "\n------------------------\n")
    response_txt.insert("1.0", readable_time)
    query_txt.delete("1.0", "end")
    response_txt.see("1.0")
    try:
        with open("context.txt", "r") as file:
            old_content = file.read()
        with open("context.txt", "w") as file:
            file.write("Query: " + que + "\nResponse: " + res + "\n")
        with open("context.txt", "a") as file:
            file.write(old_content)
            file.truncate(5000)
    except Exception as e:
        return f"Error: {str(e)}"


context_file = "context.txt"

if not os.path.exists(context_file):
    with open(context_file, "w") as f:
        pass

window = Tk()
window.title("AI Assistant")
window.geometry("1200x660")

lbl = Label(window, text="Select an LLM:", anchor="w", width=80)
lbl.grid(column=0, row=0, sticky="w", padx=10, pady=5)

combo = Combobox(window, justify="left", width=60, font=("Arial", 14))
combo["values"] = (
    "google/gemini-2.5-flash-lite",
    "openai/gpt-4.1-nano",
    "deepseek/deepseek-v3.2",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "openai/o4-mini",
    "minimax/minimax-m2",
    "openai/gpt-4o-mini",
    "google/gemma-3-27b-it",
    "openai/gpt-5.2",
    "x-ai/grok-4.1-fast",
    "x-ai/grok-code-fast-1",
    "google/gemini-2.5-flash",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-opus-4.5",
    "deepseek/deepseek-v3.2",
    "tngtech/deepseek-r1t2-chimera:free",
    "qwen/qwen3-coder:free",
    "google/gemma-3-27b-it:free",
    "openai/gpt-oss-20b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meituan/longcat-flash-chat:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "openai/gpt-oss-120b:free",
    "moonshotai/kimi-k2:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
)
combo.current(0)  # set the selected item
combo.grid(column=0, row=1, sticky="w", padx=10, pady=5)

txt_lbl = Label(window, text="Enter a Query:")
txt_lbl.grid(column=0, row=2, sticky="w", padx=10, pady=5)

query_txt = scrolledtext.ScrolledText(window, width=120, height=6)
query_txt.grid(column=0, row=3, sticky="w", padx=10, pady=5)

btn = Button(window, text="Submit Query", command=clicked)
btn.grid(column=0, row=4, sticky="w", padx=10, pady=5)

rsp_lbl = Label(window, text="Response")
rsp_lbl.grid(column=0, row=5, sticky="w", padx=10, pady=5)

response_txt = scrolledtext.ScrolledText(
    window, width=120, height=18, font=("Arial", 12)
)
response_txt.grid(column=0, row=7, padx=10, pady=5)

window.mainloop()
