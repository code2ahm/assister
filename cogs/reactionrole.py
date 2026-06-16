import asyncio
import discord
from discord.ext import commands
from discord import app_commands, ui
from utils.checks import *
from utils.variables import *
from utils.loads import *


def _build_panel_layout(title: str, roles: dict, guild: discord.Guild, description: str = None) -> ui.LayoutView:
    layout = ui.LayoutView()
    c = ui.Container()

    parts = []
    if title and title.lower() != "none":
        parts.append(f"## {title}")
    if description:
        parts.append(description)
    if roles:
        role_lines = []
        for emoji_str, role_id in roles.items():
            role = guild.get_role(role_id)
            if role:
                role_lines.append(f"{emoji_str} {role.mention}")
        if role_lines:
            parts.append("\n".join(role_lines))

    if not parts:
        parts.append("No roles configured yet.")

    c.add_item(ui.TextDisplay("\n\n".join(parts)))
    c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
    c.add_item(ui.TextDisplay("-# React to get your role"))
    layout.add_item(c)
    return layout


def _plan_layout(channel=None, title=None, description=None, roles_count=0):
    layout = ui.LayoutView()
    c = ui.Container()
    ch = channel.mention if channel else "`not set`"
    t = title if title else "`not set`"
    d = description if description else "`none`"
    c.add_item(ui.TextDisplay(
        f"### Setup Plan\n\n"
        f"**Channel:** {ch}\n"
        f"**Title:** {t}\n"
        f"**Description:** {d}\n"
        f"**Roles:** {roles_count} configured"
    ))
    layout.add_item(c)
    return layout


