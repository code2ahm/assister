import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import io
from utils.variables import *

CLONE_OPTIONS = {
    "roles":         "Roles",
    "categories":    "Categories",
    "text_channels": "Text Channels",
    "voice_channels":"Voice Channels",
    "stage_channels":"Stage Channels",
    "forum_channels":"Forum Channels",
    "emojis":        "Emojis",
    "stickers":      "Stickers",
    "server_icon":   "Server Icon",
    "server_banner": "Server Banner",
    "server_name":   "Server Name",
    "bans":          "Bans",
    "webhooks":      "Webhooks",
    "permissions":   "Channel Permissions",
}

class CloneSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=key, default=True)
            for key, label in CLONE_OPTIONS.items()
        ]
        super().__init__(
            placeholder="Select what to clone",
            min_values=1,
            max_values=len(options),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected = self.values
        await interaction.response.defer()


class CloneView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.selected: list[str] = list(CLONE_OPTIONS.keys())
        self.confirmed = False
        self.add_item(CloneSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Clone", style=discord.ButtonStyle.green, emoji=f"{tick}", row=1)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"{clock_emoji} Cloning in progress, this may take a while.",
            view=self
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji=f"{cross}", row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"{cross} Clone cancelled.", view=None)
        self.stop()


class ServerClone(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    async def _get_guild(self, guild_id: int) -> discord.Guild | None:
        return self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)

    async def _member_in_guild(self, guild: discord.Guild, user_id: int) -> discord.Member | None:
        try:
            return guild.get_member(user_id) or await guild.fetch_member(user_id)
        except discord.NotFound:
            return None


    async def wipe_roles(self, dst: discord.Guild):
        bot_top_role = dst.me.top_role
        for role in dst.roles:
            if role.is_default() or role.managed or role >= bot_top_role:
                continue
            try:
                await role.delete()
                await asyncio.sleep(0.3)
            except discord.Forbidden:
                pass

    async def wipe_channels(self, dst: discord.Guild, keep_channel: discord.TextChannel | None = None):
        for channel in dst.channels:
            if keep_channel and channel.id == keep_channel.id:
                continue
            try:
                await channel.delete()
                await asyncio.sleep(0.3)
            except discord.Forbidden:
                pass

    async def wipe_emojis(self, dst: discord.Guild):
        for emoji in dst.emojis:
            try:
                await emoji.delete()
                await asyncio.sleep(0.3)
            except discord.Forbidden:
                pass

    async def wipe_stickers(self, dst: discord.Guild):
        for sticker in dst.stickers:
            try:
                await sticker.delete()
                await asyncio.sleep(0.3)
            except discord.Forbidden:
                pass

    async def wipe_webhooks(self, dst: discord.Guild):
        for wh in await dst.webhooks():
            try:
                await wh.delete()
                await asyncio.sleep(0.2)
            except discord.Forbidden:
                pass


    async def clone_roles(self, src: discord.Guild, dst: discord.Guild) -> dict[int, discord.Role]:
        mapping: dict[int, discord.Role] = {
            src.default_role.id: dst.default_role
        }

        sorted_roles = sorted(
            [r for r in src.roles if not r.is_default() and not r.managed],
            key=lambda r: r.position  # ascending: lowest first
        )

        created: list[tuple[discord.Role, int]] = []

        for role in sorted_roles:
            try:
                new_role = await dst.create_role(
                    name=role.name,
                    permissions=role.permissions,
                    colour=role.colour,
                    hoist=role.hoist,
                    mentionable=role.mentionable,
                )
                created.append((new_role, role.position))
                mapping[role.id] = new_role
                await asyncio.sleep(0.3)
            except discord.Forbidden:
                pass

        # edit_role_positions expects a list of tuples, not a dict
        if created:
            bot_top = dst.me.top_role.position
            created.sort(key=lambda x: x[1])
            positions = {
                new_role: min(i + 1, bot_top - 1)
                for i, (new_role, _) in enumerate(created)
            }
            try:
                await dst.edit_role_positions(positions)
            except (discord.Forbidden, discord.HTTPException):
                pass

        return mapping
    
    
    async def clone_channels(
        self,
        src: discord.Guild,
        dst: discord.Guild,
        role_map: dict[int, discord.Role],
        selected: list[str],
    ):
        def build_overwrites(channel) -> dict:
            if "permissions" not in selected:
                return {}
            ows = {}
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Role):
                    mapped = role_map.get(target.id)
                    if mapped:
                        ows[mapped] = overwrite
                elif isinstance(target, discord.Member):
                    ows[target] = overwrite
            return ows

        cat_map: dict[int, discord.CategoryChannel] = {}

        if "categories" in selected:
            for cat in sorted(src.categories, key=lambda c: c.position):
                try:
                    new_cat = await dst.create_category(
                        name=cat.name,
                        overwrites=build_overwrites(cat),
                        position=cat.position,
                    )
                    cat_map[cat.id] = new_cat
                    await asyncio.sleep(0.3)
                except discord.Forbidden:
                    pass

        async def resolve_cat(ch):
            return cat_map.get(ch.category_id) if ch.category else None

        if "text_channels" in selected:
            for ch in sorted(src.text_channels, key=lambda c: c.position):
                try:
                    await dst.create_text_channel(
                        name=ch.name,
                        topic=ch.topic,
                        slowmode_delay=ch.slowmode_delay,
                        nsfw=ch.nsfw,
                        position=ch.position,
                        category=await resolve_cat(ch),
                        overwrites=build_overwrites(ch),
                    )
                    await asyncio.sleep(0.3)
                except discord.Forbidden:
                    pass

        if "voice_channels" in selected:
            for ch in sorted(src.voice_channels, key=lambda c: c.position):
                try:
                    await dst.create_voice_channel(
                        name=ch.name,
                        bitrate=min(ch.bitrate, dst.bitrate_limit),
                        user_limit=ch.user_limit,
                        position=ch.position,
                        category=await resolve_cat(ch),
                        overwrites=build_overwrites(ch),
                    )
                    await asyncio.sleep(0.3)
                except discord.Forbidden:
                    pass

        if "stage_channels" in selected:
            for ch in sorted(src.stage_channels, key=lambda c: c.position):
                try:
                    await dst.create_stage_channel(
                        name=ch.name,
                        position=ch.position,
                        category=await resolve_cat(ch),
                        overwrites=build_overwrites(ch),
                    )
                    await asyncio.sleep(0.3)
                except discord.Forbidden:
                    pass

        if "forum_channels" in selected:
            for ch in sorted(src.forums, key=lambda c: c.position):
                try:
                    await dst.create_forum(
                        name=ch.name,
                        topic=ch.topic,
                        position=ch.position,
                        category=await resolve_cat(ch),
                        overwrites=build_overwrites(ch),
                    )
                    await asyncio.sleep(0.3)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    async def clone_emojis(self, src: discord.Guild, dst: discord.Guild):
        for emoji in src.emojis:
            try:
                img = await emoji.read()
                await dst.create_custom_emoji(name=emoji.name, image=img)
                await asyncio.sleep(0.5)
            except (discord.Forbidden, discord.HTTPException):
                pass

    async def clone_stickers(self, src: discord.Guild, dst: discord.Guild):
        for sticker in src.stickers:
            try:
                s = await sticker.fetch()
                img = await s.read()
                await dst.create_sticker(
                    name=s.name,
                    description=s.description or s.name,
                    emoji=s.emoji,
                    file=discord.File(fp=io.BytesIO(img), filename=f"{s.name}.png"),
                )
                await asyncio.sleep(0.5)
            except (discord.Forbidden, discord.HTTPException, AttributeError):
                pass

    async def clone_bans(self, src: discord.Guild, dst: discord.Guild):
        async for ban_entry in src.bans():
            try:
                await dst.ban(ban_entry.user, reason=f"[Clone] {ban_entry.reason or 'No reason'}")
                await asyncio.sleep(0.3)
            except (discord.Forbidden, discord.HTTPException):
                pass

    async def clone_webhooks(self, src: discord.Guild, dst: discord.Guild):
        src_hooks = await src.webhooks()
        dst_text = {ch.name: ch for ch in dst.text_channels}
        for wh in src_hooks:
            if wh.channel and wh.channel.name in dst_text:
                try:
                    avatar = await wh.avatar.read() if wh.avatar else None
                    await dst_text[wh.channel.name].create_webhook(name=wh.name, avatar=avatar)
                    await asyncio.sleep(0.3)
                except (discord.Forbidden, discord.HTTPException):
                    pass


    @commands.hybrid_command(
        name="clone",
        description="Clone one server's configuration into another.",
        usage="clone <source_server_id> <target_server_id>",
        category="Admin",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(
        source="ID of the reference server to clone from.",
        target="ID of the destination server to clone into.",
    )
    async def clone(self, ctx: commands.Context, source: int, target: int):

        src = await self._get_guild(source)
        dst = await self._get_guild(target)

        if src is None or dst is None:
            return await ctx.reply(f"{cross} The bot is not in one (or both) of those servers.", mention_author=False)

        src_member = await self._member_in_guild(src, ctx.author.id)
        dst_member = await self._member_in_guild(dst, ctx.author.id)

        if src_member is None or not src_member.guild_permissions.administrator:
            return await ctx.reply(f"{cross} You need **Administrator** in the source server.", mention_author=False)
        if dst_member is None or not dst_member.guild_permissions.administrator:
            return await ctx.reply(f"{cross} You need **Administrator** in the destination server.", mention_author=False)
        if src.id == dst.id:
            return await ctx.reply(f"{cross} Source and destination can't be the same server.", mention_author=False)

        embed = discord.Embed(
            description=(
                f"**Source:** `{src.name}` (`{src.id}`)\n"
                f"**Destination:** `{dst.name}` (`{dst.id}`)\n\n"
                "Select what you want to clone, then press **Clone**.\n"
                "<:bionic_g_caution:1261557581319508068> This is **destructive** — existing content in the destination **will be wiped** first."
            ),
            color=colour,
        )
        embed.set_author(name="Assister Server Clone", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"{ctx.author} • Timeout: 60 seconds", icon_url=ctx.author.display_avatar.url)

        view = CloneView(ctx.author.id)
        msg = await ctx.reply(embed=embed, view=view, mention_author=False)
        await view.wait()

        if not view.confirmed:
            return

        selected = view.selected
        results: list[str] = []
        role_map: dict[int, discord.Role] = {}

        channel_keys = {"categories", "text_channels", "voice_channels", "stage_channels", "forum_channels"}
        keep = ctx.channel if ctx.guild.id == dst.id else None

        async def run(label: str, coro):
            try:
                result = await coro
                results.append(f"<:right:1496889463564009565> {label}")
                return result
            except Exception as e:
                results.append(f"{caution} {label} — {type(e).__name__}: {e}")
                return None

        if "roles"    in selected: await run("Wipe Roles",    self.wipe_roles(dst))
        if any(k in selected for k in channel_keys):
            await run("Wipe Channels", self.wipe_channels(dst, keep_channel=keep))
        if "emojis"   in selected: await run("Wipe Emojis",   self.wipe_emojis(dst))
        if "stickers" in selected: await run("Wipe Stickers", self.wipe_stickers(dst))
        if "webhooks" in selected: await run("Wipe Webhooks", self.wipe_webhooks(dst))

        if "roles" in selected:
            role_map = await run("Roles", self.clone_roles(src, dst)) or {}

        if any(k in selected for k in channel_keys):
            await run("Channels & Categories", self.clone_channels(src, dst, role_map, selected))

        if "emojis"        in selected: await run("Emojis",       self.clone_emojis(src, dst))
        if "stickers"      in selected: await run("Stickers",     self.clone_stickers(src, dst))
        if "bans"          in selected: await run("Bans",          self.clone_bans(src, dst))
        if "webhooks"      in selected: await run("Webhooks",      self.clone_webhooks(src, dst))
        if "server_name"   in selected: await run("Server Name",   dst.edit(name=src.name))
        if "server_icon"   in selected and src.icon:
            await run("Server Icon",   dst.edit(icon=await src.icon.read()))
        if "server_banner" in selected and src.banner:
            await run("Server Banner", dst.edit(banner=await src.banner.read()))

        result_embed = discord.Embed(
            description=f"{tick} **Server Cloned Successfully**\n\n<:readlist:1496885036971069450> Cloned Items:\n" + "\n".join(results) if results else "Nothing was cloned.",
            color=colour,
        )
        result_embed.set_footer(text=f"{src.name}  →  {dst.name}", icon_url=ctx.author.display_avatar.url)
        await msg.edit(content=None, embed=result_embed, view=None)

        if keep and any(k in selected for k in channel_keys):
            await asyncio.sleep(2)
            try:
                await keep.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerClone(bot))