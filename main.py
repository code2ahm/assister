import discord
import asyncio
import logging
import os
from datetime import datetime
import time
import aiohttp
from discord import app_commands, ui
from discord.ext import commands
from colorlog import ColoredFormatter
import traceback

import sys
sys.dont_write_bytecode = True
from utils.token    import TOKEN
from utils.prefixes import *
from utils.variables import *
from utils.checks   import *
from utils.helplund import *
from utils.loads import *
from utils.blacklists import *
from utils.paginator import Ahm




intents = discord.Intents.default()
intents.message_content = True
intents.members         = True
intents.guilds          = True

client = commands.Bot(
    command_prefix     = get_prefix,
    intents            = intents,
    case_insensitive   = True,
    strip_after_prefix = True,
)
client.remove_command("help")

handler = logging.StreamHandler()

formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s | %(message)s",
    datefmt="%H:%M:%S",
    log_colors={
        "DEBUG":    "cyan",
        "INFO":     "green",
        "WARNING":  "yellow",
        "ERROR":    "red",
        "CRITICAL": "bold_red",
    }
)

handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(handler)





@client.event
async def on_ready():
    await client.change_presence(activity=discord.CustomActivity(name=".help | assisterbot.xyz"))

    cmds    = len(client.commands)
    subcmds = sum(len(c.commands) for c in client.commands if hasattr(c, "commands"))

    try:
        synced = await client.tree.sync()
        slash  = len(synced)
    except Exception as e:
        logging.error(f"Slash sync failed: {e}")
        slash = 0

    logging.info(f"Logged     : {client.user}")
    logging.info(f"Guilds     : {len(client.guilds)}")
    logging.info(f"Users      : {len(client.users)}")
    logging.info(f"Prefix cmds: {cmds} | Subcmds: {subcmds}")
    logging.info(f"Slash cmds : {slash}")
    logging.info(f"Total cmds : {cmds + subcmds}")




async def _webhook_send(url: str, content: str):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(url, session=session)

        if len(content) <= 2000:
            await webhook.send(content)
        else:
            for i in range(0, len(content), 1900):
                await webhook.send(content[i:i+1900])


async def log_cooldown(cmd, user, guild, guild_id, user_id, retry_after):
    msg = (
        f"- ❗ **Cooldown Triggered**\n"
        f"  - **Guild:** {guild} (`{guild_id}`)\n"
        f"  - **User:** {user} (`{user_id}`)\n"
        f"  - **Command:** `{cmd}`\n"
        f"  - **Cooldown:** `{retry_after:.2f}s`"
    )
    await _webhook_send(ahmw2, msg)


async def log_command(cmd_usage, user, guild, guild_id, user_id, content, success, error=None):
    status = "✅ Executed" if success else "❌ Failed"

    msg = (
        f"**Command Log**\n"
        f"**Guild:** {guild} (`{guild_id}`)\n"
        f"**User:** {user} (`{user_id}`)\n"
        f"**Command:** `{cmd_usage}`\n"
        f"**Raw:** `{content[:1000]}`\n"
        f"**Status:** {status}\n"
    )

    if error:
        err = error[:1500]
        msg += f"```py\n{err}\n```"

    await _webhook_send(ahmw1, msg)






_cooldown_notified: set = set()

async def _clear_cooldown_flag(user_id: int):
    await asyncio.sleep(10)
    _cooldown_notified.discard(user_id)


async def chuttt(ctx: commands.Context, **kwargs):
    try:
        if ctx.interaction:
            if ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(**kwargs, ephemeral=True)
            else:
                await ctx.interaction.response.send_message(**kwargs, ephemeral=True)
        else:
            await ctx.reply(**kwargs, mention_author=False)
    except (discord.NotFound, discord.HTTPException):
        pass 


