import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import logging
from scripts.settings import get_settings, save_settings
from TemplatePicker import templatePicker
from Tracker import StatTracker
import scripts.templates as templates
import asyncio
import datetime
import random
from dailies import DAILIES_NORMAL
from holidays import HOLIDAYS


load_dotenv()
# These are the environment variables that need to be set in .env, not included in repo
TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
#logger.addHandler(logging.StreamHandler())

statTracker = StatTracker()

intents = discord.Intents.default()
intents.message_content = True

Bot = commands.Bot(command_prefix="/", intents=intents)
tp = templatePicker()
def format_daily_summary(timeframe="today"):
    top_users = statTracker.top_users(timeframe=timeframe)
    top_requests = statTracker.top_requests(timeframe=timeframe)
    if timeframe == "today":
        summary = "### Daily Summary\n"
    elif timeframe == "week":
        summary = "### Weekly Summary\n"
    else:
        summary = "### Monthly Summary\n"

    summary += "**Top 3 Users by Points:**\n"
    if top_users:
        for i, (user, points) in enumerate(top_users, 1):
            summary += f"{i}. {user} - {points} points\n"
    else:
        summary += "No user points recorded in timeframe.\n"

    summary += "\n**Top 3 Requests by Replies:**\n"
    if top_requests:
        server_id = setting.get("server_id")
        channel_id = setting.get("channel_id")
        for i, (post_id, reply_count) in enumerate(top_requests, 1):
            summary += (
                f"{i}. {reply_count} replies - "
                f"[Message ID {post_id}](https://discord.com/channels/{server_id}/{channel_id}/{post_id})\n"
            )
    else:
        summary += "No requests with replies today.\n"

    return summary
setting = get_settings()
cooldown = setting["cooldown_max"] #start at max cooldown
#setting["message_list"] = [] #list of message IDs RandyBot has recently posted

# Track active tasks to prevent duplicate loops
active_tasks = {
    'send_periodically': None,
    'periodic_save': None
}

@Bot.event
async def on_ready():
    logger.info('We have logged in.')
    templates.auto_import()
    logger.info("Current settings:")
    logger.info(setting)
    try:
        synced = await Bot.tree.sync()
        logger.info(synced)
    except Exception as e:
        logger.info("Sync failed")
        logger.error(e)

    # Check if tasks are already running before creating new ones
    global active_tasks
    
    # Create send_periodically task if not already running
    if active_tasks['send_periodically'] is None or active_tasks['send_periodically'].done():
        active_tasks['send_periodically'] = Bot.loop.create_task(send_periodically())
        logger.info("Created new send_periodically task")
    else:
        logger.info("send_periodically task already running, not creating a new one")
    
    # Create periodic_save task if not already running
    if active_tasks['periodic_save'] is None or active_tasks['periodic_save'].done():
        active_tasks['periodic_save'] = Bot.loop.create_task(periodic_save())
        logger.info("Created new periodic_save task")
    else:
        logger.info("periodic_save task already running, not creating a new one")

async def periodic_save():
    while True:
        await asyncio.sleep(3600) #save every hour
        tp.save_templates()

async def send_periodically():
    global cooldown
    time = 0
    while True:
        #does this every loop in case settings change
        channel = Bot.get_channel(int(setting["channel_id"]))

        logger.info("Cooldown: " + str(cooldown) + '  ---  Time Since Last Message: ' + str(time))

        if setting["active"]:
            if setting["mode"] == "random":
                await random_message(channel)
            elif setting["mode"] == "daily":
                await daily_message(channel)
            else:
                logger.error("UNKNOWN MODE. Cannot send message.")

        #wait 10 seconds at a time until the timer is up
        time = 0
        while time < cooldown:
            # Check if (now + 10s) is a new day; if so, send summary as extra message
            now = datetime.datetime.now(datetime.timezone.utc)
            ten_seconds_later = now + datetime.timedelta(seconds=10)
            if ten_seconds_later.date() != now.date():
                if now.weekday() == 6:  # Sunday
                    timeframe = "week"
                # Determine if today is the last day of the month
                now = datetime.datetime.now(datetime.timezone.utc)
                tomorrow = now + datetime.timedelta(days=1)
                if tomorrow.month != now.month:
                    timeframe = "month"
                elif now.weekday() == 6:  # Sunday
                    timeframe = "week"
                else:
                    timeframe = "today"
                summary = format_daily_summary(timeframe=timeframe)
                post = await channel.send(summary)
                logger.info("Summary message sent at end of day (extra message).")
            await asyncio.sleep(10)
            time += 10
        
async def random_message(channel : discord.TextChannel):
    logger.info("Sending random message...")
    message = tp.build_random_message(setting)
    post = await channel.send(message)
    
    #add the message ID to the list of recent messages
    setting["message_list"].append(post.id)
    if len(setting["message_list"]) > setting["lookback"]:
        setting["message_list"].pop(0)
    save_settings(setting)

    #log and set cooldown
    logger.info("Message sent:" + str(post.id) + "\n" + message)
    cooldown = setting["cooldown_max"]

