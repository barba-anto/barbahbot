import discord
import os
from discord.ext import commands, tasks
from datetime import datetime

import datastorage
from datastorage import update_daily_task, update_weekly_task, get_guilds_ids

from logging_setup import get_logger

description = """An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here."""

intents = discord.Intents.default()
intents.members = True

_LOGGER = get_logger(__name__)


class MyBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.activity = discord.Activity(name='Your peepee pics', type=discord.ActivityType.watching)

        # Start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        _LOGGER.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        _LOGGER.info("------")

    async def on_message(self, message: discord.Message):
        content = message.content.lower()

        # We do not want the bot to reply to itself
        if message.author.id == bot.user.id:
            return

        if content.startswith("dickpick"):
            await message.reply("Hello!", mention_author=True)

        idx = content.find("stfu")
        if idx >= 0:
            await message.channel.send(f"Yeah, stfu {content[idx + len('stfu'):]}")

        await self.process_commands(message)

    @tasks.loop(seconds=1)  # Task that runs every 60 seconds
    async def my_background_task(self):
        now = datetime.now()
        now_hm = now.strftime('%H:%M')
        now_ymdhm = now.strftime('%Y-%m-%d %H:%M')
        weekday = str(now.weekday())
        for guild in datastorage.localstorage.keys():
            for ch_id in datastorage.localstorage[guild].keys():
                ch = self.get_channel(int(ch_id))
                if ch:
                    for task_id, t in enumerate(datastorage.get_daily_tasks(guild, ch_id)):
                        if now_hm == t['time'] and t['last_execution'] != now_ymdhm:
                            _LOGGER.info(f"Executing daily task {task_id}!")
                            await ch.send(t['text'])
                            update_daily_task(guild, ch_id, task_id, time=t['time'], text=t['text'],
                                              last_execution=now_ymdhm)
                    for task_id, t in enumerate(datastorage.get_weekly_tasks(guild, ch_id)):
                        if ch:
                            if weekday == t['day'] and now_hm == t['time'] and t['last_execution'] != now_ymdhm:
                                _LOGGER.info(f"Executing weekly task {task_id}!")
                                await ch.send(t['text'])
                                update_weekly_task(guild, ch_id, task_id, day=t['day'], time=t['time'],
                                                   text=t['text'], last_execution=now_ymdhm)


bot = MyBot(command_prefix="!", description=description, intents=intents)


@bot.command()
async def daily(ctx: commands.context.Context, hhmm, *message):
    """Sends a message every day at a predetermined time. The time MUST be in HH:MM format.

    Usage: !daily HH:MM PUT HERE YOUR MESSAGE"""
    try:
        datetime.strptime(hhmm, '%H:%M')
    except ValueError:
        await ctx.reply("First argument not matching HH:MM format!")
        return

    _LOGGER.info("Adding to daily tasks")
    datastorage.new_daily_task(ctx.guild.id, ctx.channel.id, hhmm, ' '.join(message))


@bot.slash_command(guild_ids=[int(g) for g in get_guilds_ids()])
async def daily(ctx: discord.ApplicationContext, hhmm, message):
    """Sends a message every day at a predetermined time. The time MUST be in HH:MM format.

    Usage: /daily HH:MM PUT HERE YOUR MESSAGE
    :param hhmm: "Use HH:MM format"
    """
    try:
        datetime.strptime(hhmm, '%H:%M')
    except ValueError:
        await ctx.respond("First argument not matching HH:MM format!")
        return

    _LOGGER.info("Adding to daily tasks")
    datastorage.new_daily_task(ctx.guild.id, ctx.channel.id, hhmm, message)
    await ctx.respond("Daily reminder addedd succesfully")

@bot.command()
async def weekly(ctx: commands.context.Context, dayoftheweek, hhmm, *message):
    """Sends a message every day at a predetermined time. The time MUST be in HH:MM format.

    Usage: !daily HH:MM PUT HERE YOUR MESSAGE"""
    try:
        if int(dayoftheweek) < 0 or int(dayoftheweek) > 6:
            raise ValueError
    except ValueError:
        await ctx.reply("The day of the week must be a number between 0 (Monday) and 6 (Sunday)")
    try:
        datetime.strptime(hhmm, '%H:%M')
    except ValueError:
        await ctx.reply("First argument not matching HH:MM format!")
        return

    _LOGGER.info("Adding to daily tasks")
    datastorage.new_weekly_task(ctx.guild.id, ctx.channel.id, dayoftheweek, hhmm, ' '.join(message))


bot.run(os.getenv('DISCORD_TOKEN'))
