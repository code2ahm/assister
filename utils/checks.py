import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from collections import Counter
from utils.blacklists import *
from utils.variables import *

def bled(): 
    async def predicate(ctx: commands.Context):
        if ctx.author.id in blacklisted_users:
            embed = discord.Embed(
                title="",
                description=f"{animated_cross} **You are blacklisted**\n{e_dot} You are blacklisted globally and can't use any command.\n<:fn_verify:1123230264445915296> Join **{support_server}** to appeal!",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

            raise commands.CheckFailure("Loda")
        return True
    return commands.check(predicate)


def bledslash(): 
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id in blacklisted_users:
            embed = discord.Embed(
                title="",
                description=f"{animated_cross} **You are blacklisted**\n{e_dot} You are blacklisted globally and can't use any command.\n<:fn_verify:1123230264445915296> Join **{support_server}** to appeal!",
                color=colour
            )
            embed.set_user(name=interaction.user, icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
            await interaction.response.send_message(embed=embed)

            raise commands.CheckFailure("Loda")
        return True
    return commands.check(predicate)


def admin():
    async def predicate(ctx: commands.Context):
        if not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="",
                description=f"## {animated_cross} **Missing Permissions**\n```yaml\nYou miss Administrator permissions```",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

            raise commands.CheckFailure("Loda")
        return True
    return commands.check(predicate)


def aboveb():
    async def predicate(ctx: commands.Context):
        author_top_role = ctx.author.top_role
        bot_top_role = ctx.guild.me.top_role

        if author_top_role <= bot_top_role and not ctx.guild.owner == ctx.author:
            embed = discord.Embed(
                title="",
                description=f"## {animated_cross} **Insufficient Permissions**\n```yaml\nYour Role Must Be Above My Role```",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

            raise commands.CheckFailure("Loda")
        return True
    return commands.check(predicate)




def modd():
    async def predicate(ctx: commands.Context):
        target = None

        for arg in ctx.args[2:]:
            if isinstance(arg, discord.Member):
                target = arg
                break

        if target is None:
            for arg in ctx.kwargs.values():
                if isinstance(arg, discord.Member):
                    target = arg
                    break

        if not target:
            return True

        perms = [
            'manage_messages',
            'kick_members',
            'ban_members',
            'administrator',
            'mute_members'
        ]
        has_perms = any(getattr(target.guild_permissions, perm, False) for perm in perms)
        if has_perms:
            target_top_role = max(target.roles, key=lambda role: role.position)
            author_top_role = ctx.author.top_role
            if target_top_role.position > author_top_role.position:
                embed = discord.Embed(
                    description=f"## {animated_cross} Insufficient permissions```You can't perform this action on a mod/admin with a higher role```",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)
                raise commands.CheckFailure("Loda")

        return True
    return commands.check(predicate)




async def delmsgs(ctx, limit, predicate, *, before=None, after=None):
    if limit > 1000:
        msg = f"{cross} Max message delete count is 1000."
        if ctx.interaction:
            await ctx.interaction.followup.send(msg, ephemeral=True)
        else:
            await ctx.reply(embed=discord.Embed(description=msg, color=colour), delete_after=5, mention_author=False)
        return

    before_obj = ctx.message if before is None else discord.Object(id=before)
    after_obj  = discord.Object(id=after) if after is not None else None
    cutoff     = datetime.now(timezone.utc) - timedelta(days=14)

    def wrapped_predicate(msg):
        return predicate(msg) and msg.created_at > cutoff

    try:
        deleted = await ctx.channel.purge(
            limit=limit,
            before=before_obj,
            after=after_obj,
            check=wrapped_predicate,
        )
    except discord.Forbidden:
        msg = f"{cross} I don't have permission to delete messages here."
        if ctx.interaction:
            await ctx.interaction.followup.send(msg, ephemeral=True)
        else:
            await ctx.send(msg, delete_after=5)
        return
    except discord.HTTPException:
        return

    count = len(deleted)
    try:
        if ctx.interaction:
            await ctx.interaction.followup.send(
                f"{tick} Deleted {count} message{'s' if count != 1 else ''}.",
                ephemeral=True,
            )
        else:
            await ctx.send(
                f"{tick} Deleted {count} message{'s' if count != 1 else ''}.",
                delete_after=5,
            )
    except (discord.NotFound, discord.HTTPException):
        pass
    


developer_team_ids = [1217734448947134514, 1497159980900417546, 1414972795665911892] # worse4sure, ahm.fr, ritik

def is_developer():
    async def predicate(ctx: commands.Context):
        if ctx.author.id not in developer_team_ids:
            embed = discord.Embed(
                title="",
                description=f"## {animated_cross} **Access Denied**\n```yaml\nDeveloper Only Command```",
                color=colour
            )
            if ctx.author.avatar:
                embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar.url)
            else:
                embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.default_avatar.url)

            await ctx.reply(embed=embed, mention_author=False, delete_after = 5)
            raise commands.CheckFailure("Loda")
        return True
    return commands.check(predicate)



NSFW_KEYWORDS = [
    'porn', 'adult', 'xxx', 'sex', 'nude', 'mature', 'explicit', 'xnxx', 'stepsister', 'milf',
    'fuck', 'ass', 'dick', 'pussy', 'cunt', 'blowjob', 'handjob', 'orgy', 'shemale', 'gay', 
    'lesbian', 'pornhub', 'sex.com', 'onlyfans', 'adultfriendfinder', 'camgirl', 'bdsm', 'fetish',
    'erotic', 'swinger', 'dominatrix', 'spankbang', 'tits', 'boobs', 'butt', 'anal', 'vibrator',
    'kink', 'cougar', 'horny', 'pornographic', 'amateur', 'naked', 'hardcore', 'softcore', 'sexy',
    'sexxx', 'cocksucking', 'cum', 'sexting', 'nudes', 'erotica', 'threesome', 'milf', 'hentai',
    'yaoi', 'yuri', 'striptease', 'sexxy', 'bukkake', 'orgasm', 'adultsite', 'x-rated', 'dirty',
    'nsfw', 'xxx', 'fetish', 'escort', 'massageparlor', 'peep', 'sexvideo', 'sexpics', 'sexvideo',
    'sextape', 'redtube', 'adultfilm', 'pornsite', 'dildo', 'fisting', 'lesbo', 'panties', 'cock',
    'blowjob', 'tease', 'strip', 'buttplug', 'pornography', 'porns', 'hustler', 'nubile', 'amateurporn'
]

def contains_nsfw(text):
    return any(keyword in text.lower() for keyword in NSFW_KEYWORDS)