async def daily_message(channel : discord.TextChannel):
    global cooldown
    logger.info("Sending daily message...")
    now = datetime.datetime.now(datetime.timezone.utc)
    logger.info(f"UTC time is {now}")
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    daynumber = now.weekday()
    weeknumber = now.isocalendar()[1]
    # build a [year, 'month-day'] list to check for holidays
    today = [now.year, now.strftime('%m-%d')]
    day = days[daynumber]
    logger.info(f"Today is {today[1]}")

    if not today[1] in HOLIDAYS[today[0]]:
        daily_info = DAILIES_NORMAL[day]
        selection = daily_info[(weeknumber + 0) % len(daily_info)]
    else:
        logger.info(f"Today is a holiday: {HOLIDAYS[today[0]][today[1]]}. Overriding daily message.")
        selection = HOLIDAYS[today[0]][today[1]]

    #rotate through descriptions based on the time of day
    current_time_seconds = (now.hour * 3600 +
                            now.minute * 60 +
                            now.second)
    description_index = (current_time_seconds // cooldown) % len(selection["descriptions"])
    description = selection["descriptions"][description_index]

    message = "## It's " + selection["name"] + "!\n" + description
    post = await channel.send(message)
    logger.info("Message sent:" + str(post.id) + ":\n" + message)

    #add the message ID to the list of recent messages
    setting["message_list"].append(post.id)
    if len(setting["message_list"]) > setting["lookback"]:
        setting["message_list"].pop(0)
    save_settings(setting)
    

#limit to only the requests channel
@Bot.event
async def on_message(message):
    global cooldown
    if not setting["active"]:
        return
    if message.author == Bot.user:
        return
    if message.channel.id != setting["channel_id"]:
        return
    if message.content.startswith("/"):
        return
    if message.reference == None:
        return
    if len(message.attachments) == 0:
        return
    
    #The following code will execute any time a message is replied to with an attachment (image) in the current channel
    refMessage = await message.channel.fetch_message(message.reference.message_id) #get the message that was replied to
    logger.info(f"Message from {str(message.author)} referencing {str(refMessage.author)} message {str(message.reference.message_id)}")
    statTracker.handle_new_reply(
        str(refMessage.author),
        message.reference.message_id,
        str(message.author),
        message.id,
        message.created_at.astimezone(datetime.timezone.utc).isoformat()
    )

    #decrease cooldown if the message is a reply to the bot
    if message.reference.message_id in setting["message_list"]:
        try:
            logger.info("Message from " + str(message.author) + " referencing RandyBot " + str(message.reference.message_id))
            cooldown = max(cooldown - setting["cooldown_adjustment"], setting["cooldown_min"])
            logger.info("Cooldown reduced by " + str(setting["cooldown_adjustment"]) + " seconds to " + str(cooldown))
            await message.add_reaction("⭐")
        except Exception as e:
            logger.info(e)
            logger.info("Cooldown reduction failed")

#show error if failed
@Bot.event
async def on_message_error(ctx, error):
    logger.info(error)

async def is_in_server_list(ctx: discord.Interaction):
    logger.info("incoming `" + ctx.data["name"] + "` command from " + str(ctx.guild_id))
    logger.info("allowed servers: " + str(setting["server_whitelist"]))
    return (ctx.guild_id in setting["server_whitelist"]) or setting["server_whitelist"] == []

# @Bot.tree.command(name="randyadd", description="Add a new random option to a template file")
# @app_commands.default_permissions(manage_messages=True)
# @app_commands.check(is_in_server_list)
# @app_commands.describe(target="Which list to add the new line to")
# @app_commands.choices(target =[
#     app_commands.Choice(name="descriptors", value="descriptors"),
#     app_commands.Choice(name="subjects", value="subjects"),
#     app_commands.Choice(name="intros", value="intros")
# ])
# async def randy_add(Interaction: discord.Interaction, target: str, line: str):
#     total = tp.add_to_template(line, target)
#     if total == -1:
#         await Interaction.response.send_message(content=None, embed=discord.Embed(title="'" + line + "' already exists in " + target, color=0xff0000), ephemeral=True)
#         return
#     await Interaction.response.send_message(content=None, embed=discord.Embed(title="Added `" + line + "` to the " + target + " list.\nThere are now " + str(total) + " " + target, color=0x00ff00), ephemeral=True)

# @Bot.tree.command(name="randyremove", description="Remove a random option from a template file")
# @app_commands.default_permissions(manage_messages=True)
# @app_commands.check(is_in_server_list)
# @app_commands.describe(target="Which list to remove the line from")
# @app_commands.choices(target =[
#     app_commands.Choice(name="descriptors", value="descriptors"),
#     app_commands.Choice(name="subjects", value="subjects"),
#     app_commands.Choice(name="intros", value="intros")
# ])
# async def randy_remove(Interaction: discord.Interaction, target: str, line: str):
#     total = tp.remove_from_template(line, target)
#     if total == -1:
#         await Interaction.response.send_message(content=None, embed=discord.Embed(title="Could not find '" + line + "' in " + target, color=0xff0000), ephemeral=True)
#     else:
#         await Interaction.response.send_message(content=None, embed=discord.Embed(title="Removed `" + line + "` from the " + target + " list.\nThere are now " + str(total) + " " + target, color=0x00ff00), ephemeral=True)

# @Bot.tree.command(name="randyrandom", description="Send a random message from RandyBOT right now")
# @app_commands.default_permissions(manage_messages=True)
# @app_commands.check(is_in_server_list)
# async def randy_random(Interaction: discord.Interaction):
#     channel = Bot.get_channel(int(setting["channel_id"]))
#     message = tp.build_random_message(setting)
#     logger.info("Sending manual message...")
#     logger.info(message)
#     await channel.send(message)
#     await Interaction.response.send_message(content=None, embed=discord.Embed(title="Sent random message", color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randyactivate", description="Activate RandyBOT in this channel. Hijacks from previous location.")
@app_commands.default_permissions(manage_messages=True)
@app_commands.check(is_in_server_list)
async def randy_activate(Interaction: discord.Interaction):
    setting["channel_id"] = Interaction.channel.id
    setting["server_id"] = Interaction.guild_id
    logger.info("Attaching to channel " + str(Interaction.channel.id))
    logger.info("Setting server_id to " + str(Interaction.guild_id))
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
    app_commands.Choice(name="Lookback (messages)", value="lookback"),
    app_commands.Choice(name="Mode (daily/random)", value="mode")
])
async def randy_settings(Interaction: discord.Interaction, setting_name: str, value: str):
    try:
        setting[setting_name] = int(value)
        logger.info("Changed " + setting_name + " to " + str(setting[setting_name]))
        save_settings(setting) #save settings, correct any invalid values
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Changed " + setting_name + " to " + str(setting[setting_name]), color=0x00ff00), ephemeral=True)
    except Exception as e:
        logger.error(e)
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
    stringform += "Active: " + str(setting["active"]) + "\n"
    stringform += "Tracked Users: " + str(statTracker.get_total_users()) + "\n"

    #stringform += "\nIf a message is a reply to one of RandyBot's last " + str(setting["lookback"]) + " messages, the cooldown is reduced by " + str(setting["cooldown_adjustment"]) + " seconds, down to a minimum of " + str(setting["cooldown_min"]) + " seconds."

    await Interaction.response.send_message(content=None, embed=discord.Embed(title="RandyBot", description=stringform, color=0x00ff00), ephemeral=True)

