import discord
from discord.ext import commands
from discord import app_commands
import random
import os
from dotenv import load_dotenv
import logging
from scripts.settings import get_settings, save_settings
import scripts.templates as templates
import asyncio

load_dotenv()
# These are the environment variables that need to be set in .env, not included in repo
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.guilds = True
intents.message_content = True

Bot = commands.Bot(command_prefix="/", intents=intents)
setting = get_settings()

@Bot.event
async def on_ready():
    print('We have logged in.')
    print('Target Channel: ' + CHANNEL_ID)
    channel = Bot.get_channel(int(CHANNEL_ID))
    templates.auto_import()
    print("Current settings:")
    print(setting)
    try:
        synced = await Bot.tree.sync()
        print(synced)
    except Exception as e:
        print("Sync failed")
        print(e)

    Bot.loop.create_task(send_periodically())

@Bot.event
async def send_periodically():
    channel = Bot.get_channel(int(CHANNEL_ID))
    while True:
        print("Sending message...")
        message = templates.build_random_message()
        await channel.send(message)
        print(message)
        await asyncio.sleep(setting["posting_timer"])

def only_this_guild(guild_id: int):
    async def predicate(ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage() 
        return ctx.guild.id == guild_id           
    return commands.check(predicate)

@Bot.tree.command(name="randyadd", description="Add a new random option to a template file")
@app_commands.describe(target="Which list to add the new line to")
@app_commands.choices(target =[
    app_commands.Choice(name="descriptors", value="descriptors"),
    app_commands.Choice(name="subjects", value="subjects"),
    app_commands.Choice(name="intros", value="intros")
])
async def randy_add(Interaction: discord.Interaction, target: str, line: str):
    templates.add_to_template(line, target)
    channel = Bot.get_channel(int(CHANNEL_ID))
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Added '" + line + "' to " + target, color=0x00ff00), ephemeral=True)
    await channel.send(Interaction.user.name + " added `" + line + "` to the " + target + " list.")

@Bot.tree.command(name="randyremove", description="Remove a random option from a template file")
@app_commands.describe(target="Which list to remove the line from")
@app_commands.choices(target =[
    app_commands.Choice(name="descriptors", value="descriptors"),
    app_commands.Choice(name="subjects", value="subjects"),
    app_commands.Choice(name="intros", value="intros")
])
async def randy_remove(Interaction: discord.Interaction, target: str, line: str):
    templates.remove_from_template(line, target)
    channel = Bot.get_channel(int(CHANNEL_ID))
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Removed '" + line + "' from " + target, color=0x00ff00), ephemeral=True)
    await channel.send(Interaction.user.name + " removed `" + line + "` from the " + target + " list.")

@Bot.tree.command(name="randyspeed", description="Change the posting speed of RandyBOT")
@app_commands.describe(speed="How often RandyBOT should post, in seconds")
async def randy_speed(Interaction: discord.Interaction, speed: int):
    setting["posting_timer"] = speed
    save_settings(setting)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Changed posting speed to " + str(speed) + " seconds", color=0x00ff00), ephemeral=True)

Bot.run(TOKEN, log_handler=handler)