def _resp(text: str) -> ui.LayoutView:
    layout = ui.LayoutView()
    c = ui.Container()
    c.add_item(ui.TextDisplay(text))
    layout.add_item(c)
    return layout


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        data = lrr()
        rr = data.get(str(payload.message_id))
        if not rr or rr["guild_id"] != payload.guild_id:
            return

        role_id = rr["roles"].get(str(payload.emoji))
        if not role_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        role = guild.get_role(role_id)
        if not role:
            return

        if role in member.roles:
            await member.remove_roles(role, reason="Reaction Role")
        else:
            await member.add_roles(role, reason="Reaction Role")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        data = lrr()
        rr = data.get(str(payload.message_id))
        if not rr or rr["guild_id"] != payload.guild_id:
            return

        role_id = rr["roles"].get(str(payload.emoji))
        if not role_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        role = guild.get_role(role_id)
        if not role:
            return

        if role in member.roles:
            await member.remove_roles(role, reason="Reaction Role")


    async def _resolve_panel_msg(self, rr: dict, message_id: str, guild: discord.Guild):
        channel = guild.get_channel(rr["channel_id"])
        if not channel:
            return None
        try:
            return await channel.fetch_message(int(message_id))
        except (discord.NotFound, discord.Forbidden):
            return None


    @commands.hybrid_group(name='reactionrole', aliases=['rr'],
                           invoke_without_command=True,
                           description="Self-assign roles by reacting to messages",
                           usage="reactionrole", category="Reaction Role")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reactionrole(self, ctx: commands.Context):
        cmd = self.bot.get_command('help')
        if cmd:
            await ctx.invoke(cmd, query='reactionrole')

    @reactionrole.command(name='add', aliases=['create'],
                          description="Creates a new reaction role panel in a channel",
                          usage="reactionrole add <channel> <title>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Channel to send the panel to", title="Panel title")
    async def rr_add(self, ctx: commands.Context, channel: discord.TextChannel, *, title: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        layout = _build_panel_layout(title, {}, ctx.guild)
        msg = await channel.send(view=layout)

        data = lrr()
        data[str(msg.id)] = {
            "guild_id": ctx.guild.id,
            "channel_id": channel.id,
            "title": title,
            "roles": {},
            "description": None,
        }
        saverr(data)

        result = _resp(
            f"### {tick} Panel Created\n\n"
            f"{channel.mention}\n"
            f"Message ID: `{msg.id}`\n\n"
            f"Run `{ctx.prefix}rr addrole {msg.id} <emoji> <role>` to add roles."
        )
        await ctx.reply(view=result, mention_author=False)

    @reactionrole.command(name='panel',
                          description="Registers an existing message as a reaction role panel",
                          usage="reactionrole panel <message_id> <title>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(message_id="ID of the existing message", title="Panel title for reference")
    async def rr_panel(self, ctx: commands.Context, message_id: str, *, title: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        msg = None
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(ctx.guild.me).read_message_history:
                try:
                    msg = await channel.fetch_message(int(message_id))
                    break
                except (discord.NotFound, discord.Forbidden):
                    continue

        if not msg:
            await ctx.reply(view=_resp(f"{cross} Could not find a message with ID `{message_id}` in any channel I can see."), mention_author=False)
            return

        data = lrr()
        if str(msg.id) in data:
            await ctx.reply(view=_resp(f"{cross} That message is already registered as a reaction role panel."), mention_author=False)
            return

        data[str(msg.id)] = {
            "guild_id": ctx.guild.id,
            "channel_id": msg.channel.id,
            "title": title,
            "roles": {},
            "custom_message": True,
        }
        saverr(data)

        result = _resp(
            f"### {tick} Panel Registered\n\n"
            f"{msg.channel.mention} [Jump to message]({msg.jump_url})\n"
            f"Title: **{title}**\n\n"
            f"Use `{ctx.prefix}rr addrole {msg.id} <emoji> <role>` to add roles.\n"
            f"{caution} The message content will not be modified."
        )
        await ctx.reply(view=result, mention_author=False)

    @reactionrole.command(name='addrole',
                          description="Adds an emoji-role pair to a reaction role panel. Users can click the emoji to get the role.",
                          usage="reactionrole addrole <message_id> <emoji> <role>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(message_id="Message ID of the panel", emoji="Emoji to react with", role="Role to assign")
    async def rr_addrole(self, ctx: commands.Context, message_id: str, emoji: str, role: discord.Role):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        data = lrr()
        rr = data.get(message_id)
        if not rr or rr["guild_id"] != ctx.guild.id:
            await ctx.reply(view=_resp(f"{cross} No reaction role panel found with ID `{message_id}`."), mention_author=False)
            return

        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.reply(view=_resp(f"{cross} That role is above your top role."), mention_author=False)
            return

        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.reply(view=_resp(f"{cross} I need the **Manage Roles** permission."), mention_author=False)
            return

        if role >= ctx.guild.me.top_role:
            await ctx.reply(view=_resp(f"{cross} That role is above my top role."), mention_author=False)
            return

        msg = await self._resolve_panel_msg(rr, message_id, ctx.guild)
        if not msg:
            await ctx.reply(view=_resp(f"{cross} Could not find the panel message."), mention_author=False)
            return

        try:
            await msg.add_reaction(emoji)
        except (discord.HTTPException, discord.InvalidArgument):
            await ctx.reply(view=_resp(f"{cross} Invalid emoji. Make sure the emoji is from this server or a standard unicode emoji."), mention_author=False)
            return

        rr["roles"][emoji] = role.id
        saverr(data)

        if not rr.get("custom_message"):
            await msg.edit(embed=None, view=_build_panel_layout(rr["title"], rr["roles"], ctx.guild, rr.get("description", None)))

        result = _resp(
            f"### {tick} Role Added\n\n"
            f"{emoji} {role.mention}\n\n"
            f"[Jump to panel]({msg.jump_url})"
        )
        await ctx.reply(view=result, mention_author=False)

    @reactionrole.command(name='removerole', aliases=['deleterole'],
                          description="Removes an emoji-role pair from a panel",
                          usage="reactionrole removerole <message_id> <emoji>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(message_id="Message ID of the panel", emoji="Emoji to remove")
    async def rr_removerole(self, ctx: commands.Context, message_id: str, emoji: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        data = lrr()
        rr = data.get(message_id)
        if not rr or rr["guild_id"] != ctx.guild.id:
            await ctx.reply(view=_resp(f"{cross} No reaction role panel found with ID `{message_id}`."), mention_author=False)
            return

        if emoji not in rr["roles"]:
            await ctx.reply(view=_resp(f"{cross} That emoji is not configured on this panel."), mention_author=False)
            return

        del rr["roles"][emoji]
        saverr(data)

        msg = await self._resolve_panel_msg(rr, message_id, ctx.guild)
        if msg:
            if not rr.get("custom_message"):
                await msg.edit(embed=None, view=_build_panel_layout(rr["title"], rr["roles"], ctx.guild, rr.get("description", None)))
            try:
                await msg.clear_reaction(emoji)
            except (discord.HTTPException, discord.NotFound):
                pass

        await ctx.reply(view=_resp(f"{tick} Removed `{emoji}` from the reaction role panel."), mention_author=False)

    @reactionrole.command(name='edit',
                          description="Changes the title of a reaction role panel. Updates the embed if the bot created it.",
                          usage="reactionrole edit <message_id> <new_title>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(message_id="Message ID of the panel", title="New panel title")
    async def rr_edit(self, ctx: commands.Context, message_id: str, *, title: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        data = lrr()
        rr = data.get(message_id)
        if not rr or rr["guild_id"] != ctx.guild.id:
            await ctx.reply(view=_resp(f"{cross} No reaction role panel found with ID `{message_id}`."), mention_author=False)
            return

        rr["title"] = title
        saverr(data)

        msg = await self._resolve_panel_msg(rr, message_id, ctx.guild)
        if msg and not rr.get("custom_message"):
            await msg.edit(embed=None, view=_build_panel_layout(title, rr["roles"], ctx.guild, rr.get("description", None)))

        await ctx.reply(view=_resp(f"{tick} Panel title updated to **{title}**."), mention_author=False)

    @reactionrole.command(name='delete',
                          description="Deletes a reaction role panel entirely and removes its message.",
                          usage="reactionrole delete <message_id>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(message_id="Message ID of the panel")
    async def rr_delete(self, ctx: commands.Context, message_id: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        data = lrr()
        rr = data.get(message_id)
        if not rr or rr["guild_id"] != ctx.guild.id:
            await ctx.reply(view=_resp(f"{cross} No reaction role panel found with ID `{message_id}`."), mention_author=False)
            return

        del data[message_id]
        saverr(data)

        msg = await self._resolve_panel_msg(rr, message_id, ctx.guild)
        if msg:
            try:
                await msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        await ctx.reply(view=_resp(f"{tick} Reaction role panel deleted."), mention_author=False)

    @reactionrole.command(name='list',
                          description="Shows all reaction role panels in the server with their roles and message IDs.",
                          usage="reactionrole list")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rr_list(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        data = lrr()
        guild_panels = {mid: rr for mid, rr in data.items()
                        if rr["guild_id"] == ctx.guild.id}

        if not guild_panels:
            await ctx.reply(view=_resp(f"{grey} No reaction role panels in this server."), mention_author=False)
            return

        pages = list(guild_panels.items())
        total = len(pages)

        class RRListLayout(ui.LayoutView):
            def __init__(self, pages, total, ctx):
                super().__init__(timeout=120)
                self.pages = pages
                self.total = total
                self.ctx   = ctx
                self.page  = 0
                self._render()

            def _render(self):
                self.clear_items()
                mid, rr = self.pages[self.page]
                channel = ctx.guild.get_channel(rr["channel_id"])
                ch = channel.mention if channel else "#deleted-channel"

                c = ui.Container()
                c.add_item(ui.TextDisplay(
                    f"### {rr['title']}\n\n"
                    f"{ch}\n"
                    f"Message ID: `{mid}`\n"
                    f"**{len(rr['roles'])}** role{'s' if len(rr['roles']) != 1 else ''}"
                ))

                if rr["roles"]:
                    c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
                    role_lines = []
                    for emoji_str, role_id in rr["roles"].items():
                        role = ctx.guild.get_role(role_id)
                        r = role.mention if role else f"`{role_id}`"
                        role_lines.append(f"{emoji_str} {r}")
                    c.add_item(ui.TextDisplay("\n".join(role_lines)))

                c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
                c.add_item(ui.TextDisplay(f"-# Page {self.page + 1}/{self.total}"))
                self.add_item(c)

                row = ui.ActionRow()
                prev = ui.Button(emoji="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0)
                nxt  = ui.Button(emoji="▶", style=discord.ButtonStyle.secondary, disabled=self.page >= self.total - 1)

                async def _prev(i: discord.Interaction):
                    self.page -= 1
                    self._render()
                    await i.response.edit_message(view=self)

                async def _next(i: discord.Interaction):
                    self.page += 1
                    self._render()
                    await i.response.edit_message(view=self)

                prev.callback = _prev
                nxt.callback  = _next
                row.add_item(prev)
                row.add_item(nxt)
                self.add_item(row)

        await ctx.reply(view=RRListLayout(pages, total, ctx), mention_author=False)

    @reactionrole.command(name='setup',
                          description="Interactive setup wizard. Guides you through creating a reaction role panel step by step.",
                          usage="reactionrole setup")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def rr_setup(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        async def wait_answer(timeout=120):
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=timeout)
                if msg.content.lower() == "cancel":
                    raise asyncio.CancelledError
                return msg
            except asyncio.TimeoutError:
                await ctx.send(f"{cross} Setup timed out. Run `{ctx.prefix}rr setup` to start again.")
                raise asyncio.CancelledError

        try:
            channel = None
            title = None
            description = None
            parsed_roles = {}

            plan_msg = await ctx.reply(view=_plan_layout(), mention_author=False)

            now = int(__import__("time").time())
            await ctx.send(f"Which channel should the panel go in?  ⏰ <t:{now + 120}:R>")
            channel_msg = await wait_answer(120)
            if channel_msg.channel_mentions:
                channel = channel_msg.channel_mentions[0]
            else:
                ch_name = channel_msg.content.strip().lower()
                channel = discord.utils.get(ctx.guild.text_channels, name=ch_name)
            if not channel:
                channel = ctx.channel
            await plan_msg.edit(view=_plan_layout(channel=channel))

            now = int(__import__("time").time())
            await ctx.send(f"What should the panel title be? (type `none` for no title)  ⏰ <t:{now + 120}:R>")
            title_msg = await wait_answer(120)
            title = title_msg.content
            await plan_msg.edit(view=_plan_layout(channel=channel, title=title))

            now = int(__import__("time").time())
            await ctx.send(f"Do you want a custom description for the panel? (yes/no)  ⏰ <t:{now + 120}:R>")
            desc_choice = await wait_answer(120)
            if desc_choice.content.lower() in ("yes", "y"):
                now = int(__import__("time").time())
                await ctx.send(f"Send the description text.  ⏰ <t:{now + 120}:R>")
                desc_msg = await wait_answer(120)
                description = desc_msg.content
                await plan_msg.edit(view=_plan_layout(channel=channel, title=title, description=description))

            await ctx.send(
                f"Send role-emoji pairs. One per line. Example:\n"
                f"```\n@Gamer 🎮\n@Artist 🎨\n```\n"
                f"Type **`done`** when finished, or **`skip`** to add none.  ⏰ <t:{now + 120}:R>"
            )
            roles_msg = await wait_answer(300)
            roles_raw = roles_msg.content
            if roles_raw.lower() not in ("done", "skip"):
                lines = roles_raw.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.rsplit(None, 1)
                    if len(parts) != 2:
                        await ctx.send(f"{cross} Invalid line: `{line}`. Expected: `@Role <emoji>`. Skipping.")
                        continue
                    role_str, emoji_str = parts
                    role = None
                    if roles_msg.role_mentions:
                        for r in roles_msg.role_mentions:
                            if r.mention == role_str or f"<@&{r.id}>" == role_str:
                                role = r
                                break
                    if not role:
                        role = discord.utils.get(ctx.guild.roles, name=role_str.strip("@& "))
                    if not role:
                        await ctx.send(f"{cross} Could not find role: `{role_str}`. Skipping.")
                        continue
                    if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                        await ctx.send(f"{cross} `{role.name}` is above your top role. Skipping.")
                        continue
                    if role >= ctx.guild.me.top_role:
                        await ctx.send(f"{cross} `{role.name}` is above my top role. Skipping.")
                        continue
                    parsed_roles[emoji_str] = role.id

            await plan_msg.edit(view=_plan_layout(channel=channel, title=title, description=description, roles_count=len(parsed_roles)))

            layout = _build_panel_layout(title, parsed_roles, ctx.guild, description)
            msg = await channel.send(view=layout)

            for emoji_str in parsed_roles:
                try:
                    await msg.add_reaction(emoji_str)
                except (discord.HTTPException, discord.InvalidArgument):
                    await ctx.send(f"{cross} Could not add reaction `{emoji_str}`. Invalid emoji.")

            data = lrr()
            data[str(msg.id)] = {
                "guild_id": ctx.guild.id,
                "channel_id": channel.id,
                "title": title,
                "roles": parsed_roles,
                "description": description,
            }
            saverr(data)

            count = len(parsed_roles)
            result = _resp(
                f"### {tick} Setup Complete\n\n"
                f"{channel.mention}\n"
                f"Message ID: `{msg.id}`\n"
                f"**{count}** role{'s' if count != 1 else ''} configured\n\n"
                f"[Jump to panel]({msg.jump_url})"
            )
            await ctx.reply(view=result, mention_author=False)

        except asyncio.CancelledError:
            await ctx.send(f"{cross} Setup cancelled.", delete_after=6)


async def setup(bot):
    await bot.add_cog(ReactionRole(bot))
