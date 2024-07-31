from openai import AzureOpenAI
import os
import json
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup

TOKEN: Final =
BOT_USERNAME: Final = '@sefpypybot'
BING_SEARCH_API_KEY: Final = os.getenv('BING_SEARCH_API_KEY')

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment_name = 'gpt-4-32k'

# Initialize a dictionary to store message logs for each user
Message_logs = {}

# Function to read prompt from a file
def read_prompt(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read().strip()

# Read the prompt from the file
prompt_text = read_prompt('PhysicsBotPrompt.txt')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am your Physics Teacher Bot. How can I assist you with physics today?')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Just ask any physics-related question, and I will do my best to help you!')

def perform_search(query):
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML", "count": 5}
    try:
        response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error in web search: {e}")
        return "Failed to fetch results due to a network error."

    try:
        search_results = response.json()
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return "Failed to parse search results."
    
    results = []

    for web_page in search_results.get('webPages', {}).get('value', [])[:3]:  # Limit to 3 results
        title = BeautifulSoup(web_page['name'], 'html.parser').get_text()
        link = web_page['url']
        snippet = BeautifulSoup(web_page['snippet'], 'html.parser').get_text()
        
        shortened_snippet = (snippet[:450] + '...') if len(snippet) > 450 else snippet
        
        results.append({"title": title, "snippet": shortened_snippet, "link": link})
    
    return results if results else "No results found."

def summarize_results(results):
    summary = ""
    for result in results:
        summary += f"Title: {result['title']}\n"
        summary += f"Summary: {result['snippet']}\n"
        summary += f"Link: {result['link']}\n\n"
    return summary.strip()

def parse_model_response(response, user_id):
    try:
        response_content = response.choices[0].message.content
        if "TOOL_REQUEST" in response_content:
            print("--------------- Search Tool --------------------")
            tool_request = json.loads(response_content.split("TOOL_REQUEST:")[1])
            if tool_request["tool"] == "web_search":
                search_results = perform_search(tool_request["query"])
                summarized_results = summarize_results(search_results)
                return handle_response(f"Here are the summarized search results:\n\n{summarized_results}\n\nHow can I further assist you?", user_id)
        return response_content
    except json.JSONDecodeError:
        return "I apologize, but I encountered an error while processing the response. Could you please rephrase your question?"

def handle_response(text: str, user_id: int) -> str:
    Messages = Message_logs[user_id]
    Messages.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        model=deployment_name,
        messages=Messages,
        max_tokens=1600
    )

    ai_response = parse_model_response(response, user_id)
    Messages.append({"role": "assistant", "content": ai_response})
    Message_logs[user_id] = Messages

    return ai_response

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    user_id: int = update.message.chat.id
    if user_id not in Message_logs:
        Message_logs[user_id] = [{'role': 'system', 'content': prompt_text}]
    username: str = update.message.chat.username if update.message.chat.username else "Unknown"

    log_entry = f"User ({user_id}) : {text}"
    print(log_entry)
    
    try:
        ai_response = handle_response(text, user_id)
        await update.message.reply_text(ai_response)

    except Exception as e:
        print(f"Error in handle_message: {e}")
        await update.message.reply_text("An error occurred while processing your message. Please try again later.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("Polling...")
    app.run_polling(poll_interval=5)

if __name__ == "__main__":
    main()
