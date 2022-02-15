# -*- coding: utf-8 -*-
import discord

import enums

task_types = discord.Option(str, name='task-type',
                            description='Type of the task',
                            choices=enums.tasks_types)

task_id = discord.Option(int, name='task-id',
                         description="The task ID. To know the ID "
                                     "use the command /show_tasks")

hhmm = discord.Option(str, name='hhmm', description="Time of the day at which "
                                                    "the task should run.\n"
                                                    "The time is in CET time")

weekdays = discord.Option(str, name='day-of-the-week',
                          description='Day on which the task should run',
                          choices=enums.daysoftheweek)

message = discord.Option(str, name="message",
                         description="The text that you want to send. "
                                     "Tags are allowed")
