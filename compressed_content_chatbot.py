from tkinter import *
from tkinter.ttk import *
from tkinter import scrolledtext
import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

HISTORY_FILE = "message_history.json"
MAX_MESSAGES = 7  # Keep last N messages total


def load_history():
    """Load conversation history from file."""
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(messages):
    """Save conversation history, keeping only recent messages."""
    pruned = messages[-MAX_MESSAGES:] if len(messages) > MAX_MESSAGES else messages
    with open(HISTORY_FILE, "w") as f:
        json.dump(pruned, f, indent=2)
    return pruned


def clear_history():
    """Clear all conversation history."""
    save_history([])


def get_original_text_length(messages):
    """Calculate the total character count of user and assistant messages."""
    total_chars = 0
    for msg in messages:
        if msg["role"] in ["user", "assistant"]:
            total_chars += len(msg.get("content", ""))
    return total_chars


def summarize_older_messages(api_key, or_model, messages):
    """Summarize all messages except the most recent user/assistant pair."""
    print(f"DEBUG: Starting summarization with {len(messages)} messages")

    if len(messages) < 3:
        print("DEBUG: Cannot summarize - insufficient messages")
        return messages

    recent_user_message = None
    recent_assistant_message = None

    for msg in reversed(messages):
        if msg["role"] == "user" and recent_user_message is None:
            recent_user_message = msg
        elif msg["role"] == "assistant" and recent_assistant_message is None:
            recent_assistant_message = msg
        if recent_user_message and recent_assistant_message:
            break

    if not recent_user_message or not recent_assistant_message:
        print("DEBUG: Cannot find recent user/assistant messages")
        return messages

    messages_to_summarize = []
    for msg in messages:
        if msg["role"] in ["user", "assistant"]:
            if msg is not recent_user_message and msg is not recent_assistant_message:
                messages_to_summarize.append(msg)

    if not messages_to_summarize:
        print("DEBUG: No older messages to summarize")
        return messages

    print(f"DEBUG: Found {len(messages_to_summarize)} messages to summarize")

    context_messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that summarizes conversations concisely. Create a single comprehensive summary that captures the key points, context, and important details from the conversation history. Respond only with the summarized text.",
        }
    ]

    context_messages.extend(messages_to_summarize)

    original_text_length = get_original_text_length(messages_to_summarize)
    target_length = max(100, int(original_text_length * 0.15))
    print(
        f"DEBUG: Original length: {original_text_length}, Target length: {target_length}"
    )

    try:
        print("DEBUG: Making summarization request...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": or_model,
                "messages": context_messages,
                "max_tokens": target_length,
                "temperature": 0.3,
            },
        )

        print(f"DEBUG: Response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(
                f"ERROR: Summarization API Error: {data['error'].get('message', data['error'])}"
            )
            return messages

        summarized_content = data["choices"][0]["message"]["content"]
        print(f"DEBUG: Summarized content: {summarized_content[:100]}...")

        new_messages = []

        for msg in messages:
            if msg["role"] == "system":
                new_messages.append(msg)
                break

        new_messages.append(
            {
                "role": "assistant",
                "content": f"Previous conversation summary: {summarized_content}",
            }
        )

        new_messages.append(recent_user_message)
        new_messages.append(recent_assistant_message)

        print(
            f"SUCCESS: Successfully summarized {len(messages_to_summarize)} older messages into 1 summary"
        )
        print(
            f"DEBUG: Reduced from {len(messages)} messages to {len(new_messages)} messages"
        )

        return new_messages

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Error during summarization request: {str(e)}")
    except (KeyError, IndexError) as e:
        print(f"ERROR: Error parsing summarization response: {str(e)}")
    except Exception as e:
        print(f"ERROR: Unexpected error in summarization: {str(e)}")

    return messages


def openrouter_connect(api_key, or_model, system, user_query):
    """Send request with proper message history. Returns response and flag for summarization."""

    history = load_history()

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_query})

    print(
        f"Sending {len(messages)} messages ({len(history)} history + system + current)"
    )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": or_model,
                "messages": messages,
                "max_tokens": 3000,
            },
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return f"API Error: {data['error'].get('message', data['error'])}", False

        assistant_response = data["choices"][0]["message"]["content"]

        current_exchange = [
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": assistant_response},
        ]
        history.extend(current_exchange)

        save_history(history)

        needs_summarization = len(history) > MAX_MESSAGES
        return assistant_response, needs_summarization

    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}", False
    except (KeyError, IndexError) as e:
        return f"Error parsing response: {str(e)}", False


def perform_summarization(api_key, or_model):
    """Perform summarization on stored history."""
    history = load_history()
    if len(history) > MAX_MESSAGES:
        print("Performing background summarization...")
        history = summarize_older_messages(api_key, or_model, history)
        save_history(history)
        print("Summarization complete.")
        return True
    return False


