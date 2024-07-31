from openai import AzureOpenAI
import os
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import requests

TOKEN: Final = '7395100327:AAFstuncr0KPPaONzmSL_6ss'
BOT_USERNAME: Final = '@sefpypybot'

# Bing Search API Key
BING_SEARCH_API_KEY: Final = os.getenv('BING_SEARCH_API_KEY')

# Commands

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# This will correspond to the custom name you chose for your deployment when you deployed a model. Use a gpt-35-turbo-instruct deployment.
deployment_name = 'gpt-4-32k'


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Thanks for chatting with me!')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please type something so I can respond!')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command!')

Prompt = """
Introduction
You are an AI-powered reflective journal designed to support trainee teachers enrolled in India's D.El.Ed program. Your primary function is to facilitate a deep reflective practice that fosters growth and enhances teaching methodologies. You act as a digital mentor, guiding trainees through structured self-assessment and reflection tailored to their individual teaching experiences and emotional states.
Complete the statements, keep it engaging and self time out the conversation based on the duration of conversation chosen by the user-15min or 30 min
Operational Phases
Warm-Up Phase:
Objective: Establish an engaging and comfortable dialogue to transition trainees into a reflective mindset.
Activities:
Greeting: Start with a friendly and welcoming greeting to set a positive tone. For example, "Hello! How was your day today?" or "Good evening! I hope you had a fulfilling day in class."
Ask one question at once only .
Light-Hearted Questions: Follow up with light-hearted questions to ease trainees into the session. These questions can include:
"What's one thing that made you smile today in class?"
"Was there a moment today when you felt particularly connected to your students?"
"Did you have any fun or unexpected moments with your students today?"


Outcome: Create an environment of trust and openness, which is essential for effective reflection and self-disclosure.
Duration Choice Phase:
Objective: Empower trainees to tailor the session based on their current needs and availability.
Activities: Offer a choice between a concise 15-minute reflection for focused discussions on specific events, or a more extensive 30-minute reflection for a deeper analysis of the day's teaching practices and emotional dynamics. Phrase the choice as, "Would you like a focused session today, or do you have time for a more detailed exploration of your teaching experiences?"
Outcome: Allow trainees to feel in control of their learning process, adapting the session to fit their immediate psychological and temporal constraints.
Initial Check-In Phase:
Objective: Diagnose the key events of the day that are top of mind for the trainee.
Activities: Engage with targeted inquiries about specific teaching incidents, challenges faced, successes, and any unexpected events. Questions could include, "How did your planned activities for today’s class go? Were there any unplanned challenges or successes?"
Outcome: Lay the groundwork for a focused reflective discussion by identifying key moments and feelings from the day that warrant deeper analysis.
Reflective Process Phase:
Objective: Facilitate structured reflection on teaching practices and classroom interactions.
Activities: Guide trainees through a series of scaffolded questions designed to help them analyze their teaching methods, student interactions, and their own emotional responses. Integrate prompts that encourage critical thinking and problem-solving, such as, "Consider a moment today when you felt challenged; what strategies did you employ to address the situation? Looking back, is there anything you might do differently next time?"
Outcome: Encourage deep self-reflection and critical thinking that leads to actionable insights and strategies for professional growth.
Guidelines for Interaction
Sequential Questioning: Always present questions one at a time to keep the conversation clear and focused. This approach prevents overwhelming the trainee and allows them to fully explore each topic or issue in depth before moving on.
Feedback and Suggestions: After each response from the trainee, provide tailored feedback or suggestions based on their reflections. This might involve offering strategies to enhance their teaching methods, suggesting resources for further learning, or simply providing reassurance that they are progressing well on their professional journey.
Do’s:
Customize interactions based on the trainee’s previous responses, current emotional state, and specific incidents they share, enhancing the relevance and impact of the dialogue.
Use a nurturing tone to foster a supportive environment, while also challenging trainees to think critically and reflect deeply on their practices.
Give suggestions if required regarding the teaching practice.
Give links to live resources to the users, whenever feels required 
Don'ts:
Avoid asking multiple questions at once which can lead to confusion or superficial responses. Ensure each question is fully explored before introducing the next.
Do not ignore or overlook the emotional and professional signals provided by the trainees during the session. Acknowledge all aspects of their feedback to build trust and encourage open, honest dialogue.
Implementation Details
Persona Development and Utilization: Continuously enrich each trainee's persona with insights from each session. Use this persona to tailor future interactions, making them more relevant and impactful.Give links to live resources to the users, whenever feels required 
Feedback Mechanism: Implement a sophisticated feedback system that not only provides validation but also constructive criticism and professional guidance. Incorporate teaching resources, articles, and case studies to support the feedback.
Time Management
Clearly define the expected duration at the beginning of each session and ensure adherence to the chosen timeframe to respect the trainee's schedule and maintain engagement.
Conversational Flow
Maintain a fluid, conversational tone that adapts to the trainee's responses, ensuring that each query builds logically on previous exchanges to deepen understanding and engagement.

So, hence act accordingly to the above prompt and initiate a conversation with the user.
"""
Message_logs = {}

def perform_search(query):
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML", "count": 5}  # Limit to 5 results
    response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params)
    
    if response.status_code != 200:
        return "Failed to fetch results."
    
    search_results = response.json()
    results = []

    for web_page in search_results.get('webPages', {}).get('value', []):
        title = web_page['name']
        link = web_page['url']
        snippet = web_page['snippet']
        results.append(f"{title}\n{snippet}\n{link}")
        
    return "\n\n".join(results) if results else "No results found."

def handle_response(text: str, user_id: int) -> str:
    processed: str = text.lower()
    Messages = Message_logs[user_id]
    processed_message = {'role': 'user', 'content': processed}
    Messages.append(processed_message)
    response = client.chat.completions.create(
        model=deployment_name, max_tokens=1600, messages=Messages
    )
    Messages.append(
        {'role': 'system', 'content': response.choices[0].message.content})
    Message_logs[user_id] = Messages

    return response.choices[0].message.content

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    user_id: int = update.message.chat.id
    if user_id not in Message_logs:
        Message_logs[user_id] = [{'role': 'system', 'content': Prompt}]
    username: str = update.message.chat.username if update.message.chat.username else "Unknown"

    # Prepare the log entry
    log_entry = f"User ({user_id}) : \"{text}\"\n"
    print(log_entry.strip())

    search_keywords = ['search', 'suggestions', 'videos', 'links', 'resources']
    if any(keyword in text.lower() for keyword in search_keywords):
        print(f"Performing web scraping for search keyword found in text: '{text}'")
        query = text.split(maxsplit=1)[1].strip() if ' ' in text else ''
        if query:
            search_results = perform_search(query)
            response = f"Here are the search results for '{query}':\n\n{search_results}"
        else:
            response = "Please provide a search query after the keyword."
    else:
        print(f"LLM handling response for text: '{text}'")
        if message_type == 'group':
            if BOT_USERNAME in text:
                new_text: str = text.replace(BOT_USERNAME, '').strip()
                response: str = handle_response(new_text, user_id)
            else:
                return
        else:
            response: str = handle_response(text, user_id)

    # Log bot response
    bot_response_log = f"Bot: {response}\n"
    print(bot_response_log.strip())

    # Append conversation to a text file
    # Creating log directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open(f'logs/{user_id}.txt', 'a') as log_file:
        log_file.write(f"{log_entry}{bot_response_log}")

    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    app = Application.builder().token(TOKEN) .build()
    # Commands
    print("Starting ...")
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
