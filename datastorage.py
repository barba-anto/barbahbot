"""
Data is stored on a redis remote db for persistance, to avoid useless
network requests it's also stored locally

Example of a guild data:
{"GUILD_ID" : {
    "INSULTS ACTIVE CHANNELS": [CHANNEL_ID1, CHANNEL_ID2, CHANNEL_ID3]
    "CHANNEL_ID": {
    }
    }
}
"""
from __future__ import annotations

import json
import os

import redis

from logging_setup import get_logger

_LOGGER = get_logger(__name__)

host, port = os.getenv("REDIS_URL").split(':')

r = redis.Redis(host=host, port=port, password=os.getenv("REDIS_PASSWORD"))
r.ping()
_LOGGER.info("Redis login successful!")

localstorage = dict()


def update_localstorage(guild_id: int | str):
    """Updates local data by loading the data in the redis database"""
    guild_id = str(guild_id)
    _LOGGER.info(f"Updating localstorage for guild {guild_id} from redis")
    localstorage[guild_id] = json.loads(r.get(guild_id))


def set_server_data(guild_id: int | str, data: dict):
    """Updates the redis database by uploading a json of the data"""
    r.set(str(guild_id), json.dumps(data))


def get_guilds_ids():
    return localstorage.keys()


def new_guild(guild_id: int | str):
    r.set(str(guild_id), "{}")


def delete_guild_data(guild_id: int | str):
    r.delete(str(guild_id))


def _get_channel_data(guild_id: int | str, channel_id: int | str) -> dict:
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    return localstorage.get(str(guild_id), {channel_id: {}}).get(
        str(channel_id))


def get_daily_tasks(guild_id: int | str, channel_id: int | str) -> list:
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    data = _get_channel_data(guild_id=guild_id, channel_id=channel_id)
    return data.get('daily', [])


def get_weekly_tasks(guild_id: int | str, channel_id: int | str) -> list:
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    data = _get_channel_data(guild_id=guild_id, channel_id=channel_id)
    return data.get('weekly', [])


def new_daily_task(guild_id: int | str, channel_id: int | str, time: str,
                   text: str):
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    new_task = {
        'time': time,
        'text': text,
        'last_execution': None
    }
    if not localstorage.get(guild_id):
        localstorage[guild_id] = {
            channel_id: {
                'daily': [new_task]
            }
        }
    else:
        channel_data = localstorage[guild_id].get(channel_id)
        if channel_data:
            daily_tasks = localstorage[guild_id][channel_id].get('daily', [])
            if daily_tasks:
                localstorage[guild_id][channel_id]['daily'].append(new_task)
                return
        localstorage[guild_id][channel_id]['daily'] = [new_task]

    set_server_data(guild_id, localstorage[guild_id])


def update_daily_task(guild_id: int | str, channel_id: int | str, task_id: int,
                      time: str = None, text: str = None,
                      last_execution: str = None):
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    new_task = {
        'time': time,
        'text': text,
        'last_execution': last_execution
    }
    localstorage[guild_id][channel_id]['daily'].pop(task_id)
    localstorage[guild_id][channel_id]['daily'].append(new_task)
    set_server_data(guild_id, localstorage[guild_id])


def new_weekly_task(guild_id: int, channel_id: int, day: str, time: str,
                    text: str):
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    new_task = {
        'day': day,
        'time': time,
        'text': text,
        'last_execution': None
    }

    if not localstorage.get(guild_id):
        localstorage[guild_id] = {
            channel_id: {
                'weekly': [new_task]
            }
        }
    else:
        channel_data = localstorage[guild_id].get(channel_id)
        if channel_data:
            weekly_tasks = localstorage[guild_id][channel_id].get('weekly', [])
            if weekly_tasks:
                localstorage[guild_id][channel_id]['weekly'].append(new_task)
                return
        localstorage[guild_id][channel_id]['weekly'] = [new_task]

    set_server_data(guild_id, localstorage[guild_id])


def update_weekly_task(guild_id: int | str, channel_id: int | str,
                       task_id: int, day: str,
                       time: str, text: str, last_execution: str):
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    new_task = {
        'day': day,
        'time': time,
        'text': text,
        'last_execution': last_execution
    }
    localstorage[guild_id][channel_id]['weekly'].pop(task_id)
    localstorage[guild_id][channel_id]['weekly'].append(new_task)
    set_server_data(guild_id, localstorage[guild_id])


def delete_daily_task(guild_id: int|str, channel_id: int|str, task_id: int):
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    if localstorage.get(guild_id):
        channel_data = localstorage[guild_id].get(channel_id)
        if channel_data:
            daily_tasks = localstorage[guild_id][channel_id].get('daily', [])
            if daily_tasks:
                localstorage[guild_id][channel_id]['daily'].pop(task_id)


def delete_weekly_task(guild_id: int|str, channel_id: int|str, task_id: int):
    guild_id = str(guild_id)
    channel_id = str(channel_id)
    if localstorage.get(guild_id):
        channel_data = localstorage[guild_id].get(channel_id)
        if channel_data:
            weekly_tasks = localstorage[guild_id][channel_id].get('weekly', [])
            if weekly_tasks:
                localstorage[guild_id][channel_id]['weekly'].pop(task_id)


for key in r.keys():
    update_localstorage(key.decode())
