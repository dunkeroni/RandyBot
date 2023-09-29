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
    print(setting)
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
    while True:
        #does this every loop in case settings change
        channel = Bot.get_channel(int(setting["channel_id"]))
        if setting["active"]:
            print("Sending message...")
            message = templates.build_random_message()
            await channel.send(message)
            print(message)
        #wait 10 seconds at a time until the timer is up
        time = 0
        while time < setting["posting_timer"]:
            await asyncio.sleep(10)
            time += 10

async def is_in_server_list(ctx: discord.Interaction):
    print("incoming command from " + str(ctx.guild_id))
    print("allowed servers: " + str(setting["server_whitelist"]))
    return (ctx.guild_id in setting["server_whitelist"]) or setting["server_whitelist"] == []

@Bot.tree.command(name="randyadd", description="Add a new random option to a template file")
@app_commands.check(is_in_server_list)
@app_commands.describe(target="Which list to add the new line to")
@app_commands.choices(target =[
    app_commands.Choice(name="descriptors", value="descriptors"),
    app_commands.Choice(name="subjects", value="subjects"),
    app_commands.Choice(name="intros", value="intros")
])
async def randy_add(Interaction: discord.Interaction, target: str, line: str):
    templates.add_to_template(line, target)
    channel = Bot.get_channel(int(setting["channel_id"]))
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Added '" + line + "' to " + target, color=0x00ff00), ephemeral=True)
    await channel.send(Interaction.user.name + " added `" + line + "` to the " + target + " list.")

@Bot.tree.command(name="randyremove", description="Remove a random option from a template file")
@app_commands.check(is_in_server_list)
@app_commands.describe(target="Which list to remove the line from")
@app_commands.choices(target =[
    app_commands.Choice(name="descriptors", value="descriptors"),
    app_commands.Choice(name="subjects", value="subjects"),
    app_commands.Choice(name="intros", value="intros")
])
async def randy_remove(Interaction: discord.Interaction, target: str, line: str):
    templates.remove_from_template(line, target)
    channel = Bot.get_channel(int(setting["channel_id"]))
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Removed '" + line + "' from " + target, color=0x00ff00), ephemeral=True)
    await channel.send(Interaction.user.name + " removed `" + line + "` from the " + target + " list.")

@Bot.tree.command(name="randyspeed", description="Change the posting speed of RandyBOT")
@app_commands.check(is_in_server_list)
@app_commands.describe(speed="How often RandyBOT should post, in seconds")
async def randy_speed(Interaction: discord.Interaction, speed: int):
    setting["posting_timer"] = speed
    save_settings(setting)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Changed posting speed to " + str(speed) + " seconds", color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randyrandom", description="Send a random message from RandyBOT right now")
@app_commands.check(is_in_server_list)
async def randy_random(Interaction: discord.Interaction):
    channel = Bot.get_channel(int(setting["channel_id"]))
    message = templates.build_random_message()
    await channel.send(message)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Sent random message", color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randyactivate", description="Activate RandyBOT in this channel. Hijacks from previous location.")
@app_commands.check(is_in_server_list)
async def randy_activate(Interaction: discord.Interaction):
    setting["channel_id"] = Interaction.channel.id
    print("Attaching to channel " + str(Interaction.channel.id))
    setting["active"] = True
    save_settings(setting)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Activated RandyBOT in this channel", color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randydeactivate", description="Deactivate RandyBOT.")
@app_commands.check(is_in_server_list)
async def randy_deactivate(Interaction: discord.Interaction):
    setting["active"] = False
    save_settings(setting)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Deactivated RandyBOT", color=0x00ff00), ephemeral=True)

Bot.run(TOKEN, log_handler=handler)
