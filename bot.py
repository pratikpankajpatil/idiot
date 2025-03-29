import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
import os
import requests
from dotenv import load_dotenv

# --------- Load Tokens ---------
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --------- Setup ---------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
GUILD_ID = discord.Object(id=1355394059828727838)  # replace with your server id

# --------- Basic Storage ---------
last_questions = {}  # user_id : last_question

# --------- Events ---------
@bot.event
async def on_ready():
    guild = discord.Object(id=1355394059828727838)
    await bot.tree.sync(guild=guild)
    await bot.tree.sync()  # also sync globally to clear junk
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Synced commands!")

# --------- Slash Commands ---------
@bot.tree.command(name="hello", description="Say hello to the bot!", guild=GUILD_ID)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f'Hello {interaction.user.display_name}, I am online!')

@bot.tree.command(name="time", description="Get current server time", guild=GUILD_ID)
async def time(interaction: discord.Interaction):
    now = datetime.datetime.now()
    await interaction.response.send_message(f'⏰ Current time: {now.strftime("%H:%M:%S")}')

@bot.tree.command(name="motivate", description="Get a motivational quote", guild=GUILD_ID)
async def motivate(interaction: discord.Interaction):
    quotes = [
        "You can do it!",
        "Stay focused.",
        "Don't forget why you started.",
        "One day, or day one. You decide.",
        "Be the Stark of your own story."
    ]
    await interaction.response.send_message(random.choice(quotes))

@bot.tree.command(name="note", description="Save a personal note", guild=GUILD_ID)
@app_commands.describe(content="The content of the note")
async def note(interaction: discord.Interaction, content: str):
    filename = f"notes_{interaction.user.id}.txt"
    with open(filename, "a") as f:
        f.write(f"{content}\n")
    await interaction.response.send_message("📝 Note saved!")

@bot.tree.command(name="readnotes", description="Read your saved notes", guild=GUILD_ID)
async def readnotes(interaction: discord.Interaction):
    filename = f"notes_{interaction.user.id}.txt"
    try:
        with open(filename, "r") as f:
            notes = f.read()
        await interaction.response.send_message(f"📓 Your notes:\n{notes}")
    except FileNotFoundError:
        await interaction.response.send_message("⚠ No notes found.")

@bot.tree.command(name="ask", description="Ask Hugging Face AI something", guild=GUILD_ID)
@app_commands.describe(question="Your question for the AI")
async def ask(interaction: discord.Interaction, question: str):
    try:
        # Only defer if the response will take a significant amount of time
        await interaction.response.defer()  # typing indicator

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
        payload = {"inputs": question}

        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            output = result[0]['generated_text'] if isinstance(result, list) else result.get("generated_text", "No answer.")
            last_questions[interaction.user.id] = question

            # Check if the output is too long (longer than 2000 characters)
            if len(output) > 2000:
                # Send the output in chunks of 2000 characters
                chunk_size = 2000
                for i in range(0, len(output), chunk_size):
                    await interaction.followup.send(output[i:i+chunk_size])
            else:
                await interaction.followup.send(f"💬 **AI:** {output}")
        else:
            await interaction.followup.send("❌ Hugging Face API error. Maybe quota finished?")
    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred: {e}")

@bot.tree.command(name="lastquestion", description="Show your last asked question", guild=GUILD_ID)
async def lastquestion(interaction: discord.Interaction):
    q = last_questions.get(interaction.user.id, None)
    if q:
        await interaction.response.send_message(f"🕑 Your last question was:\n> {q}")
    else:
        await interaction.response.send_message("You haven't asked anything yet.")

# --------- Start ---------
bot.run(DISCORD_TOKEN)
