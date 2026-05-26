import asyncio
import discord
from discord.ext import commands
from discord import app_commands, ui
from discord.ui import View, Button
import re, aiohttp
from utils.variables import *
from utils.checks import *
from utils.loads import lafk, saveafk, kalaloda
from utils.paginator import Ahm
from datetime import datetime


class AvatarView(View):
    def __init__(self, ctx, user, sav, mainav):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.user = user
        self.sav = sav
        self.mainav = mainav
        self.is_sav = bool(sav)

        self.toggle_btn = Button(
            label="Switch to Global Avatar" if self.is_sav else "Switch to Server Avatar",
            style=discord.ButtonStyle.primary,
            emoji="🔄",
            disabled=not sav,
            row=0,
        )
        self.toggle_btn.callback = self.toggle_callback
        self.add_item(self.toggle_btn)
        self.add_item(Button(
            label="Download",
            url=(sav if self.is_sav else mainav).url,
            style=discord.ButtonStyle.link,
            row=0,
        ))

    def make_embed(self):
        current = self.sav if self.is_sav else self.mainav
        label = "Server" if self.is_sav else "Global"
        embed = discord.Embed(color=colour)
        embed.set_author(name=f"{self.user}'s {label} Avatar", icon_url=self.ctx.author.display_avatar.url)
        embed.set_image(url=current.url)
        embed.set_footer(text=f"Requested by {self.ctx.author}", icon_url=self.ctx.author.display_avatar.url)
        return embed

    async def toggle_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Not your command.", ephemeral=True)
        self.is_sav = not self.is_sav
        self.toggle_btn.label = "Switch to Global Avatar" if self.is_sav else "Switch to Server Avatar"
        for item in self.children:
            if isinstance(item, Button) and item.url:
                item.url = (self.sav if self.is_sav else self.mainav).url
        await interaction.response.edit_message(embed=self.make_embed(), view=self)