@client.event
async def on_command_error(ctx: commands.Context, error):

    if isinstance(error, commands.CheckFailure):
        return
        
    if isinstance(error, commands.CommandOnCooldown):
        uid = ctx.author.id
        if uid not in _cooldown_notified:
            _cooldown_notified.add(uid)
            embed = discord.Embed(
                description=f"❗ Command on cooldown. Try again in `{error.retry_after:.2f}s`.",
                color=colour,
            )
            embed.set_author(name="Assister Slowdown", icon_url=client.user.avatar.url)
            await chuttt(ctx, embed=embed, delete_after=6)
            client.loop.create_task(_clear_cooldown_flag(uid))

        await log_cooldown(
            ctx.command.name, ctx.author.display_name,
            ctx.guild.name, ctx.guild.id,
            ctx.author.id, error.retry_after,
        )

    elif isinstance(error, commands.MissingRequiredArgument):
        prefix = guild_prefix(str(ctx.guild.id)) if ctx.guild else "."
        embed = discord.Embed(
            description=(
                f"{cross} | You missed the `{error.param.name}` argument\n"
                f"{e_dot} Correct usage:```{prefix}{ctx.command.usage}```"
            ),
            color=colour,
        )
        embed.set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
        )
        await chuttt(ctx, embed=embed, delete_after=10)

    elif isinstance(error, commands.MissingPermissions):
        missing = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
        embed = discord.Embed(
            description=f"## {animated_cross} **Missing Permissions**\n```py\nYou need: {missing}```",
            color=colour,
        )
        embed.set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
        )
        await chuttt(ctx, embed=embed)

    elif isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
        embed = discord.Embed(
            description=f"## {animated_cross} **Bot Missing Permissions**\n```py\nI need: {missing}```",
            color=colour,
        )
        embed.set_author(name=client.user, icon_url=client.user.avatar.url)
        await chuttt(ctx, embed=embed)

    elif isinstance(error, commands.MemberNotFound):
        embed = discord.Embed(
            description=f"{cross} | Member not found. That user is not in this server.",
            color=colour,
        )
        embed.set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
        )
        await chuttt(ctx, embed=embed, delete_after=10)

    elif isinstance(error, commands.CommandNotFound):
        return

    else:
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logging.error(f"[COMMAND ERROR] {ctx.command} | {ctx.author} | {ctx.guild}\n{tb}")

        await log_command(
            ctx.command.name if ctx.command else "unknown",
            ctx.author.display_name,
            ctx.guild.name if ctx.guild else "DM",
            ctx.guild.id if ctx.guild else "DM",
            ctx.author.id,
            ctx.message.content,
            False,
            tb,
        )

        await chuttt(
            ctx,
            embed=discord.Embed(
                description=f"{cross} An unexpected error occurred.",
                color=colour,
            ),
            delete_after=8,
        )





@client.event
async def on_command_completion(ctx: commands.Context):
    try:
        await log_command(
            ctx.command.usage, ctx.author.display_name,
            ctx.guild.name, ctx.guild.id,
            ctx.author.id, ctx.message.content, True,
        )
    except Exception as e:
        await log_command(
            ctx.command.usage, ctx.author.display_name,
            ctx.guild.name, ctx.guild.id,
            ctx.author.id, ctx.message.content, False, str(e),
        )




@client.hybrid_command(
    aliases     = ["allcmds", "allcommands", "cmds", "commands"],
    usage       = "commands",
    description = "Shows all my commands",
)
@bled()
@commands.cooldown(1, 8, commands.BucketType.user)
async def mycommand(ctx: commands.Context):

    cmds    = len(client.commands)
    subcmds = sum(len(c.commands) for c in client.commands if hasattr(c, "commands"))
    
    total = cmds + subcmds
    pages = []

    for category, cmds in lul.items():
        cmd_list = ", ".join(f"`{c}`" for c in cmds)
        embed = discord.Embed(
            description=f"## {category.capitalize()} — {len(cmds)} commands\n{cmd_list}\n{blnk}",
            color=colour,
        )
        embed.set_footer(
            text     = f"{client.user.display_name} • Page {len(pages)+1}/{len(lul)} • Total: {total}",
            icon_url = client.user.avatar.url,
        )
        embed.set_author(name=f"Total: {total} commands", icon_url=client.user.avatar.url)
        pages.append(embed)

    await Ahm(pages).start(ctx)







@client.command(aliases=['r'])
@is_developer()
async def reload(ctx, cog: str = None):
    if cog is None:
        return await ctx.send("Please specify a cog or use `all`.")

    if cog.lower() == "all":
        success = []
        failed = []

        for extension in list(client.extensions):
            try:
                await client.reload_extension(extension)
                success.append(extension)
            except Exception as e:
                failed.append((extension, str(e)))

        msg = f"{tick} Reloaded {len(success)} cogs."
        if failed:
            msg += f"\n{animated_cross} Failed: " + ", ".join(f"`{name}`" for name, _ in failed)

        await ctx.send(msg)
    else:
        try:
            await client.reload_extension(f"cogs.{cog}")
            await ctx.send(f"{tick} Reloaded `{cog}`")
        except Exception as e:
            await ctx.send(f"{animated_cross} Error: `{e}`")


@client.command()
@is_developer()
async def cmdids(ctx):
    cmds = await client.tree.fetch_commands()
    lines = [f"`{c.name}` → `{c.id}`" for c in cmds]

    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > 2000:
            chunks.append(current)
            current = ""
        current += line + "\n"

    if current:
        chunks.append(current)

    if ctx.interaction:  
        await ctx.interaction.response.send_message(chunks[0], ephemeral=True)
        for chunk in chunks[1:]:
            await ctx.followup.send(chunk, ephemeral=True)
    else: 
        for chunk in chunks:
            await ctx.send(chunk)



async def load_extensions():
    for root, _, files in os.walk("./cogs"):
        for file in files:
            if not file.endswith(".py"):
                continue
            rel  = os.path.relpath(os.path.join(root, file), "./cogs").replace(os.sep, ".")
            name = f"cogs.{rel[:-3]}"
            try:
                await client.load_extension(name)
                print(f"Loaded  {name}")
            except Exception as e:
                print(f"Failed  {name}: {e}")


async def main():
    await load_extensions()
    try:
        await client.load_extension("jishaku")
        print("Loaded  jishaku")
    except Exception:
        print("jishaku not installed — skipping")
    await client.start(TOKEN)


asyncio.run(main())