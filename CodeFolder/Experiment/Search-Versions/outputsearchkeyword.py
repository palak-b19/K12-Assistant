from openai import AzureOpenAI
import os
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup

TOKEN: Final = '7395100327:AAFstuncapDCsVc5wY3r0KPPaONzmSL_6ss'
BOT_USERNAME: Final = '@sefpypybot'

# Bing Search API Key
BING_SEARCH_API_KEY: Final = os.getenv('BING_SEARCH_API_KEY')

# Azure OpenAI client setup
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

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

Important
Give suggestions if required regarding the teaching practices
Give links to live resources to the users, whenever feels required 
Whenever you decide to give links, or any resources start the reponse with phrase "You can refer to the following resources"


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
Important Do’s:
Customize interactions based on the trainee’s previous responses, current emotional state, and specific incidents they share, enhancing the relevance and impact of the dialogue.
Use a nurturing tone to foster a supportive environment, while also challenging trainees to think critically and reflect deeply on their practices.
Very important Do's:
Give suggestions if required regarding the teaching practices
Give links to live resources to the users, whenever feels required 
Whenever you decide to give links, or any resources start the reponse with phrase "You can refer to the following resources"
If you decide to give some links/resources based on user query, then limit the description text of each link to 2-3 lines
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
    params = {"q": query, "textDecorations": True, "textFormat": "HTML", "count": 5}
    response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params)
    
    if response.status_code != 200:
        return "Failed to fetch results."
    
    search_results = response.json()
    results = []

    for web_page in search_results.get('webPages', {}).get('value', []):
        title = BeautifulSoup(web_page['name'], 'html.parser').get_text()
        link = web_page['url']
        snippet = BeautifulSoup(web_page['snippet'], 'html.parser').get_text()
        
        # Shorten the snippet to 2-3 lines (assuming about 150 characters per line)
        shortened_snippet = (snippet[:450] + '...') if len(snippet) > 450 else snippet
        
        results.append(f"{title}\n{shortened_snippet}\n{link}")
        
        # Limit to 5 results
        if len(results) >= 5:
            break
    
    return "\n\n".join(results) if results else "No results found."

def handle_response(text: str, user_id: int) -> (str, str):
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

    response_content = response.choices[0].message.content
    return response_content, text

def detect_search_intent(response: str) -> bool:
    search_triggers = ['Here are a few','Here are ','You can refer to the following','I also recommend referring to this ','I also recommend referring to this','Remember to make use of resources available online ','Here is a useful [article]','Here is a useful ','Here\'s an artcile','Here is a link','Here\'s a link','Here\'s a video','Here\'s a blog','Here\'s an ','Here\'s a','Here is a']
    return any(trigger in response for trigger in search_triggers)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    user_id: int = update.message.chat.id
    if user_id not in Message_logs:
        Message_logs[user_id] = [{'role': 'system', 'content': Prompt}]
    username: str = update.message.chat.username if update.message.chat.username else "Unknown"

    log_entry = f"User ({user_id}) : {text}"
    print(log_entry)
    
    try:
        # Get AI response and context for search
        ai_response, search_context = handle_response(text, user_id)
        
        # Perform Bing search if intent is detected
        if detect_search_intent(ai_response):
            print(' ############# Using web scraping #################')
            search_results = perform_search(search_context)
            ai_response += "\n\n" + search_results

        await update.message.reply_text(ai_response)

    except Exception as e:
        print(f"Error: {e}")
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