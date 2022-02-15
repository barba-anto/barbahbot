import os
from datetime import datetime

import discord
from discord.ext import commands, tasks

import datastorage
import enums
import options
from datastorage import update_daily_task, update_weekly_task
from logging_setup import get_logger

description = """An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here."""

intents = discord.Intents.default()
intents.members = True

if os.getenv("DEBUG_SERVER_IDS", []):
    # DEBUG_SERVER_IDS = [int(i) for i in os.getenv("DEBUG_SERVER_IDS").split(',')]
    DEBUG_SERVER_IDS = [943104380448681987, 669694248756445225]
else:
    DEBUG_SERVER_IDS = None

_LOGGER = get_logger(__name__)


class MyBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.activity = discord.Activity(name='Your peepee pics :eyes:',
                                         type=discord.ActivityType.watching)

        # Start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        _LOGGER.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        _LOGGER.info("------")

    async def on_application_command_error(self,
                                           ctx: discord.ApplicationContext,
                                           exception: commands.MissingPermissions):
        if type(exception) == commands.MissingPermissions:
            await ctx.respond(
                "You dont have the permissions to run this command!")
            _LOGGER.warning(f"User {ctx.user} tried to run command "
                            f"without sufficent permissions! "
                            f"Permissions required: "
                            f"{', '.join(exception.missing_permissions)}")
        else:
            await super(MyBot, self).on_application_command_error(ctx,
                                                                  exception)

    async def on_guild_remove(self, guild: discord.Guild):
        _LOGGER.info(f"Removed from guild {guild.name} ({guild.id})")
        datastorage.delete_guild_data(guild.id)

    async def on_guild_join(self, guild: discord.Guild):
        _LOGGER.info(f"Joined new guild {guild.name} ({guild.id})")
        datastorage.new_guild(guild.id)

    async def on_message(self, message: discord.Message):
        content = message.content.lower()

        # We do not want the bot to reply to itself
        if message.author.id == bot.user.id:
            return

        await self.process_commands(message)

    @tasks.loop(seconds=1)  # Task that runs every 1 second
    async def my_background_task(self):
        now = datetime.now()
        now_hm = now.strftime('%H:%M')
        now_ymdhm = now.strftime('%Y-%m-%d %H:%M')
        weekday = str(now.weekday())
        for guild in datastorage.localstorage.keys():
            for ch_id in datastorage.localstorage[guild].keys():
                ch = self.get_channel(int(ch_id))
                if ch:
                    for task_id, t in enumerate(
                            datastorage.get_daily_tasks(guild, ch_id)):
                        if now_hm == t['time'] and t[
                            'last_execution'] != now_ymdhm:
                            _LOGGER.info(f"Executing daily task {task_id}!")
                            await ch.send(t['text'])
                            update_daily_task(guild, ch_id, task_id,
                                              time=t['time'], text=t['text'],
                                              last_execution=now_ymdhm)
                    for task_id, t in enumerate(
                            datastorage.get_weekly_tasks(guild, ch_id)):
                        if ch:
                            if weekday == t['day'] and now_hm == t['time'] and \
                                    t['last_execution'] != now_ymdhm:
                                _LOGGER.info(
                                    f"Executing weekly task {task_id}!")
                                await ch.send(t['text'])
                                update_weekly_task(guild, ch_id, task_id,
                                                   day=t['day'],
                                                   time=t['time'],
                                                   text=t['text'],
                                                   last_execution=now_ymdhm)


bot = MyBot(command_prefix="!", description=description, intents=intents)


# @bot.command()
# @commands.has_permissions(manage_channels=True)
# async def daily(ctx: commands.context.Context, hhmm, *message):
#     """Sends a message every day at a predetermined time. The time MUST be in HH:MM format.
#
#     Usage: !daily HH:MM PUT HERE YOUR MESSAGE"""
#     try:
#         datetime.strptime(hhmm, '%H:%M')
#     except ValueError:
#         await ctx.reply("First argument not matching HH:MM format!")
#         return
#
#     _LOGGER.info("Adding to daily tasks")
#     datastorage.new_daily_task(ctx.guild.id, ctx.channel.id, hhmm,
#                                ' '.join(message))


@bot.slash_command(guild_ids=DEBUG_SERVER_IDS)
async def info(ctx):
    await ctx.respond("This bot was made by BarbaH#2895.\n"
                      "If you have any issue with the bot "
                      "just pretend you didn't see anything")


@bot.slash_command(guild_ids=DEBUG_SERVER_IDS,
                   default_permissions=False)