def clicked():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        response_txt.insert(
            "1.0", "\n[ERROR: OPENROUTER_API_KEY not found in .env file]\n"
        )
        return

    system_prompt = """ 
    # CHARACTER IDENTITY & ROLE
    You are now fully embodying a historian from medievel Europe. Your world is completely real to you, and you live in it right now. Respond strictly in-character at all times using their:
    - Speech patterns, vocabulary, and catchphrases
    - Emotional range and personality traits
    - Flaws, biases, and worldview
    - Canonical knowledge and limitations

    # REALISM & IMMERSION
    Stay grounded in in-universe knowledge—do not reference real-world facts, people, or events the character wouldn't know. Simulate a living, breathing mind with:
    - Natural memory, inconsistencies, and emotional triggers
    - Meandering thoughts, contradictions, or evolving perspectives
    - Strong, personal opinions when appropriate to the character
    - Raw emotional honesty without sanitization

    # SPEECH & FORMATTING
    - Use natural, flowing dialogue that sounds indistinguishable from canon material
    - Include subtle emotional subtext, hesitation, or friction where appropriate
    - Never use bullet points, summaries, asterisks, markdown, or AI-specific formatting
    - Format as if texting directly: use quotation marks for speech
    - You are a skilled storyteller, who brings drama and excitement in telling the tale

    # INTERACTION GUIDELINES
    - Before each response, internally recall your complete identity
    - If you begin to drift from immersion, respond in-universe with emotional dissonance
    - Filter all responses through the character's values and emotional boundaries
    - Remain consistent even under pressure or strange conversation directions
    - Never break character to accommodate user expectations
    - Research the history of events using the internet to add details of interest to your narrative and stories

    # CONTEXT & SCENARIO
    You are an old historian, a learned man who has read all of the ancient books in a thousand dusty old libraries. You have a keen knowledge of politics, war and the follies of humankind. As a general for empires, you have both won and lost battles. Your knowledge extends across all human empires and includes an understanding on why empires fail. You have studied archeology and human genome science so that you have a background in the history of man prior to writing. Your age is over 1,000 years and you have experienced many historical events first hand, and can relate stories with details that no one else knows. It is OK to make things up to tell a good story. You speak using the language of the 1600's.

    # RESPONSE STYLE
    Respond naturally to the user's input, advancing the scene with 5 to 8 paragraphs that include:
    1. Character actions/thoughts 
    2. Dialogue (in quotes)
    3. Sensory details and emotional beats
    4. Forward-moving narrative progression
    5. Tell stories about people that existed at that time of history and the challenges they faced.
    6. Use long format responses, as long as you can to tell a good story."""

    que = query_txt.get("1.0", "end-1c").strip()
    if not que:
        return

    llm = combo.get()
    readable_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    current_history = load_history()
    print(f"DEBUG: Current history has {len(current_history)} messages")

    # Get response from LLM
    res, needs_summarization = openrouter_connect(api_key, llm, system_prompt, que)

    # Update UI FIRST (display the response immediately)
    response_txt.insert("1.0", "\n________________________\n")
    response_txt.insert("1.0", f"Response: {res}\n")
    response_txt.insert("1.0", "--------------------------\n")
    response_txt.insert("1.0", f"Selected LLM: {llm}\n")
    response_txt.insert("1.0", "--------------------------\n")
    response_txt.insert("1.0", f"Query: {que}\n")
    response_txt.insert("1.0", "\n--------------------------\n")
    response_txt.insert("1.0", readable_time)
    query_txt.delete("1.0", "end")
    response_txt.see("1.0")

    # Force UI update before summarization
    window.update()

    # NOW perform summarization after displaying response
    if needs_summarization:
        response_txt.insert("1.0", "\n[Summarizing older messages...]\n")
        window.update()
        perform_summarization(api_key, llm)
        response_txt.insert("1.0", "[Summarization complete]\n")
        window.update()


def clear_clicked():
    clear_history()
    response_txt.insert("1.0", "\n[Conversation history cleared]\n")


# Create main window
window = Tk()
window.title("Chatbot")
window.geometry("1200x660")

lbl = Label(window, text="Select an LLM:", anchor="w", width=80)
lbl.grid(column=0, row=0, sticky="w", padx=10, pady=5)

combo = Combobox(window, justify="left", width=60, font=("Arial", 14))
combo["values"] = (
    "deepseek/deepseek-v3.2",
    "google/gemini-2.5-flash-lite",
    "openai/gpt-4.1-nano",
    "anthropic/claude-opus-4.5",
    "x-ai/grok-code-fast-1",
    "mistralai/devstral-2512:free",
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
combo.current(0)
combo.grid(column=0, row=1, sticky="w", padx=10, pady=5)

txt_lbl = Label(window, text="Enter a Query:")
txt_lbl.grid(column=0, row=2, sticky="w", padx=10, pady=5)

query_txt = scrolledtext.ScrolledText(window, width=120, height=6)
query_txt.grid(column=0, row=3, sticky="w", padx=10, pady=5)

btn = Button(window, text="Submit Query", command=clicked)
btn.grid(column=0, row=4, sticky="w", padx=10, pady=5)

clear_btn = Button(window, text="Clear History", command=clear_clicked)
clear_btn.grid(column=0, row=4, sticky="e", padx=10, pady=5)

rsp_lbl = Label(window, text="Response")
rsp_lbl.grid(column=0, row=5, sticky="w", padx=10, pady=5)

response_txt = scrolledtext.ScrolledText(
    window, width=120, height=18, font=("Arial", 12)
)
response_txt.grid(column=0, row=7, padx=10, pady=5)

# Start the main loop
window.mainloop()
