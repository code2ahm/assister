import discord, json, os
from discord.ext import commands

prefix_file = "prefixes.json"
noprefix_file = "noprefix.txt"

def load_prefixes():
    if os.path.exists(prefix_file):
        try:
            with open(prefix_file, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

def save_prefixes(prefixes):
    with open(prefix_file, "w") as file:
        json.dump(prefixes, file, indent=4)

prefixes = load_prefixes()

def load_noprefixes():
    if os.path.exists(noprefix_file):
        try:
            with open(noprefix_file, "r") as file:
                return set(map(int, file.read().splitlines()))
        except ValueError:
            return set()
    return set()

def save_noprefix(noprefix):
    with open(noprefix_file, "w") as file:
        file.write("\n".join(map(str, noprefix)))

noprefix = load_noprefixes()

def np_ids():
    return noprefix

def guild_prefix(guild_id):
    return prefixes.get(guild_id, '.')

async def get_prefix(bot, message):
    if isinstance(message.channel, discord.DMChannel):
        return

    if message.guild:
        guild_id = str(message.guild.id)
        if message.author.id in np_ids():
            return commands.when_mentioned_or(guild_prefix(guild_id), '')(bot, message)
        
        return commands.when_mentioned_or(guild_prefix(guild_id))(bot, message)

    return