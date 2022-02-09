# This example requires the 'members' privileged intents

import random
import discord
import os
from discord.ext import commands, tasks
from datetime import datetime

from tasks import daily_tasks

description = """An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here."""

intents = discord.Intents.default()
intents.members = True


class MyBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.activity = discord.Activity(name='Your peepee pics', type=discord.ActivityType.watching)

        # Start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")
        print("------")

    async def on_message(self, message: discord.Message):
        content = message.content.lower()

        # We do not want the bot to reply to itself
        if message.author.id == bot.user.id:
            return

        if content.startswith("dickpick"):
            await message.reply("Hello!", mention_author=True)

        idx = content.find("stfu")
        if idx >= 0:
            await message.channel.send(f"Yeah, stfu {content[idx+len('stfu'):]}")

        await self.process_commands(message)

    @tasks.loop(seconds=1)  # Task that runs every 60 seconds
    async def my_background_task(self):
        now = datetime.now()
        now_ymd = now.strftime('%Y-%m-%d')
        now_hm = now.strftime('%H:%M')
        for ch_id, ch_tasks in daily_tasks.items():
            ch = self.get_channel(ch_id)
            for task in ch_tasks:
                if now_hm == task['execution_time'] and task['last_execution'] != now_ymd:
                    print("Executing task!")
                    await ch.send(task['text'])
                    task['last_execution'] = now_ymd


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

    print("Adding to daily tasks")
    if not daily_tasks.get(ctx.channel.id):
        daily_tasks[ctx.channel.id] = []

    daily_tasks[ctx.channel.id].append({
        'execution_time': hhmm,
        'last_execution': '',
        'text': ' '.join(message)
    })

    print(ctx.channel.id, hhmm, message)


@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split("d"))
    except Exception:
        await ctx.send("Format has to be in NdN!")
        return

    result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)


bot.run(os.getenv('DISCORD_TOKEN'))
