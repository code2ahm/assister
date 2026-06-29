import discord
from discord.ext import commands
from humanfriendly import parse_timespan, InvalidTimespan
from datetime import datetime, timedelta
from discord import utils as Utils, app_commands, ui
from utils.prefixes import *
from utils.variables import *
from utils.paginator import YoNo, Ahm
from utils.checks import *
from discord.ui import Button, View
from typing import Union
import io
import asyncio


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def layout_err(self, ctx, msg):
        layout = ui.LayoutView(timeout=0)
        c = ui.Container()
        c.add_item(ui.TextDisplay(msg))
        layout.add_item(c)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(f"-# Requested by {ctx.author.display_name}  •  {ctx.guild.name}"))
        return layout

    def layout_ok(self, ctx, msg):
        layout = ui.LayoutView(timeout=0)
        c = ui.Container()
        c.add_item(ui.TextDisplay(msg))
        layout.add_item(c)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(f"-# Moderator: {ctx.author.display_name}  •  {ctx.guild.name}"))
        return layout

    def _pre_mod_check(self, ctx, target: discord.Member, action: str):
        if target == ctx.author:
            return f"## {cross} Cannot {action.title()} Yourself\nYou cannot {action} yourself."
        if target == ctx.guild.owner:
            return f"## {cross} Cannot {action.title()} Owner\nYou cannot {action} the server owner."
        if target.top_role >= ctx.guild.me.top_role:
            return f"## {cross} Role Too Low\nMy highest role is below or equal to **{target.display_name}**'s role. Move my role higher."
        if ctx.author != ctx.guild.owner and target.top_role >= ctx.author.top_role:
            return f"## {cross} Role Too Low\n**{target.display_name}**'s role is higher or equal to yours."
        return None

    def _result_embed(self, title: str, description: str, ctx) -> discord.Embed:
        e = discord.Embed(description=f"{title}\n\n{description}", color=colour)
        e.set_footer(text=f"Moderator: {ctx.author.display_name}  •  {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        return e



    @commands.hybrid_command(
        name="mute",
        aliases=["stfu", "silence", "timeout"],
        description="Times out a member for a given duration.",
        usage="mute <member(s)> [duration] [reason]"
    )
    @modd()
    @commands.has_guild_permissions(moderate_members=True)
    @commands.bot_has_guild_permissions(moderate_members=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(
        targets="Mention one or more members to mute",
        duration="Duration e.g. 10m, 1h, 2d (default: 1d)",
        reason="Reason for the mute"
    )
    async def mute(self, ctx: commands.Context, targets: commands.Greedy[discord.Member], duration: str = "1d", *, reason: str = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        if not targets:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} No Members Specified\nMention at least one member to mute."), mention_author=False)

        try:
            seconds = parse_timespan(duration)
        except InvalidTimespan:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Invalid Duration\n`{duration}` is not a valid duration. Try something like `10m`, `1h`, or `2d`."), mention_author=False)

        successes, failed, dm_ok, dm_fail = [], [], [], []

        for target in targets:
            err = self._pre_mod_check(ctx, target, "mute")
            if err:
                failed.append((target, err.split("\n")[1]))
                continue
            if target.is_timed_out():
                failed.append((target, "Already muted"))
                continue
            try:
                await target.timeout(Utils.utcnow() + timedelta(seconds=seconds), reason=f"{ctx.author} | {reason or 'No reason'}")
                successes.append(target)
                dm_embed = discord.Embed(
                    description=f"<:punishment:1499307386823901287> You were timed out in **{ctx.guild.name}**\n{e_dot} Duration: `{duration}`\n{e_dot} Reason: {reason or 'No reason provided'}",
                    color=colour
                )
                dm_embed.set_author(name=f"Moderator: {ctx.author}", icon_url=ctx.author.display_avatar.url)
                try:
                    await target.send(embed=dm_embed)
                    dm_ok.append(target)
                except Exception:
                    dm_fail.append(target)
            except discord.Forbidden:
                failed.append((target, "Missing permissions"))
            except Exception as e:
                failed.append((target, str(e)[:60]))

        lines = [f"## <:punishment:1499307386823901287> Mute Results"]
        if successes:
            lines.append(f"\n**Muted ({len(successes)}):**")
            lines += [f"{tick} {m}" for m in successes]
            lines.append(f"\n{e_dot} Duration: `{duration}`\n{e_dot} Reason: {reason or 'No reason provided'}\n{e_dot} Moderator: {ctx.author}")
            dm_line = ""
            if dm_ok:
                dm_line += f"{tick} Sent"
            if dm_fail:
                dm_line += f"  {cross} Failed"
            if dm_line:
                lines.append(f"\n{e_dot} DM: {dm_line}")
        if failed:
            lines.append(f"\n**Failed ({len(failed)}):**")
            lines += [f"{cross} {m} — {r}" for m, r in failed]

        await ctx.reply(view=self.layout_ok(ctx, "\n".join(lines)), mention_author=False)



    @commands.hybrid_command(
        name="unmute",
        description="Removes timeout / unmutes a member.",
        usage="unmute <member> [reason]"
    )
    @modd()
    @commands.has_guild_permissions(moderate_members=True)
    @commands.bot_has_guild_permissions(moderate_members=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(target="Member to unmute", reason="Reason for unmuting")
    async def unmute(self, ctx: commands.Context, target: discord.Member, *, reason: str = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        if not target.is_timed_out():
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Not Muted\n{target} is not currently timed out."), mention_author=False)

        err = self._pre_mod_check(ctx, target, "unmute")
        if err:
            return await ctx.reply(view=self.layout_err(ctx, err), mention_author=False)

        try:
            await target.timeout(None, reason=f"{ctx.author} | {reason or 'No reason'}")
        except discord.Forbidden:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Missing Permissions\nI don't have permission to unmute {target}."), mention_author=False)

        dm_status = ""
        try:
            dm_embed = discord.Embed(
                description=f"{tick} You were unmuted in **{ctx.guild.name}**\n{e_dot} Reason: {reason or 'No reason provided'}",
                color=colour
            )
            dm_embed.set_author(name=f"Moderator: {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await target.send(embed=dm_embed)
            dm_status = f"{tick} Sent"
        except Exception:
            dm_status = f"{cross} Failed"

        await ctx.reply(view=self.layout_ok(ctx,
            f"## {tick} Unmuted\n"
            f"{e_dot} {target} has been unmuted.\n"
            f"{e_dot} Reason: {reason or 'No reason provided'}\n"
            f"{e_dot} Moderator: {ctx.author}\n"
            f"{e_dot} DM: {dm_status}"
        ), mention_author=False)



    @commands.hybrid_command(
        name="kick",
        aliases=["fuckoff", "kickout"],
        description="Kicks one or more members from the server.",
        usage="kick <member(s)> [reason]"
    )
    @modd()
    @commands.has_guild_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(targets="Mention one or more members to kick", reason="Reason for kick")
    async def kick(self, ctx: commands.Context, targets: commands.Greedy[discord.Member], *, reason: str = None):
        if ctx.interaction:
            await ctx.defer()

        if not targets:
            return await ctx.reply(embed=discord.Embed(description=f"{cross} **No Members Specified**\nMention at least one member to kick.", color=colour), mention_author=False)

        valid, blocked = [], []
        for t in targets:
            err = self._pre_mod_check(ctx, t, "kick")
            if err:
                blocked.append((t, err.split("\n")[1]))
            else:
                valid.append(t)

        if not valid:
            desc = "\n".join(f"{cross} {m} — {r}" for m, r in blocked)
            return await ctx.reply(embed=discord.Embed(description=f"{cross} **Cannot Kick**\n{desc}", color=colour), mention_author=False)

        confirm_view = YoNo(timeout=60)
        confirm_view.ctx = ctx
        names = ", ".join(str(t) for t in valid)
        confirm_embed = discord.Embed(
            description=f"❓ **Confirm Kick**\n<:kick:1499307114185625691> You are about to kick **{len(valid)}** member(s): {names}\n{e_dot} Reason: {reason or 'No reason provided'}\n\n{caution} This action cannot be undone.",
            color=colour
        )
        confirm_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        msg = await ctx.reply(embed=confirm_embed, view=confirm_view, mention_author=False)
        confirmed = await confirm_view.waitt()

        if not confirmed:
            return await msg.edit(embed=discord.Embed(description=f"{grey} Kick Cancelled", color=colour), view=None)

        successes, failed, dm_ok, dm_fail = [], [], [], []
        for target in valid:
            try:
                dm_embed = discord.Embed(
                    description=f"<:kick:1499307114185625691> You were kicked from **{ctx.guild.name}**\n{e_dot} Reason: {reason or 'No reason provided'}",
                    color=colour
                )
                dm_embed.set_author(name=f"Moderator: {ctx.author}", icon_url=ctx.author.display_avatar.url)
                try:
                    await target.send(embed=dm_embed)
                    dm_ok.append(target)
                except Exception:
                    dm_fail.append(target)
                await target.kick(reason=f"{ctx.author} | {reason or 'No reason'}")
                successes.append(target)
            except discord.Forbidden:
                failed.append((target, "Missing permissions"))
            except Exception as e:
                failed.append((target, str(e)[:60]))

        lines = []
        if successes:
            lines.append(f"**Kicked ({len(successes)}):**\n" + "\n".join(f"{tick} {m}" for m in successes))
            lines.append(f"{e_dot} Reason: {reason or 'No reason provided'}\n{e_dot} Moderator: {ctx.author}")
            dm_line = (f"{tick} Sent" if dm_ok else "") + (f"  {cross} Failed" if dm_fail else "")
            if dm_line:
                lines.append(f"{e_dot} DM: {dm_line}")
        if blocked:
            lines.append(f"**Blocked ({len(blocked)}):**\n" + "\n".join(f"{cross} {m} — {r}" for m, r in blocked))
        if failed:
            lines.append(f"**Failed ({len(failed)}):**\n" + "\n".join(f"{cross} {m} — {r}" for m, r in failed))

        result_embed = discord.Embed(
            description=f"## <:kick:1499307114185625691> Kick Results\n\n" + "\n\n".join(lines),
            color=colour
        )
        result_embed.set_footer(text=f"Moderator: {ctx.author.display_name}  •  {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await msg.edit(embed=result_embed, view=None)



    @commands.hybrid_command(
        name="ban",
        aliases=["expel", "fuckban"],
        description="Bans one or more members from the server.",
        usage="ban <member(s)> [reason]"
    )
    @modd()
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(targets="Mention one or more members to ban", reason="Reason for ban")
    async def ban(self, ctx: commands.Context, targets: commands.Greedy[discord.Member], *, reason: str = None):
        if ctx.interaction:
            await ctx.defer()

        if not targets:
            return await ctx.reply(embed=discord.Embed(description=f"{cross} **No Members Specified**\nMention at least one member to ban.", color=colour), mention_author=False)

        valid, blocked = [], []
        for t in targets:
            err = self._pre_mod_check(ctx, t, "ban")
            if err:
                blocked.append((t, err.split("\n")[1]))
            else:
                valid.append(t)

        if not valid:
            desc = "\n".join(f"{cross} {m} — {r}" for m, r in blocked)
            return await ctx.reply(embed=discord.Embed(description=f"{cross} **Cannot Ban**\n{desc}", color=colour), mention_author=False)

        confirm_view = YoNo(timeout=60)
        confirm_view.ctx = ctx
        names = ", ".join(str(t) for t in valid)
        confirm_embed = discord.Embed(
            description=f"❓ **Confirm Ban**\n<:bionic_g_ban:1261572949572321353> You are about to ban **{len(valid)}** member(s): {names}\n{e_dot} Reason: {reason or 'No reason provided'}\n\n{caution} This action cannot be undone.",
            color=colour
        )
        confirm_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        msg = await ctx.reply(embed=confirm_embed, view=confirm_view, mention_author=False)
        confirmed = await confirm_view.waitt()

        if not confirmed:
            return await msg.edit(embed=discord.Embed(description=f"{grey} Ban Cancelled", color=colour), view=None)

        successes, failed, dm_ok, dm_fail = [], [], [], []
        for target in valid:
            try:
                dm_embed = discord.Embed(
                    description=f"<:bionic_g_ban:1261572949572321353> You were banned from **{ctx.guild.name}**\n{e_dot} Reason: {reason or 'No reason provided'}",
                    color=colour
                )
                dm_embed.set_author(name=f"Moderator: {ctx.author}", icon_url=ctx.author.display_avatar.url)
                try:
                    await target.send(embed=dm_embed)
                    dm_ok.append(target)
                except Exception:
                    dm_fail.append(target)
                await target.ban(reason=f"{ctx.author} | {reason or 'No reason'}", delete_message_days=0)
                successes.append(target)
            except discord.Forbidden:
                failed.append((target, "Missing permissions"))
            except Exception as e:
                failed.append((target, str(e)[:60]))

        lines = []
        if successes:
            lines.append(f"**Banned ({len(successes)}):**\n" + "\n".join(f"{tick} {m}" for m in successes))
            lines.append(f"{e_dot} Reason: {reason or 'No reason provided'}\n{e_dot} Moderator: {ctx.author}")
            dm_line = (f"{tick} Sent" if dm_ok else "") + (f"  {cross} Failed" if dm_fail else "")
            if dm_line:
                lines.append(f"{e_dot} DM: {dm_line}")
        if blocked:
            lines.append(f"**Blocked ({len(blocked)}):**\n" + "\n".join(f"{cross} {m} — {r}" for m, r in blocked))
        if failed:
            lines.append(f"**Failed ({len(failed)}):**\n" + "\n".join(f"{cross} {m} — {r}" for m, r in failed))

        result_embed = discord.Embed(
            description=f"## <:bionic_g_ban:1261572949572321353> Ban Results\n\n" + "\n\n".join(lines),
            color=colour
        )
        result_embed.set_footer(text=f"Moderator: {ctx.author.display_name}  •  {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await msg.edit(embed=result_embed, view=None)



    @commands.hybrid_command(
        name="unban",
        description="Unbans a user from the server.",
        usage="unban <user id>"
    )
    @modd()
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(user="The user ID to unban")
    async def unban(self, ctx: commands.Context, user: int):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        try:
            user = await self.bot.fetch_user(user)
        except discord.NotFound:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} User Not Found\nNo user found with ID `{user}`."), mention_author=False)

        try:
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
        except discord.NotFound:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Not Banned\n**{user}** is not banned from this server."), mention_author=False)
        except discord.Forbidden:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Missing Permissions\nI don't have permission to unban members."), mention_author=False)

        await ctx.reply(view=self.layout_ok(ctx,
            f"## {tick} Unbanned\n"
            f"{e_dot} **{user}** (`{user.id}`) has been unbanned.\n"
            f"{e_dot} Moderator: {ctx.author}"
        ), mention_author=False)



    @commands.hybrid_command(
        name="nick",
        aliases=["nickname", "addnick"],
        description="Changes the nickname of a member.",
        usage="nick <member> <nickname>"
    )
    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(target="Member whose nickname to change", nickname="The new nickname")
    async def nick(self, ctx: commands.Context, target: discord.Member, *, nickname: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        if ctx.author != ctx.guild.owner and ctx.author.top_role <= target.top_role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too Low\nYou can't change the nickname of someone with a higher or equal role."), mention_author=False)
        if ctx.guild.me.top_role <= target.top_role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too Low\nMy role is not high enough to change **{target.display_name}**'s nickname."), mention_author=False)
        if len(nickname) > 32:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Nickname Too Long\nNicknames cannot exceed 32 characters (`{len(nickname)}/32`)."), mention_author=False)

        old_nick = target.display_name
        try:
            await target.edit(nick=nickname, reason=f"Changed by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Missing Permissions\nI couldn't change **{target.display_name}**'s nickname."), mention_author=False)

        await ctx.reply(view=self.layout_ok(ctx,
            f"## {tick} Nickname Changed\n"
            f"{e_dot} {target}\n"
            f"{e_dot} Before: `{old_nick}`\n"
            f"{e_dot} After: `{nickname}`\n"
            f"{e_dot} Moderator: {ctx.author}"
        ), mention_author=False)


    @commands.hybrid_command(
        name="removenick",
        aliases=["rnick", "removenickname"],
        description="Removes the nickname of a member.",
        usage="removenick <member>"
    )
    @commands.has_guild_permissions(manage_nicknames=True)
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(target="Member whose nickname to remove")
    async def removenick(self, ctx: commands.Context, target: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        if not target.nick:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} No Nickname\n{target} doesn't have a custom nickname."), mention_author=False)
        if ctx.author != ctx.guild.owner and ctx.author.top_role <= target.top_role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too Low\nYou can't remove the nickname of someone with a higher or equal role."), mention_author=False)
        if ctx.guild.me.top_role <= target.top_role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too Low\nMy role is not high enough to edit **{target.display_name}**."), mention_author=False)

        old_nick = target.nick
        try:
            await target.edit(nick=None, reason=f"Removed by {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Missing Permissions\nI couldn't remove **{target.display_name}**'s nickname."), mention_author=False)

        await ctx.reply(view=self.layout_ok(ctx,
            f"## {tick} Nickname Removed\n"
            f"{e_dot} {target}'s nickname `{old_nick}` has been removed.\n"
            f"{e_dot} Moderator: {ctx.author}"
        ), mention_author=False)




    @commands.hybrid_group(
        name="purge",
        aliases=["clear"],
        description="Purge messages from the channel.",
        usage="purge <count> [member]"
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def purge(self, ctx: commands.Context, choice: Union[discord.Member, int], count: int = None):
        if ctx.invoked_subcommand is None:
            if isinstance(choice, discord.Member):
                if count is None:
                    return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Missing Count\nProvide a message count: `purge @member 50`"), mention_author=False, delete_after=5)
                if not ctx.interaction:
                    await ctx.message.delete()
                await delmsgs(ctx, limit=count, predicate=lambda msg: msg.author == choice)
            elif isinstance(choice, int):
                if not ctx.interaction:
                    await ctx.message.delete()
                await delmsgs(ctx, limit=choice, predicate=lambda msg: True)

    @purge.command(name="all", description="Purge the last 100 messages.", usage="purge all")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def purge_all(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.message.delete()
        await delmsgs(ctx, limit=100, predicate=lambda msg: True)

    @purge.command(name="bots", description="Purge bot messages.", usage="purge bots")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def purge_bots(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.message.delete()
        await delmsgs(ctx, limit=100, predicate=lambda msg: msg.author.bot)

    @purge.command(name="embeds", description="Purge messages containing embeds.", usage="purge embeds")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def purge_embeds(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.message.delete()
        await delmsgs(ctx, limit=100, predicate=lambda msg: bool(msg.embeds))

    @purge.command(name="attachments", description="Purge messages containing attachments.", usage="purge attachments")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def purge_attachments(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.message.delete()
        await delmsgs(ctx, limit=100, predicate=lambda msg: bool(msg.attachments))

    @purge.command(name="links", description="Purge messages containing links.", usage="purge links")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def purge_links(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.message.delete()
        await delmsgs(ctx, limit=100, predicate=lambda msg: "http" in msg.content or "www" in msg.content)

    @purge.command(name="files", description="Purge messages containing files.", usage="purge files")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def purge_files(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.message.delete()
        await delmsgs(ctx, limit=100, predicate=lambda msg: bool(msg.attachments))

    @purge.command(name="member", aliases=["user"], description="Purge messages from a specific member.", usage="purge member <member> [count]")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    @app_commands.describe(target="Member whose messages to delete", count="How many messages to scan (default 50)")
    async def purge_member(self, ctx: commands.Context, target: discord.Member, count: int = 50):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.message.delete()
        await delmsgs(ctx, limit=count, predicate=lambda msg: msg.author == target)



    @commands.hybrid_command(
        name="addrole",
        aliases=["role", "giverole"],
        description="Adds a role to a member.",
        usage="addrole <member> <role> [reason]"
    )
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(target="Member to give the role to", role="Role to add", reason="Reason")
    async def addrole(self, ctx: commands.Context, target: discord.Member, role: discord.Role, *, reason: str = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        if role in target.roles:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Already Has Role\n{target} already has {role.name}."), mention_author=False)
        if ctx.author != ctx.guild.owner and ctx.author.top_role <= role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too High\nYou can't assign a role higher than or equal to your own."), mention_author=False)
        if ctx.guild.me.top_role <= role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too High\nMy role is not high enough to assign {role.name}. Move my role above it."), mention_author=False)

        try:
            await target.add_roles(role, reason=f"{ctx.author} | {reason or 'No reason'}")
        except discord.Forbidden:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Missing Permissions\nCouldn't add {role.name} to {target}."), mention_author=False)

        await ctx.reply(view=self.layout_ok(ctx,
            f"## {tick} Role Added\n"
            f"{e_dot} {role.name} → {target}\n"
            f"{e_dot} Reason: {reason or 'No reason provided'}\n"
            f"{e_dot} Moderator: {ctx.author}"
        ), mention_author=False)



    @commands.hybrid_command(
        name="removerole",
        aliases=["rrole", "takerole"],
        description="Removes a role from a member.",
        usage="removerole <member> <role> [reason]"
    )
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(target="Member to remove the role from", role="Role to remove", reason="Reason")
    async def removerole(self, ctx: commands.Context, target: discord.Member, role: discord.Role, *, reason: str = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        if role not in target.roles:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Doesn't Have Role\n{target} doesn't have {role.name}."), mention_author=False)
        if ctx.author != ctx.guild.owner and ctx.author.top_role <= role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too High\nYou can't remove a role higher than or equal to your own."), mention_author=False)
        if ctx.guild.me.top_role <= role:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Role Too High\nMy role is not high enough to remove {role.name}. Move my role above it."), mention_author=False)

        try:
            await target.remove_roles(role, reason=f"{ctx.author} | {reason or 'No reason'}")
        except discord.Forbidden:
            return await ctx.reply(view=self.layout_err(ctx, f"## {cross} Missing Permissions\nCouldn't remove {role.name} from {target}."), mention_author=False)

        await ctx.reply(view=self.layout_ok(ctx,
            f"## {tick} Role Removed\n"
            f"{e_dot} {role.name} removed from {target}\n"
            f"{e_dot} Reason: {reason or 'No reason provided'}\n"
            f"{e_dot} Moderator: {ctx.author}"
        ), mention_author=False)



    @commands.hybrid_command(
        name="nuke",
        description="Clones and resets the current channel.",
        usage="nuke [channel]"
    )
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @bled()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @app_commands.describe(channel="Channel to nuke (defaults to current)")
    async def clonechannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel

        confirm_embed = discord.Embed(
            description=f"❓ **Confirm Nuke**\n<:reacttrash:1496888674539933827> You are about to nuke {channel}.\n{caution} All messages will be permanently deleted.",
            color=colour
        )
        confirm_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        yes_btn = Button(label="Nuke it", style=discord.ButtonStyle.danger)
        no_btn  = Button(label="Cancel",  style=discord.ButtonStyle.secondary)
        view    = View(timeout=60)
        view.add_item(yes_btn)
        view.add_item(no_btn)

        msg = await ctx.reply(embed=confirm_embed, view=view, mention_author=False)

        async def do_nuke(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("❌ Not your command.", ephemeral=True)
            await interaction.response.defer()
            yes_btn.disabled = True
            no_btn.disabled  = True
            await msg.edit(view=view)
            try:
                pos    = channel.position
                new_ch = await channel.clone(reason=f"Nuked by {ctx.author}")
                await channel.delete(reason=f"Nuked by {ctx.author}")
                await new_ch.edit(position=pos)
                await new_ch.send(f"`Nukked by {ctx.author}`")

            except discord.Forbidden:
                err_embed = discord.Embed(description=f"{cross} **Missing Permissions**\nI don't have permission to delete or clone that channel.", color=colour)
                await ctx.send(embed=err_embed)

        async def do_cancel(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("❌ Not your command.", ephemeral=True)
            await interaction.response.defer()
            cancel_embed = discord.Embed(description=f"{grey} Nuke Cancelled", color=colour)
            await msg.edit(embed=cancel_embed, view=None)

        yes_btn.callback = do_nuke
        no_btn.callback  = do_cancel



    async def _set_channel_perm(self, channel, role, view_value, reason):
        try:
            await channel.set_permissions(role, view_channel=view_value, reason=reason)
            return True, None
        except discord.Forbidden:
            return False, "Missing permissions"
        except discord.HTTPException as e:
            if e.status == 429:
                return False, "Rate limited"
            return False, f"HTTP {e.status}"
        except asyncio.TimeoutError:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)[:80]

    def _make_pages(self, title, ok_items, fail_items, label_ok, label_fail, ctx):
        pages = []
        per_page = 20

        if ok_items:
            chunks = [ok_items[i:i+per_page] for i in range(0, len(ok_items), per_page)]
            for idx, chunk in enumerate(chunks):
                lines = [f"## {title}"]
                lines.append(f"\n**{label_ok} ({len(ok_items)}):**")
                lines.append("\n".join(f"{tick} {i.mention}" for i in chunk))
                if len(chunks) > 1:
                    lines.append(f"\nPage {idx+1} of {len(chunks)}")
                embed = discord.Embed(description="\n".join(lines), color=colour)
                embed.set_footer(text=f"Moderator: {ctx.author.display_name}  •  {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
                pages.append(embed)

        if fail_items:
            chunks = [fail_items[i:i+per_page] for i in range(0, len(fail_items), per_page)]
            for idx, chunk in enumerate(chunks):
                lines = [f"## {title}"]
                lines.append(f"\n**{label_fail} ({len(fail_items)}):**")
                for item in chunk:
                    if isinstance(item, tuple):
                        lines.append(f"{cross} {item[0].mention} — {item[1]}")
                    else:
                        lines.append(f"{cross} {item.mention}")
                if len(chunks) > 1:
                    lines.append(f"\nPage {idx+1} of {len(chunks)}")
                embed = discord.Embed(description="\n".join(lines), color=colour)
                embed.set_footer(text=f"Moderator: {ctx.author.display_name}  •  {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
                pages.append(embed)

        if not pages:
            return [discord.Embed(description=f"## {title}\n\nNothing affected.", color=colour)]
        return pages

    async def _process_all_channels(self, ctx, view_value, action_emoji, action_verb, done_title):
        if ctx.interaction:
            await ctx.defer()

        msg = await ctx.reply(embed=discord.Embed(description=f"{action_emoji} {action_verb} all channels...", color=colour), mention_author=False)

        ok, fail = [], []
        channels = [c for c in ctx.guild.channels if hasattr(c, 'set_permissions')]
        total = len(channels)

        for i, ch in enumerate(channels):
            success, err = await self._set_channel_perm(ch, ctx.guild.default_role, view_value, f"{action_verb.title()} by {ctx.author}")
            if success:
                ok.append(ch)
            else:
                fail.append((ch, err))

            if (i + 1) % 15 == 0 or i == total - 1:
                try:
                    await msg.edit(embed=discord.Embed(description=f"{action_emoji} {action_verb} all channels... ({i+1}/{total})", color=colour))
                except:
                    pass

            await asyncio.sleep(0.5)

        pages = self._make_pages(done_title, ok, fail, "Hidden" if view_value is False else "Unhidden", "Failed", ctx)
        if len(pages) > 1:
            paginator = Ahm(pages=pages, timeout=120)
            paginator.message = msg
            paginator.ctx = ctx
            await paginator.update_message()
        else:
            await msg.edit(embed=pages[0], view=None)


    @commands.hybrid_group(
        name="hide",
        description="Hides a channel from everyone role.",
        usage="hide [channel]"
    )
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Channel to hide (defaults to current)")
    async def hide(self, ctx: commands.Context, channel: discord.TextChannel = None):
        if ctx.invoked_subcommand is not None:
            return

        channel = channel or ctx.channel

        confirm_view = YoNo(timeout=60)
        confirm_view.ctx = ctx
        confirm_embed = discord.Embed(
            description=f"❓ **Confirm Hide**\nYou are about to hide {channel.mention}.\n{caution} All role overwrites will be denied view access.",
            color=colour
        )
        confirm_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        msg = await ctx.reply(embed=confirm_embed, view=confirm_view, mention_author=False)
        confirmed = await confirm_view.waitt()

        if not confirmed:
            return await msg.edit(embed=discord.Embed(description=f"{grey} Hide Cancelled", color=colour), view=None)

        await msg.edit(embed=discord.Embed(description=f"<a:1289683858337562625:1517941057931706519> hiding channel from everyone", color=colour), view=None)

        hidden_roles = []
        failed_roles = []

        ok, err = await self._set_channel_perm(channel, ctx.guild.default_role, False, f"Hidden by {ctx.author}")
        if ok:
            hidden_roles.append(ctx.guild.default_role)
        else:
            failed_roles.append((ctx.guild.default_role, err))

        for target in channel.overwrites:
            if isinstance(target, discord.Role) and target != ctx.guild.default_role:
                ok, err = await self._set_channel_perm(channel, target, False, f"Hidden by {ctx.author}")
                if ok:
                    hidden_roles.append(target)
                else:
                    failed_roles.append((target, err))

        pages = self._make_pages("🔒 Channel Hidden", hidden_roles, failed_roles, "Hidden from", "Failed", ctx)
        if len(pages) > 1:
            paginator = Ahm(pages=pages, timeout=120)
            paginator.message = msg
            paginator.ctx = ctx
            await paginator.update_message()
        else:
            await msg.edit(embed=pages[0], view=None)


    @hide.command(
        name="all",
        description="Hides all channels from everyone role.",
        usage="hide all"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @bled()
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def hide_all(self, ctx: commands.Context):
        await self._process_all_channels(ctx, False, "<a:1289683858337562625:1517941057931706519>", "hiding", "🔒 All Channels Hidden")


    @commands.hybrid_group(
        name="unhide",
        description="Unhides a channel from everyone role.",
        usage="unhide [channel]"
    )
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Channel to unhide (defaults to current)")
    async def unhide(self, ctx: commands.Context, channel: discord.TextChannel = None):
        if ctx.invoked_subcommand is not None:
            return

        channel = channel or ctx.channel

        confirm_view = YoNo(timeout=60)
        confirm_view.ctx = ctx
        confirm_embed = discord.Embed(
            description=f"❓ **Confirm Unhide**\nYou are about to unhide {channel.mention}.\n{caution} All role overwrites will have view access restored.",
            color=colour
        )
        confirm_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        msg = await ctx.reply(embed=confirm_embed, view=confirm_view, mention_author=False)
        confirmed = await confirm_view.waitt()

        if not confirmed:
            return await msg.edit(embed=discord.Embed(description=f"{grey} Unhide Cancelled", color=colour), view=None)

        await msg.edit(embed=discord.Embed(description=f"<a:1289683858337562625:1517941057931706519> unhiding channel from everyone", color=colour), view=None)

        unhidden_roles = []
        failed_roles = []

        ok, err = await self._set_channel_perm(channel, ctx.guild.default_role, None, f"Unhidden by {ctx.author}")
        if ok:
            unhidden_roles.append(ctx.guild.default_role)
        else:
            failed_roles.append((ctx.guild.default_role, err))

        for target in channel.overwrites:
            if isinstance(target, discord.Role) and target != ctx.guild.default_role:
                ok, err = await self._set_channel_perm(channel, target, None, f"Unhidden by {ctx.author}")
                if ok:
                    unhidden_roles.append(target)
                else:
                    failed_roles.append((target, err))

        pages = self._make_pages("🔓 Channel Unhidden", unhidden_roles, failed_roles, "Unhidden for", "Failed", ctx)
        if len(pages) > 1:
            paginator = Ahm(pages=pages, timeout=120)
            paginator.message = msg
            paginator.ctx = ctx
            await paginator.update_message()
        else:
            await msg.edit(embed=pages[0], view=None)


    @unhide.command(
        name="all",
        description="Unhides all channels from everyone role.",
        usage="unhide all"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @bled()
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def unhide_all(self, ctx: commands.Context):
        await self._process_all_channels(ctx, None, "<a:1289683858337562625:1517941057931706519>", "unhiding", "🔓 All Channels Unhidden")


async def setup(bot):
    await bot.add_cog(Moderation(bot))