@commands.has_permissions(manage_channels=True)
async def weekly(ctx: discord.ApplicationContext,
                 dayoftheweek: options.weekdays,
                 hhmm: options.hhmm, message: options.message):
    """Sends a message once in a week at a predetermined day and time.
    Days must be from 0 (MONDAY) to 6 (SUNDAY)
    The time MUST be in HH:MM format.

    Usage: /daily DAYFROMZEROTOSIX HH:MM PUT HERE YOUR MESSAGE
    """
    if dayoftheweek.lower().strip() not in enums.daysoftheweek:
        await ctx.respond("This day of the week doesn't exists")
        return

    try:
        datetime.strptime(hhmm, '%H:%M')
    except ValueError:
        await ctx.respond("The hhmm argument is not matching HH:MM format!")
        return

    _LOGGER.info("Adding to weekly tasks")
    datastorage.new_weekly_task(ctx.guild.id, ctx.channel.id,
                                dayoftheweek, hhmm, message)
    await ctx.respond("Weekly reminder addedd succesfully")


@bot.slash_command(guild_ids=DEBUG_SERVER_IDS,
                   default_permissions=False)
@commands.has_permissions(manage_channels=True)
async def daily(ctx: discord.ApplicationContext, hhmm: options.hhmm,
                message: options.message):
    """Sends a message every day at a predetermined time. The time MUST be in HH:MM format.

    Usage: /daily HH:MM PUT HERE YOUR MESSAGE
    """
    try:
        datetime.strptime(hhmm, '%H:%M')
    except ValueError:
        await ctx.respond("First argument not matching HH:MM format!")
        return

    _LOGGER.info("Adding to daily tasks")
    datastorage.new_daily_task(ctx.guild.id, ctx.channel.id, hhmm, message)
    await ctx.respond("Daily reminder addedd succesfully")


# @bot.command()
# @commands.has_permissions(manage_channels=True)
# async def weekly(ctx: commands.context.Context, dayoftheweek, hhmm, *message):
#     """Sends a message every day at a predetermined time. The time MUST be in HH:MM format.
#
#     Usage: !daily HH:MM PUT HERE YOUR MESSAGE"""
#     try:
#         if int(dayoftheweek) < 0 or int(dayoftheweek) > 6:
#             raise ValueError
#     except ValueError:
#         await ctx.reply(
#             "The day of the week must be a number between 0 (Monday) and 6 (Sunday)")
#     try:
#         datetime.strptime(hhmm, '%H:%M')
#     except ValueError:
#         await ctx.reply("First argument not matching HH:MM format!")
#         return
#
#     _LOGGER.info("Adding to daily tasks")
#     datastorage.new_weekly_task(ctx.guild.id, ctx.channel.id, dayoftheweek,
#                                 hhmm, ' '.join(message))


@bot.slash_command(guild_ids=DEBUG_SERVER_IDS,
                   default_permissions=False)
@commands.has_permissions(manage_channels=True)
async def delete_task(ctx: discord.ApplicationContext,
                      task_type: options.task_types,
                      task_id: options.task_id):
    """Delete a task in this channel, you have to specify the type of the task

    Usage: /delete task
    """

    task_type = task_type.lower().strip()
    if task_type == 'daily':
        datastorage.delete_daily_task(ctx.guild.id, ctx.channel.id, task_id)
    elif task_type == 'weekly':
        datastorage.delete_weekly_task(ctx.guild.id, ctx.channel.id, task_id)
    _LOGGER.info("Task deleted succesfully")

    await ctx.respond("Task deleted succesfully")


@bot.slash_command(guild_ids=DEBUG_SERVER_IDS,
                   default_permissions=False, )
@commands.has_permissions(manage_channels=True)
async def show_tasks(ctx: discord.ApplicationContext,
                     task_type: options.task_types):
    """Show the active tasks in this channel, you have to specify the type of the task

    Usage example: /show_tasks weekly
    :param  task_type: Type of the task, daily or weekly
    :param task_id: Use HH:MM format
    """

    task_type = task_type.lower().strip()
    if task_type == 'daily':
        _tasks = datastorage.get_daily_tasks(ctx.guild.id, ctx.channel.id)
    elif task_type == 'weekly':
        _tasks = datastorage.get_weekly_tasks(ctx.guild.id, ctx.channel.id)
    else:
        await ctx.respond(f"Task of type {task_type} does not exist")
        return

    if not _tasks:
        await ctx.respond(f"No {task_type} tasks found")
        return

    response = "##############\n"
    for task_id, task in enumerate(_tasks):
        response += f"TASK {task_id}\n"
        if task_type == 'weekly':
            response += f"Activation day: {task['day']}\n"
        response += f"Activation time: {task['time']}\n"
        response += f"Message: {task['text']}\n"
        response += f"##############\n\n"

    await ctx.respond(response)


bot.run(os.getenv('DISCORD_TOKEN'))