# @Bot.tree.command(name="randysave", description="Save the current templates to disk (otherwise saves every 10 minutes)")
# @app_commands.default_permissions(manage_messages=True)
# @app_commands.check(is_in_server_list)
# async def randy_save(Interaction: discord.Interaction):
#     tp.save_templates()
#     await Interaction.response.send_message(content=None, embed=discord.Embed(title="Saved templates", color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randystats", description="Get stats about a user")
@app_commands.check(is_in_server_list)
async def randy_stats(Interaction: discord.Interaction, user: discord.User):
    user_stats = statTracker.get_user(str(user))
    if user_stats is None:
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="No stats found for " + str(user), color=0xff0000), ephemeral=True)
    else:
        message = "Total Points: " + str(user_stats[1]) + "\n"
        message += "Request Replies: " + str(user_stats[2]) + "\n"
        message += "Successful Requests: " + str(user_stats[3]) + "\n"
        message += "Stars Given: NOT YET TRACKED\n" #+ str(user_stats[4]) + "\n"
        message += "Stars Received: NOT YET TRACKED\n" #+ str(user_stats[5]) + "\n"
        await Interaction.response.send_message(content=None, embed=discord.Embed(title="Stats for " + str(user), description=message, color=0x00ff00), ephemeral=True)
    
@Bot.tree.command(name="randysummary", description="Show today's top users and requests summary")
@app_commands.check(is_in_server_list)
async def randy_summary(Interaction: discord.Interaction):
    # Determine if today is the last day of the month
    now = datetime.datetime.now(datetime.timezone.utc)
    tomorrow = now + datetime.timedelta(days=1)
    if tomorrow.month != now.month:
        timeframe = "month"
    else:
        timeframe = "today"
    summary = format_daily_summary(timeframe=timeframe)
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="RandyBot Daily Summary", description=summary, color=0x00ff00), ephemeral=True)

@Bot.tree.command(name="randyleaderboard", description="Get the top 5 users by points")
@app_commands.check(is_in_server_list)
async def randy_leaderboard(Interaction: discord.Interaction):
    top = statTracker.top_rankings()
    if not top:
        await Interaction.response.send_message(
            content=None,
            embed=discord.Embed(
                title="Leaderboard",
                description="No leaderboard data is available.",
                color=0xff0000
            ),
            ephemeral=True
        )
        return
    message = "Top 5 Users by Points:\n"
    for i in range(len(top)):
        message += str(i+1) + ". " + str(top[i][0]) + " - " + str(top[i][1]) + " points\n"
    await Interaction.response.send_message(content=None, embed=discord.Embed(title="Leaderboard", description=message, color=0x00ff00), ephemeral=True)

Bot.run(TOKEN, log_handler=handler)
