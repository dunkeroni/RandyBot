import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import logging
from scripts.settings import get_settings, save_settings
from TemplatePicker import templatePicker
import scripts.templates as templates
import asyncio


load_dotenv()
# These are the environment variables that need to be set in .env, not included in repo
TOKEN = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()

Bot = commands.Bot(command_prefix="/", intents=intents)
tp = templatePicker()
setting = get_settings()
cooldown = setting["cooldown_max"] #start at max cooldown
references = [] #list of message IDs RandyBot has recently posted

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
    Bot.loop.create_task(periodic_save())

async def periodic_save():
    while True:
        await asyncio.sleep(600) #save every 10 minutes
        tp.save_templates()

async def send_periodically():
    global cooldown
    while True:
        #does this every loop in case settings change
        channel = Bot.get_channel(int(setting["channel_id"]))
        if setting["active"]:
            print("Sending message...")
            message = tp.build_random_message(setting)
            post = await channel.send(message)
            
            #add the message ID to the list of recent messages
            references.append(post.id)
            if len(references) > setting["lookback"]:
                references.pop(0)

            #log and set cooldown
            print("Message sent:" + str(post.id))
            print(message)
            cooldown = setting["cooldown_max"]

        #wait 10 seconds at a time until the timer is up
        time = 0
        while time < cooldown:
            await asyncio.sleep(10)
            time += 10

#limit to only the requests channel
@Bot.event
async def on_message(message):
    global cooldown
    if message.author == Bot.user:
        return
    if message.channel.id != setting["channel_id"]:
        return
    if message.content.startswith("/"):
        return
    if setting["active"]:
        #decrease cooldown if the message is a reply to the bot
        if message.reference != None:
            if message.reference.message_id in references and len(message.attachments):
                try:
                    print("Message from " + str(message.author) + " referencing RandyBot " + str(message.reference.message_id))
                    cooldown = max(cooldown - setting["cooldown_adjustment"], setting["cooldown_min"])
                    print("Cooldown reduced by " + str(setting["cooldown_adjustment"]) + " seconds to " + str(cooldown))
                    await message.add_reaction("⭐")
                except Exception as e:
                    print(e)
                    print("Cooldown reduction failed")

#show error if failed
@Bot.event
async def on_message_error(ctx, error):
    print(error)

async def is_in_server_list(ctx: discord.Interaction):
    print("incoming `" + ctx.data["name"] + "` command from " + str(ctx.guild_id))
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
    total = tp.add_to_template(line, target)
    if total == -1:
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="'" + line + "' already exists in " + target, color=0xff0000), ephemeral=True)
        return
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Added `" + line + "` to the " + target + " list.\nThere are now " + str(total) + " " + target, color=0x00ff00), ephemeral=True)

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
    total = tp.remove_from_template(line, target)
    if total == -1:
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Could not find '" + line + "' in " + target, color=0xff0000), ephemeral=True)
    else:
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Removed `" + line + "` from the " + target + " list.\nThere are now " + str(total) + " " + target, color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randyrandom", description="Send a random message from RandyBOT right now")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
async def randy_random(Interaction: discord.Interaction):
    channel = Bot.get_channel(int(setting["channel_id"]))
    message = tp.build_random_message(setting)
    print("Sending manual message...")
    print(message)
    await channel.send(message)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Sent random message", color=0x00ff00), ephemeral=True)

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
    #app_commands.Choice(name="Posting Rate (s)", value="posting_timer"),
    app_commands.Choice(name="Descriptor Recursion Chance (1/X)", value="repetition_odds"),
    app_commands.Choice(name="Max Prompt Length (characters)", value="max_length"),
    app_commands.Choice(name="Number of Prompts", value="num_prompts"),
    app_commands.Choice(name="Cooldown Max (s)", value="cooldown_max"),
    app_commands.Choice(name="Cooldown Min (s)", value="cooldown_min"),
    app_commands.Choice(name="Cooldown Adjustment per reply (s)", value="cooldown_adjustment"),
    app_commands.Choice(name="Lookback (messages)", value="lookback")
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

#randy info command
@Bot.tree.command(name="randyinfo", description="Get info about RandyBOT and current settings")
@app_commands.check(is_in_server_list)
async def randy_info(Interaction: discord.Interaction):
    desc = """A bot that generates random prompts for the requests channel.
    Community Watch roles and up can control this bot and add/remove words from the prompt lists.
    If you have questions, suggestions, or want to report a bug, contact dunkeroni on Discord."""
    length = tp.info()
    stringform = desc + "\n"
    stringform += "Source Code: https://github.com/dunkeroni/RandyBot \n"
    stringform += "Current message rate: " + str(setting["cooldown_max"]) + " seconds\n"
    stringform += "Prompts per message: " + str(setting["num_prompts"]) + "\n"
    stringform += "Consecutive descriptor chance: 1 in " + str(setting["repetition_odds"]) + "\n"
    stringform += "Active: " + str(setting["active"]) + "\n"
    stringform += "Current number of descriptors: " + str(length["descriptors"]) + "\n"
    stringform += "Current number of subjects: " + str(length["subjects"]) + "\n"
    stringform += "Current number of intros: " + str(length["intros"]) + "\n"

    stringform += "\nIf a message is a reply to one of RandyBot's last " + str(setting["lookback"]) + " messages, the cooldown is reduced by " + str(setting["cooldown_adjustment"]) + " seconds, down to a minimum of " + str(setting["cooldown_min"]) + " seconds."

    await Interaction.response.send_message(content=None, embed=discord.Embed(title="RandyBot", description=stringform, color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randysave", description="Save the current templates to disk (otherwise saves every 10 minutes)")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
async def randy_save(Interaction: discord.Interaction):
    tp.save_templates()
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Saved templates", color=0x00ff00), ephemeral=True)

Bot.run(TOKEN, log_handler=handler)