CUSTOM_EMOJI_RE = re.compile(r"<(a?):([A-Za-z0-9_]+):(\d+)>")
URL_RE = re.compile(r"https?://\S+\.(?:png|jpg|jpeg|gif|webp)(\?\S*)?", re.IGNORECASE)
 
 
async def _fetch_bytes(url: str) -> bytes | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"lund emoji {e}")
    return None


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delms: dict[int, list] = {}
        self.active_builds = {}



    @commands.hybrid_command(
        name="addemoji",
        aliases=["stealemoji"],
        description="Add one or more emojis to the server",
        usage="addemoji <emoji1> [emoji2] [emoji3] ..."
    )
    @bled()
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.describe(emojis="One or more custom emojis or image URLs to add")
    async def addemoji(self, ctx: commands.Context, *, emojis: str = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        CUSTOM_EMOJI_RE = re.compile(r"<(a?):([A-Za-z0-9_]+):(\d+)>")
        URL_RE          = re.compile(r"https?://\S+\.(?:png|jpg|jpeg|gif|webp)(\?\S*)?", re.IGNORECASE)

        tokens: list[str] = []

        ref = ctx.message.reference
        if ref:
            try:
                replied = ref.resolved or await ctx.channel.fetch_message(ref.message_id)
                found = CUSTOM_EMOJI_RE.findall(replied.content)
                tokens = [f"<{a}:{n}:{i}>" for a, n, i in found]
            except Exception:
                return

        if not tokens:
            if not emojis:
                await self._addemoji_usage(ctx)
                return
            tokens = CUSTOM_EMOJI_RE.findall(emojis)
            tokens = [f"<{a}:{n}:{i}>" for a, n, i in tokens]
            url_tokens = URL_RE.findall(emojis) 
            url_tokens = URL_RE.finditer(emojis)
            for m in url_tokens:
                tokens.append(m.group(0))

        if not tokens:
            await self._send_error(
                ctx,
                f"No valid emojis or image URLs found.\n\n"
                f"**Accepted inputs:**\n"
                f"{e_dot} Custom emojis: `:emoji1: :emoji2: :emoji3:`\n"
                f"{e_dot} Direct image URLs ending in `.png`, `.jpg`, `.gif`, `.webp`\n"
                f"{e_dot} Reply to a message that contains emojis"
            )
            return

        added:  list[discord.Emoji] = []
        failed: list[tuple[str, str]] = []

        for token in tokens:
            emoji_name: str  = ""
            image_bytes: bytes | None = None

            custom_match = CUSTOM_EMOJI_RE.match(token)
            if custom_match:
                animated  = bool(custom_match.group(1))
                emoji_name = custom_match.group(2)
                emoji_id   = int(custom_match.group(3))
                ext        = "gif" if animated else "png"
                url        = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?quality=lossless"

                image_bytes = await _fetch_bytes(url)

                if image_bytes is None:
                    failed.append((emoji_name, "Could not download from Discord CDN"))
                    continue

            elif URL_RE.match(token):
                url        = token
                animated   = url.lower().split("?")[0].endswith(".gif")
                filename   = url.split("/")[-1].split("?")[0]
                emoji_name = re.sub(r"\.[^.]+$", "", filename)
                emoji_name = re.sub(r"[^A-Za-z0-9_]", "_", emoji_name)[:32]

                image_bytes = await _fetch_bytes(url)

                if image_bytes is None:
                    failed.append((url[:40] + "...", "Could not download from URL"))
                    continue

            else:
                failed.append((token[:30], "Unrecognised format"))
                continue

            emoji_name = re.sub(r"[^A-Za-z0-9_]", "_", emoji_name)[:32]
            if len(emoji_name) < 2:
                emoji_name = emoji_name.ljust(2, "_")

            if len(image_bytes) > 256 * 1024:
                failed.append((emoji_name, "Image exceeds 256 KB limit"))
                continue

            try:
                new_emoji = await ctx.guild.create_custom_emoji(
                    name=emoji_name,
                    image=image_bytes,
                    reason=f"Added by {ctx.author} via addemoji"
                )
                added.append(new_emoji)
            except discord.HTTPException as e:
                if e.code == 30008:
                    failed.append((emoji_name, "Server emoji limit reached"))
                    break
                else:
                    failed.append((emoji_name, f"Discord error: {e.text}"))
                    print(e)
            except Exception as e:
                failed.append((emoji_name, "Unexpected error"))
                print(e)

        layout = ui.LayoutView(timeout=0)

        if added:
            added_lines = "  ".join(str(e) for e in added)
            detail_lines = "\n".join(
                f"{e_dot} {str(e)} **`:{e.name}:`** — `{e.id}` {'*(animated)*' if e.animated else ''}"
                for e in added
            )

            header = ui.Container()
            header.add_item(ui.TextDisplay(
                f"## {tick} {'Emoji' if len(added) == 1 else 'Emojis'} Added\n"
                f"{added_lines}"
            ))
            layout.add_item(header)

            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

            body = ui.Container()
            body.add_item(ui.TextDisplay(detail_lines))
            layout.add_item(body)
        
        if failed:
            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            fail_lines = "\n".join(f"{cross} **{name}** — {reason}" for name, reason in failed)
            fail_block = ui.Container()
            fail_block.add_item(ui.TextDisplay(
                f"**Failed ({len(failed)}):**\n{fail_lines}"
            ))
            layout.add_item(fail_block)

        if not added and not failed:
            await self._send_error(ctx, "Nothing was processed.")
            return

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Added by {ctx.author.display_name}  •  {ctx.guild.name}  •  "
            f"{len(added)} added{f', {len(failed)} failed' if failed else ''}"
        ))

        await ctx.reply(view=layout, mention_author=False)

    async def _addemoji_usage(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix   = guild_prefix(guild_id) if guild_id else '.'
        layout   = ui.LayoutView(timeout=0)
        c = ui.Container()
        c.add_item(ui.TextDisplay(
            f"## ❓ Add Emoji\n"
            f"Add one or more emojis to this server.\n\n"
            f"**Usage:**\n"
            f"`{prefix}addemoji <emoji1> [emoji2] [emoji3] ...`\n\n"
            f"**Examples:**\n"
            f"{e_dot} `{prefix}addemoji :emoji1: :emoji2: :emoji3:`\n"
            f"{e_dot} `{prefix}addemoji https://example.com/img.png`\n"
            f"{e_dot} Reply to any message containing emojis with `{prefix}addemoji`"
        ))
        layout.add_item(c)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(f"-# {ctx.guild.name}  •  Assister"))
        await ctx.reply(view=layout, mention_author=False)

    async def _send_error(self, ctx: commands.Context, message: str):
        layout = ui.LayoutView(timeout=0)
        c = ui.Container()
        c.add_item(ui.TextDisplay(f"## {cross} Failed to Add Emoji\n{message}"))
        layout.add_item(c)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Requested by {ctx.author.display_name}  •  {ctx.guild.name}"
        ))
        await ctx.reply(view=layout, mention_author=False)



    @commands.hybrid_command(
        name="addsticker",
        aliases=["steal"],
        description="Add a sticker from a replied message to the server",
        usage="addsticker [name]"
    )
    @bled()
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(name="Optional custom name for the sticker")
    async def addsticker(self, ctx: commands.Context, *, name: str = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        def err(msg):
            layout = ui.LayoutView(timeout=0)
            c = ui.Container()
            c.add_item(ui.TextDisplay(msg))
            layout.add_item(c)
            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            layout.add_item(ui.TextDisplay(f"-# Requested by {ctx.author.display_name}  •  {ctx.guild.name}"))
            return layout

        ref = ctx.message.reference
        if not ref:
            return await ctx.reply(view=err(f"## {cross} No Replied Message\nReply to a message that contains a sticker and run this command."), mention_author=False)

        try:
            replied = ref.resolved or await ctx.channel.fetch_message(ref.message_id)
        except Exception:
            return await ctx.reply(view=err(f"## {cross} Failed\nCould not fetch the replied message."), mention_author=False)

        if not replied.stickers:
            return await ctx.reply(view=err(f"## {cross} No Sticker Found\nThe replied message doesn't contain any stickers."), mention_author=False)

        sticker_item = replied.stickers[0]

        try:
            full_sticker: discord.GuildSticker = await sticker_item.fetch()
        except Exception:
            return await ctx.reply(view=err(f"## {cross} Failed\nCould not fetch sticker details from Discord."), mention_author=False)

        if full_sticker.type != discord.StickerType.guild:
            return await ctx.reply(view=err(f"## {cross} Unsupported Sticker\nOnly custom guild stickers can be stolen. Nitro/standard stickers cannot be downloaded."), mention_author=False)

        sticker_name = re.sub(r"[^A-Za-z0-9_ ]", "_", name or full_sticker.name)[:30].strip() or "sticker"
        description  = full_sticker.description or sticker_name
        emoji_str    = full_sticker.emoji or "⭐"
        fmt          = full_sticker.format
        url          = full_sticker.url

        image_bytes = await _fetch_bytes(url)
        if image_bytes is None:
            return await ctx.reply(view=err(f"## {cross} Download Failed\nCould not download the sticker image from Discord's CDN."), mention_author=False)

        if len(image_bytes) > 512 * 1024:
            return await ctx.reply(view=err(f"## {cross} File Too Large\nSticker exceeds Discord's 512 KB limit (`{len(image_bytes) // 1024} KB`)."), mention_author=False)

        import io
        if fmt == discord.StickerFormatType.lottie:
            file = discord.File(fp=io.BytesIO(image_bytes), filename="sticker.json")
        elif fmt == discord.StickerFormatType.apng:
            file = discord.File(fp=io.BytesIO(image_bytes), filename="sticker.gif")
        else:
            file = discord.File(fp=io.BytesIO(image_bytes), filename="sticker.png")

        try:
            new_sticker: discord.GuildSticker = await ctx.guild.create_sticker(
                name        = sticker_name,
                description = description,
                emoji       = emoji_str,
                file        = file,
                reason      = f"Stolen by {ctx.author} via stealsticker"
            )
        except discord.HTTPException as e:
            reason = "Server sticker limit reached" if e.code == 30039 else f"Discord error: {e.text}"
            return await ctx.reply(view=err(f"## {cross} Upload Failed\n{reason}"), mention_author=False)
        except Exception as e:
            return await ctx.reply(view=err(f"## {cross} Unexpected Error\nSomething went wrong while uploading."), mention_author=False)

        layout = ui.LayoutView(timeout=0)
        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## {tick} Sticker Added\n"
            f"{e_dot} **`{new_sticker.name}`** — `{new_sticker.id}`\n"
            f"{e_dot} Emoji tag: {emoji_str}\n"
            f"{e_dot} Format: `{fmt.name}`"
        ))
        layout.add_item(header)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(f"-# Added by {ctx.author.display_name}  •  {ctx.guild.name}"))
        await ctx.reply(view=layout, mention_author=False)
        



    @commands.hybrid_command(name="embed", description="Interactively build and send an embed", aliases=['createembed', 'buildembed'])
    @bled()
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def embed(self, ctx: commands.Context):
        uid = ctx.author.id

        if self.active_builds.get(uid):
            return await ctx.reply("❌ You already have an active embed builder.", mention_author=False, delete_after=5)
        
        self.active_builds[uid] = True

        def check(m):
            return m.author.id == uid and m.channel == ctx.channel

        async def ask(question, timeout=60):
            qmsg = await ctx.send(question)
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=timeout)
            except asyncio.TimeoutError:
                await qmsg.delete()
                await ctx.send("⏰ Timeout reached. Embed building cancelled.", delete_after=5)
                raise asyncio.CancelledError
            await qmsg.delete()
            await msg.delete()
            if msg.content.lower() == "cancel":
                raise asyncio.CancelledError
            return None if msg.content.lower() == "none" else msg

        try:
            liveebd = discord.Embed(title="", description="This is your embed preview...", color=0x302c34)
            preebd = await ctx.reply(content="**Embed Preview** — Might take sometime to load, keep going!\n**Type `cancel` anytime to cancel. Type `none` to skip a field.**", embed=liveebd, mention_author=False)

            channel_msg = await ask("**Which channel should I send the embed in? Mention it or type `here` for this channel:**")
            if channel_msg.content.lower() == "here":
                target_channel = ctx.channel
            elif channel_msg.channel_mentions:
                target_channel = channel_msg.channel_mentions[0]
            else:
                await ctx.send("⚠ Invalid channel, using this channel instead.", delete_after=5)
                target_channel = ctx.channel


            title_msg = await ask("**Enter the `title` of the embed:**")
            if title_msg:
                liveebd.title = title_msg.content
                await preebd.edit(embed=liveebd)


            desc_msg = await ask("**Enter the `description` of the embed:**")
            if desc_msg:
                liveebd.description = desc_msg.content
                await preebd.edit(embed=liveebd)

            author_msg = await ask("**Enter the `author name` (or `none` to skip):**")
            author_icon = None
            if author_msg:
                icon_msg = await ask("**Enter the `author icon URL` (or `none` to skip):")
                author_icon = icon_msg.content if icon_msg else None
                liveebd.set_author(name=author_msg.content, icon_url=author_icon)
                await preebd.edit(embed=liveebd)

            footer_msg = await ask("**Enter the `footer text` (or `none` to skip):**")
            footer_icon = None
            if footer_msg:
                icon_msg = await ask("**Enter the `footer icon URL` (or `none` to skip):**")
                footer_icon = icon_msg.content if icon_msg else None
                liveebd.set_footer(text=footer_msg.content, icon_url=footer_icon)
                await preebd.edit(embed=liveebd)

            thumb_msg = await ask("**Enter the `thumbnail URL` (or `none` to skip):**")
            if thumb_msg:
                liveebd.set_thumbnail(url=thumb_msg.content)
                await preebd.edit(embed=liveebd)

            image_msg = await ask("**Enter the `image URL` (or `none` to skip):**")
            if image_msg:
                liveebd.set_image(url=image_msg.content)
                await preebd.edit(embed=liveebd)

            color_msg = await ask("**Enter the `hex color` of the embed (like `#FF0000`) or `none` for default:**")
            if color_msg:
                try:
                    liveebd.color = discord.Color(int(color_msg.content.strip("#"), 16))
                    await preebd.edit(embed=liveebd)
                except:
                    await ctx.send("**⚠ Invalid color, using default.**", delete_after=5)

            button_msg = await ask("**Enter a `link button URL` (or `none` to skip):**")
            view = None
            if button_msg and button_msg.content.startswith(("http://", "https://")):
                text_msg = await ask("**Enter the `link button text` (or `none` for default):**")
                button_text = text_msg.content if text_msg else "Click Here"
                view = View()
                view.add_item(Button(label=button_text, url=button_msg.content))
            elif button_msg:
                await ctx.send("**⚠ Invalid URL, skipping button.**", delete_after=5)

            await preebd.delete()
            await ctx.message.delete()
            await target_channel.send(embed=liveebd, view=view)
            await ctx.send(f"**✅ Embed sent successfully in {target_channel.mention}!**", delete_after=5)

        except asyncio.CancelledError:
            await ctx.send(f"**{cross} Embed creation cancelled.**", delete_after=5)
        finally:
            self.active_builds[uid] = False


    @commands.hybrid_command(name="cancelembed", description="Cancel your active embed builder")
    @bled()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def cancelembed(self, ctx: commands.Context):
        uid = ctx.author.id
        if self.active_builds.get(uid):
            self.active_builds[uid] = False
            await ctx.reply("✅ Embed building cancelled.", delete_after=5, mention_author=False)
        else:
            await ctx.reply("❌ You don't have an active embed builder.", delete_after=5, mention_author=False)

            

    @commands.hybrid_command(description="Sets you AFK globally.", usage="afk [reason]", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(reason="Reason for your AFK.")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        ahmd = lafk()
        timestamp = datetime.now().isoformat()
        ahmd[ctx.author.id] = {"reason": reason, "timestamp": timestamp}
        saveafk(ahmd)
        unix_timestamp = kalaloda(timestamp)

        embed = discord.Embed(color=colour)
        embed.set_author(name="AFK Set", icon_url=ctx.author.display_avatar.url)
        embed.description = (
            f"{e_dot} Marked you AFK globally.\n"
            f"{e_dot} Reason: **{reason}**\n"
            f"{e_dot} Set at: <t:{unix_timestamp}:F>"
        )
        await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(aliases=["si"], description="Shows the server information.", usage="si", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def serverinfo(self, ctx: commands.Context):
        server = ctx.guild
        icon = server.icon.url if server.icon else None
        author_icon = ctx.author.display_avatar.url
        TOTAL = 4

        def base(page: int) -> discord.Embed:
            e = discord.Embed(color=colour)
            e.set_author(name=server.name, icon_url=icon)
            if icon:
                e.set_thumbnail(url=icon)
            e.set_footer(
                text=f"Requested by {ctx.author}  •  Page {page}/{TOTAL}",
                icon_url=author_icon,
            )
            return e

        p1 = base(1)
        tmem = server.member_count
        bots = sum(1 for m in server.members if m.bot)
        tch = len(server.text_channels)
        vch = len(server.voice_channels)
        tchlocked = sum(1 for c in server.text_channels if c.overwrites_for(server.default_role).read_messages is False)
        vchlocked = sum(1 for c in server.voice_channels if c.overwrites_for(server.default_role).connect is False)

        p1.add_field(name=f"{e_dot} General", value=(
            f"**Name:** {server.name}\n"
            f"**ID:** `{server.id}`\n"
            f"**Owner:** {server.owner.mention}\n"
            f"**Created:** <t:{int(server.created_at.timestamp())}:R>"
        ), inline=False)
        p1.add_field(name="", value="\u200a", inline=False)
        p1.add_field(name=f"{e_dot} Members", value=(
            f"{e_dot} **Total:** {tmem}\n{e_dot} **Humans:** {tmem - bots}\n{e_dot} **Bots:** {bots}"
        ), inline=False)
        p1.add_field(name="", value="\u200a", inline=False)
        p1.add_field(name=f"{e_dot} Channels", value=(
            f"{e_dot} **Text:** {tch} ({tchlocked} locked)\n{e_dot} **Voice:** {vch} ({vchlocked} locked)\n"
            f"{e_dot} **Total:** {len(server.channels)}"
        ), inline=False)
        if server.banner:
            p1.set_image(url=server.banner.url)

        p2 = base(2)
        p2.add_field(name=f"{e_dot} Boost Info", value=(
            f"**Level:** {server.premium_tier}  •  **Boosts:** {server.premium_subscription_count}\n"
            f"**Boost Bar:** {'Yes' if server.premium_tier else 'No'}"
        ), inline=False)
        p2.add_field(name="", value="\u200a", inline=False)
        p2.add_field(name=f"{e_dot} Extras", value="\n".join([
            f"**Verification:** {server.verification_level.name}",
            f"**Upload Limit:** {server.filesize_limit / 1024 / 1024:.2f} MB",
            f"**AFK Channel:** {server.afk_channel.mention if server.afk_channel else 'None'}",
            f"**AFK Timeout:** {server.afk_timeout // 60}m",
            f"**Rules Channel:** {server.rules_channel.mention if server.rules_channel else 'None'}",
            f"**2FA Required:** {'Yes' if server.mfa_level == 1 else 'No'}",
            f"**Explicit Filter:** {server.explicit_content_filter.name}",
            f"**System Channel:** {server.system_channel.mention if server.system_channel else 'None'}",
        ]), inline=False)

        lul = {
            'VANITY_URL': "Vanity URL", 'PARTNERED': "Partnered", 'COMMUNITY': "Community",
            'DISCOVERABLE': "Discoverable", 'ANIMATED_ICON': "Animated Icon", 'BANNER': "Banner",
            'WELCOME_SCREEN_ENABLED': "Welcome Screen", 'NEWS': "News Channels", 'ROLE_ICONS': "Role Icons",
            'PRIVATE_THREADS': "Private Threads", 'AUTO_MODERATION': "Auto Moderation",
            'GUILD_ONBOARDING': "Guild Onboarding", 'MORE_STICKERS': "More Stickers",
            'MONETIZATION_ENABLED': "Monetization", 'INVITE_SPLASH': "Invite Splash",
            'MEMBER_VERIFICATION_GATE_ENABLED': "Membership Screening",
            'PREVIEW_ENABLED': "Server Preview", 'THREE_DAY_THREAD_ARCHIVE': "3-Day Thread Archive",
        }
        features = [f"{tick} {lul[f]}" for f in server.features if f in lul]
        p3 = base(3)
        p3.add_field(
            name=f"{e_dot} Server Features",
            value="\n".join(features) if features else "No notable features.",
            inline=False,
        )

        roles_list = [r.mention for r in reversed(server.roles) if r.name != "@everyone"]
        p4 = base(4)
        p4.add_field(
            name=f"{e_dot} Roles [{len(roles_list)}]",
            value=(
                ", ".join(roles_list)
                if len(roles_list) <= 40
                else f"Too many roles to display ({len(roles_list)} total)"
            ),
            inline=False,
        )

        paginator = Ahm([p1, p2, p3, p4])
        await paginator.start(ctx)


    @commands.hybrid_command(aliases=["mc"], description="Shows member count of the server.", usage="mc", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def membercount(self, ctx: commands.Context):
        guild = ctx.guild
        hmn = sum(1 for m in guild.members if not m.bot)
        bots = sum(1 for m in guild.members if m.bot)

        embed = discord.Embed(color=colour)
        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
        embed.description = (
            f"{e_dot} **Total:** {guild.member_count}\n"
            f"{e_dot} **Humans:** {hmn}\n"
            f"{e_dot} **Bots:** {bots}"
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(aliases=["av"], description="Shows avatar of the member.", usage="av [member]", category="Utility")
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(user="Select the member to view their avatar.")
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        user = user or ctx.author
        sav = user.guild_avatar if isinstance(user, discord.Member) and user.guild_avatar else None
        mainav = user.avatar or user.default_avatar

        view = AvatarView(ctx, user, sav, mainav)
        await ctx.reply(embed=view.make_embed(), view=view, mention_author=False)


    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        cid = message.channel.id
        if cid not in self.delms:
            self.delms[cid] = []
        self.delms[cid].append({"message": message, "sender": message.author})
        if len(self.delms[cid]) > 10:
            self.delms[cid].pop(0)

    @commands.hybrid_command(name="snipe", description="Snipes the most recently deleted message.", usage="snipe", category="Utility")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @bled()
    async def snipe(self, ctx: commands.Context):
        cid = ctx.channel.id
        if cid not in self.delms or not self.delms[cid]:
            return await ctx.reply("**No deleted messages to snipe.**", delete_after=10, mention_author=False)

        delm = self.delms[cid][-1]
        msg = delm["message"]
        sender = delm["sender"]

        embed = discord.Embed(color=colour)
        embed.description = (
            f"{e_dot} **{str(sender)}'s message was deleted:**\n"
            f"```{msg.content or '*[No text content]*'}```"
        )
        if msg.attachments:
            embed.add_field(name="Attachment", value=msg.attachments[0].url, inline=False)
        embed.set_author(name="Assister Snipe", icon_url=botav)
        embed.set_footer(
            text=f"Sniped by {ctx.author}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="snipeall", description="Snipes the last 10 deleted messages.", usage="snipeall", category="Utility")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @bled()
    async def snipeall(self, ctx: commands.Context):
        cid = ctx.channel.id
        if cid not in self.delms or not self.delms[cid]:
            return await ctx.reply("**No deleted messages to snipe.**", delete_after=10, mention_author=False)

        msgs = self.delms[cid][-10:]
        embed = discord.Embed(color=colour)
        embed.set_author(
            name=f"Last {len(msgs)} deleted messages",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
        )

        for i, delm in enumerate(reversed(msgs), 1):
            msg = delm["message"]
            sender = delm["sender"]
            content = msg.content or "*[No text content]*"
            embed.add_field(
                name="",
                value=f"{e_dot} **{str(sender)}:** {content}",
                inline=False,
            )
            if i != len(msgs):
                embed.add_field(name="", value="\u200a", inline=False)

        embed.set_footer(
            text=f"Sniped by {ctx.author}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(aliases=["ui", "whois"], description="Fetch user information.", usage="userinfo [user]", category="Utility")
    @commands.cooldown(1, 8, commands.BucketType.user)
    @bled()
    @app_commands.describe(user="Select the member to view their information.")
    async def userinfo(self, ctx: commands.Context, user: discord.User = None):
        target_user: discord.User = user or ctx.author

        try:
            fetched = await self.bot.fetch_user(target_user.id)
        except Exception:
            return await ctx.reply("**Unable to fetch user details.**", mention_author=False)

        member: discord.Member | None = ctx.guild.get_member(target_user.id)
        if member is None:
            try:
                member = await ctx.guild.fetch_member(target_user.id)
            except (discord.NotFound, discord.HTTPException):
                member = None

        avatar_url = fetched.avatar.url if fetched.avatar else fetched.default_avatar.url
        badges = " ".join(self.get_badge_emoji(f.name) for f in fetched.public_flags.all()) or "None"
        author_icon = ctx.author.display_avatar.url
        is_member = member is not None
        TOTAL = 2 if is_member else 1

        def base(page: int) -> discord.Embed:
            e = discord.Embed(color=colour)
            e.set_thumbnail(url=avatar_url)
            e.set_author(name=f"{fetched.name}'s Info", icon_url=avatar_url)
            e.set_footer(
                text=f"Requested by {ctx.author}  •  Page {page}/{TOTAL}",
                icon_url=author_icon,
            )
            if fetched.banner:
                e.set_image(url=fetched.banner.url)
            return e

        p1 = base(1)
        p1.add_field(name=f"{e_dot} General", value=(
            f"**Username:** {fetched.name}\n"
            f"**ID:** `{fetched.id}`\n"
            f"**Display Name:** {member.display_name if is_member else fetched.display_name}\n"
            f"**Created:** <t:{int(fetched.created_at.timestamp())}:R>\n"
            f"**Bot:** {'Yes' if fetched.bot else 'No'}\n"
            f"**Badges:** {badges}"
        ), inline=False)

        if not is_member:
            await ctx.reply(embed=p1, mention_author=False)
            return

        p2 = base(2)
        p2.add_field(name=f"{e_dot} Guild Info", value=(
            f"**Joined:** <t:{int(member.joined_at.timestamp())}:R>\n"
            f"**Boosting:** {'Yes' if member.premium_since else 'No'}\n"
            f"**In Voice:** {member.voice.channel.mention if member.voice else 'No'}\n"
            f"**Acknowledgement:** "
            + (
                "Server Owner" if member == ctx.guild.owner
                else "Admin" if member.guild_permissions.administrator
                else "Member"
            )
        ), inline=False)
        p2.add_field(name="", value="\u200a", inline=False)

        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        p2.add_field(name=f"{e_dot} Roles [{len(roles)}]", value=(
            f"**Top Role:** {member.top_role.mention}\n"
            + (", ".join(roles) if len(roles) <= 20 else f"{len(roles)} roles — too many to list")
        ), inline=False)
        p2.add_field(name="", value="\u200a", inline=False)

        key_perms = [
            perm.replace("_", " ").title()
            for perm in [
                "kick_members", "ban_members", "administrator", "manage_channels",
                "manage_messages", "mention_everyone", "manage_roles", "manage_webhooks",
            ]
            if getattr(member.guild_permissions, perm)
        ]
        p2.add_field(
            name=f"{e_dot} Key Permissions",
            value=", ".join(key_perms) if key_perms else "None",
            inline=False,
        )

        paginator = Ahm([p1, p2])
        await paginator.start(ctx)

    def get_badge_emoji(self, badge_name: str):
        lul = {
            "staff": "<:trial_Staff:1497628595189977088>",
            "partner": "<:Discord_partner:1497547092166447225>",
            "hypesquad": "<:hypesquad_events:1497546705359343747>",
            "bug_hunter": "<:goldbughunter:1497628360908607540>",
            "hypesquad_bravery": "<:hypesquad:1497628083304403066>",
            "hypesquad_brilliance": "<:hypesquad:1497628070079893595>",
            "hypesquad_balance": "<:hypesquad:1497627845625909412>",
            "early_supporter": "<:early:1497546978081505391>",
            "verified_bot": "<:verified_bot_1:1497629019783303361><:verified_bot_2:1497629035839094944><:verified_bot_3:1497629050758496317>",
            "verified_bot_developer": "<:bionic_g_VerifiedBotDeveloper:1261552705697091697>",
            "bug_hunter_level_2": "<:bughunter:1497629459610599474>",
            "premium_early_supporter": "<:early:1497546978081505391>",
            "discord_certified_moderator": "<:mod:1497629704868331710>",
            "system": "<:discord_system:1266017065320448030>",
        }
        return lul.get(badge_name, badge_name)


    @commands.hybrid_group(name="banner", description="Displays banner information.", usage="banner", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def banner(self, ctx: commands.Context):
        cmd = self.bot.get_command("help")
        if cmd:
            await ctx.invoke(cmd, query="utility")

    @banner.command(name="user", description="Displays the banner of a user.", usage="banner user [member]", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to view their banner.")
    async def banner_user(self, ctx: commands.Context, member: discord.User = None):
        member = member or ctx.author
        fetched = await ctx.bot.fetch_user(member.id)

        if not fetched.banner:
            embed = discord.Embed(description=f"{cross} {member.mention} has no banner.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        webp = fetched.banner.replace(format="webp").url
        jpg  = fetched.banner.replace(format="jpg").url
        png  = fetched.banner.replace(format="png").url

        embed = discord.Embed(color=colour)
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_image(url=fetched.banner.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        view = View()
        view.add_item(Button(label="WEBP", url=webp, style=discord.ButtonStyle.link))
        view.add_item(Button(label="PNG",  url=png,  style=discord.ButtonStyle.link))
        view.add_item(Button(label="JPG",  url=jpg,  style=discord.ButtonStyle.link))
        if fetched.banner.is_animated():
            gif = fetched.banner.replace(format="gif").url
            view.add_item(Button(label="GIF", url=gif, style=discord.ButtonStyle.link))

        await ctx.reply(embed=embed, view=view, mention_author=False)

    @banner.command(name="server", description="Displays the server banner.", usage="banner server", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def banner_server(self, ctx: commands.Context):
        server = ctx.guild
        if not server.banner:
            embed = discord.Embed(description=f"{cross} **{server.name}** has no banner.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        webp = server.banner.replace(format="webp").url
        jpg  = server.banner.replace(format="jpg").url
        png  = server.banner.replace(format="png").url

        embed = discord.Embed(color=colour)
        embed.set_author(name=server.name, icon_url=server.icon.url if server.icon else None)
        embed.set_image(url=server.banner.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        view = View()
        view.add_item(Button(label="WEBP", url=webp, style=discord.ButtonStyle.link))
        view.add_item(Button(label="PNG",  url=png,  style=discord.ButtonStyle.link))
        view.add_item(Button(label="JPG",  url=jpg,  style=discord.ButtonStyle.link))
        if server.banner.is_animated():
            gif = server.banner.replace(format="gif").url
            view.add_item(Button(label="GIF", url=gif, style=discord.ButtonStyle.link))

        await ctx.reply(embed=embed, view=view, mention_author=False)


    @commands.hybrid_command(name="servericon", description="Displays the server icon.", usage="servericon", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def servericon(self, ctx: commands.Context):
        server = ctx.guild
        if not server.icon:
            embed = discord.Embed(description=f"{cross} **{server.name}** has no icon.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        icon = server.icon
        embed = discord.Embed(color=colour)
        embed.set_author(name=f"{server.name}'s Icon", icon_url=icon.url)
        embed.set_image(url=icon.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        view = View()
        view.add_item(Button(label="WEBP", url=icon.replace(format="webp").url, style=discord.ButtonStyle.link))
        view.add_item(Button(label="PNG",  url=icon.replace(format="png").url,  style=discord.ButtonStyle.link))
        view.add_item(Button(label="JPG",  url=icon.replace(format="jpg").url,  style=discord.ButtonStyle.link))
        if icon.is_animated():
            view.add_item(Button(label="GIF", url=icon.replace(format="gif").url, style=discord.ButtonStyle.link))

        await ctx.reply(embed=embed, view=view, mention_author=False)



    @commands.hybrid_command(name="roleinfo", aliases=["ri"], description="Shows role information.", usage="roleinfo <role>", category="Utility")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def roleinfo(self, ctx: commands.Context, role: discord.Role):
        embed = discord.Embed(color=role.color if role.color.value else colour)
        embed.set_author(name=f"Role: {role.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)

        embed.add_field(name=f"{e_dot} General", value=(
            f"**Name:** {role.mention}\n"
            f"**ID:** `{role.id}`\n"
            f"**Color:** `#{role.color.value:06X}`\n"
            f"**Created:** <t:{int(role.created_at.timestamp())}:R>"
        ), inline=False)
        embed.add_field(name="", value="\u200a", inline=False)

        embed.add_field(name=f"{e_dot} Details", value=(
            f"**Members:** {len(role.members)}\n"
            f"**Position:** {role.position}\n"
            f"**Hoisted:** {'Yes' if role.hoist else 'No'}\n"
            f"**Mentionable:** {'Yes' if role.mentionable else 'No'}\n"
            f"**Managed:** {'Yes' if role.managed else 'No'}"
        ), inline=False)
        embed.add_field(name="", value="\u200a", inline=False)

        key_perms = [
            perm.replace("_", " ").title()
            for perm in [
                "administrator", "kick_members", "ban_members", "manage_channels",
                "manage_messages", "manage_roles", "mention_everyone", "manage_webhooks",
            ]
            if getattr(role.permissions, perm)
        ]
        embed.add_field(
            name=f"{e_dot} Key Permissions",
            value=", ".join(key_perms) if key_perms else "None",
            inline=False,
        )

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(Utility(bot))