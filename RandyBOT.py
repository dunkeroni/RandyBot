import discord
from discord.ext import commands
from discord import app_commands
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
            message = templates.build_random_message(setting)
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
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
@app_commands.describe(target="Which list to add the new line to")
@app_commands.choices(target =[
    app_commands.Choice(name="descriptors", value="descriptors"),
    app_commands.Choice(name="subjects", value="subjects"),
    app_commands.Choice(name="intros", value="intros")
])
async def randy_add(Interaction: discord.Interaction, target: str, line: str):
    total = templates.add_to_template(line, target)
    channel = Bot.get_channel(int(setting["channel_id"]))
    if total == -1:
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="'" + line + "' already exists in " + target, color=0xff0000), ephemeral=True)
        return
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Added '" + line + "' to " + target, color=0x00ff00), ephemeral=True)
    await channel.send(Interaction.user.name + " added `" + line + "` to the " + target + " list.\nThere are now " + str(total) + " " + target)

@Bot.tree.command(name="randyremove", description="Remove a random option from a template file")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
@app_commands.describe(target="Which list to remove the line from")
@app_commands.choices(target =[
    app_commands.Choice(name="descriptors", value="descriptors"),
    app_commands.Choice(name="subjects", value="subjects"),
    app_commands.Choice(name="intros", value="intros")
])
async def randy_remove(Interaction: discord.Interaction, target: str, line: str):
    total = templates.remove_from_template(line, target)
    channel = Bot.get_channel(int(setting["channel_id"]))
    if total == -1:
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Could not find '" + line + "' in " + target, color=0xff0000), ephemeral=True)
        return
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Removed '" + line + "' from " + target, color=0x00ff00), ephemeral=True)
    await channel.send(Interaction.user.name + " removed `" + line + "` from the " + target + " list.\nThere are now " + str(total) + " " + target)

@Bot.tree.command(name="randyrandom", description="Send a random message from RandyBOT right now")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
async def randy_random(Interaction: discord.Interaction):
    channel = Bot.get_channel(int(setting["channel_id"]))
    message = templates.build_random_message(setting)
    try:
        await channel.send(message)
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Sent random message", color=0x00ff00), ephemeral=True)
    except Exception as e:
        print(e)
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Failed to send message", color=0xff0000), ephemeral=True)

@Bot.tree.command(name="randyactivate", description="Activate RandyBOT in this channel. Hijacks from previous location.")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
async def randy_activate(Interaction: discord.Interaction):
    setting["channel_id"] = Interaction.channel.id
    print("Attaching to channel " + str(Interaction.channel.id))
    setting["active"] = True
    save_settings(setting)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Activated RandyBOT in this channel", color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randydeactivate", description="Deactivate RandyBOT.")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
async def randy_deactivate(Interaction: discord.Interaction):
    setting["active"] = False
    save_settings(setting)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Deactivated RandyBOT", color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randysetting", description="Adjust RandyBOT settings")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
@app_commands.describe(setting_name="Which setting to change")
@app_commands.choices(setting_name =[
    app_commands.Choice(name="Posting Rate (s)", value="posting_timer"),
    app_commands.Choice(name="Descriptor Recursion Chance (1/X)", value="repetition_odds"),
    app_commands.Choice(name="Max Prompt Length (characters)", value="max_length"),
    app_commands.Choice(name="Number of Prompts", value="num_prompts")
])
async def randy_settings(Interaction: discord.Interaction, setting_name: str, value: str):
    try:
        setting[setting_name] = int(value)
        print("Changed " + setting_name + " to " + str(setting[setting_name]))
        save_settings(setting) #save settings, correct any invalid values
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Changed " + setting_name + " to " + str(setting[setting_name]), color=0x00ff00), ephemeral=True)
    except Exception as e:
        print(e)
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Failed to change " + setting_name + " to " + value, color=0xff0000), ephemeral=True)

Bot.run(TOKEN, log_handler=handler)
