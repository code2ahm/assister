import discord
from discord import ui
from discord.ext import commands
from discord import app_commands
from utils.loads import *
from utils.variables import *
from utils.checks import *
from utils.prefixes import *




DEFAULT_MESSAGE = "Welcome to **{server}**, {user}! You are member **#{count}**."
DEFAULT_TITLE   = "Welcome!"
DEFAULT_FOOTER  = "{server} • Member #{count}"
DEFAULT_AUTHOR = "{server}"

EMBED_LIMITS = {
    "title":   256,
    "message": 4096,
    "footer":  2048,
    "author":  256,
}

WELCOME_VARS = (
    f"{e_dot} `{{user}}` — Mentions the member\n"
    f"{e_dot} `{{username}}` — Member's username\n"
    f"{e_dot} `{{server}}` — Server name\n"
    f"{e_dot} `{{count}}` — Current member count"
)

DEFAULT_SETTINGS = {
    "enabled":        False,
    "channel_id":     None,
    "message":        DEFAULT_MESSAGE,
    "title":          DEFAULT_TITLE,
    "footer":         DEFAULT_FOOTER,
    "author":         DEFAULT_AUTHOR,
    "color":          None,
    "thumbnail":      "user",
    "thumbnail_url":  None,
    "image":          "none",
    "image_url":      None,
    "ping":           False,
}


def _format(template: str, member: discord.Member) -> str:
    return template.replace(
        "{user}",     member.mention
    ).replace(
        "{username}", member.display_name
    ).replace(
        "{server}",   member.guild.name
    ).replace(
        "{count}",    str(member.guild.member_count)
    )

def _get_thumbnail(config: dict, member: discord.Member) -> str | None:
    mode = config.get("thumbnail", "user")
    if mode == "user":
        return member.display_avatar.url
    elif mode == "server":
        return member.guild.icon.url if member.guild.icon else None
    elif mode == "custom":
        return config.get("thumbnail_url")
    return None

def _get_image(config: dict, member: discord.Member, banner_url: str = None) -> str | None:
    mode = config.get("image", "none")
    if mode == "userbanner":
        return banner_url or None
    elif mode == "serverbanner":
        return member.guild.banner.url if member.guild.banner else None
    elif mode == "custom":
        return config.get("image_url")
    return None

def _get_color(config: dict) -> discord.Color:
    raw = config.get("color")
    if raw:
        try:
            return discord.Color(int(raw.strip("#"), 16))
        except Exception:
            pass
    return discord.Color(colour)


def _build_embed(config: dict, member: discord.Member, banner_url: str = None) -> discord.Embed:
    raw_title = config.get("title", DEFAULT_TITLE)
    title     = _format(raw_title, member) if raw_title else ""
    desc      = _format(config.get("message", DEFAULT_MESSAGE), member)
    footer    = _format(config.get("footer",  DEFAULT_FOOTER),  member)
    author    = _format(config.get("author",  DEFAULT_AUTHOR),  member)
    clr       = _get_color(config)
    thumbnail = _get_thumbnail(config, member)
    image     = _get_image(config, member, banner_url)

    guild_icon = member.guild.icon.url if member.guild.icon else None

    embed = discord.Embed(title=title, description=desc, color=clr)
    embed.set_footer(text=footer, icon_url=guild_icon)
    embed.set_author(name=author, icon_url=guild_icon)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    return embed



class WelcomeSuccessLayout(ui.LayoutView):
    def __init__(self, title: str, body_text: str, user: discord.abc.User, footer: str):
        super().__init__(timeout=0)
        self._build(title, body_text, user, footer)

    def _build(self, title, body_text, user, footer):
        self.clear_items()
        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {tick} {title}"))
        self.add_item(header)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        body = ui.Container()
        body.add_item(ui.TextDisplay(body_text))
        self.add_item(body)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay(f"-# Updated by {user.display_name}  •  Assister Welcomer"))


class WelcomeConfirmLayout(ui.LayoutView):
    def __init__(self, author_id: int, title: str, body_text: str, on_confirm, on_cancel=None):
        super().__init__(timeout=60)
        self.author_id   = author_id
        self._confirm_cb = on_confirm
        self._cancel_cb  = on_cancel
        self._build(title, body_text)

    def _build(self, title, body_text):
        self.clear_items()
        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## <:bionic_g_caution:1261557581319508068> {title}"))
        self.add_item(header)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        body = ui.Container()
        body.add_item(ui.TextDisplay(body_text))
        self.add_item(body)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Welcomer  •  Confirm action"))
        btn_row = ui.ActionRow()
        yes = ui.Button(label="Confirm", style=discord.ButtonStyle.success, custom_id="wlc_confirm_yes")
        no  = ui.Button(label="Cancel",  style=discord.ButtonStyle.danger,  custom_id="wlc_confirm_no")
        yes.callback = self._yes
        no.callback  = self._no
        btn_row.add_item(yes)
        btn_row.add_item(no)
        self.add_item(btn_row)

    async def _yes(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return
        await self._confirm_cb(interaction)

    async def _no(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return
        if self._cancel_cb:
            await self._cancel_cb(interaction)
        else:
            self.clear_items()
            c = ui.Container()
            c.add_item(ui.TextDisplay(f"## {grey} Action Cancelled"))
            self.add_item(c)
            await interaction.response.edit_message(view=self)


class WelcomeToggleLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_name: str, welcome: dict,
                 guild_id: str, save_fn, field: str, label: str):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_name = guild_name
        self.welcome    = welcome
        self.guild_id   = guild_id
        self.save_fn    = save_fn
        self.field      = field
        self.label      = label
        self._build()

    def _build(self):
        self.clear_items()
        enabled = self.welcome.get(self.guild_id, {}).get(self.field, False)
        status  = "<a:enable:1496894249822720052> Enabled" if enabled else "<a:disable:1496894585035817022> Disabled"

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:bionic_g_caution:1261557581319508068> {self.label} — {self.guild_name}\n"
            f"Current status: {status}"
        ))
        self.add_item(header)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay(f"-# Assister Welcomer  •  {self.label}"))

        btn_row = ui.ActionRow()
        enable_btn  = ui.Button(label="Enable",  style=discord.ButtonStyle.success, custom_id=f"wlc_{self.field}_enable")
        disable_btn = ui.Button(label="Disable", style=discord.ButtonStyle.danger,  custom_id=f"wlc_{self.field}_disable")
        enable_btn.callback  = self._on_enable
        disable_btn.callback = self._on_disable
        btn_row.add_item(enable_btn)
        btn_row.add_item(disable_btn)
        self.add_item(btn_row)

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return False
        return True

    async def _on_enable(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        self.welcome.setdefault(self.guild_id, {})[self.field] = True
        self.save_fn(self.welcome)
        await interaction.response.edit_message(view=WelcomeSuccessLayout(
            title=f"{self.label} Enabled — {self.guild_name}",
            body_text=f"<a:enable:1496894249822720052> **{self.label}** has been **enabled**.",
            user=interaction.user,
            footer=f"Assister Welcomer  •  {self.label}",
        ))

    async def _on_disable(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        self.welcome.setdefault(self.guild_id, {})[self.field] = False
        self.save_fn(self.welcome)
        await interaction.response.edit_message(view=WelcomeSuccessLayout(
            title=f"{self.label} Disabled — {self.guild_name}",
            body_text=f"<a:disable:1496894585035817022> **{self.label}** has been **disabled**.",
            user=interaction.user,
            footer=f"Assister Welcomer  •  {self.label}",
        ))


class WelcomeThumbnailLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_name: str, welcome: dict, guild_id: str, save_fn):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_name = guild_name
        self.welcome    = welcome
        self.guild_id   = guild_id
        self.save_fn    = save_fn
        self._build()

    def _build(self):
        self.clear_items()
        current = self.welcome.get(self.guild_id, {}).get("thumbnail", "user").capitalize()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:welcomer:1500012556633243728> Thumbnail Mode — {self.guild_name}\n"
            f"Current mode: `{current}`"
        ))
        self.add_item(header)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **User Avatar** — Shows the joining member's avatar\n"
            f"{e_dot} **Server Icon** — Shows the server icon\n"
            f"{e_dot} **Custom URL** — Use `welcomer thumbnail custom <url>`\n"
            f"{e_dot} **None** — No thumbnail"
        ))
        self.add_item(body)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Welcomer  •  Thumbnail"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Choose thumbnail mode…",
            custom_id="wlc_thumbnail_select",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="User Avatar", value="user",   description="Joining member's avatar"),
                discord.SelectOption(label="Server Icon", value="server", description="Your server's icon"),
                discord.SelectOption(label="None",        value="none",   description="No thumbnail"),
            ]
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return
        chosen = interaction.data["values"][0]
        self.welcome.setdefault(self.guild_id, {})["thumbnail"] = chosen
        self.save_fn(self.welcome)
        await interaction.response.edit_message(view=WelcomeSuccessLayout(
            title=f"Thumbnail Updated — {self.guild_name}",
            body_text=f"{e_dot} Thumbnail mode set to `{chosen.capitalize()}`.",
            user=interaction.user,
            footer="Assister Welcomer  •  Thumbnail",
        ))


class WelcomeImageLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_name: str, welcome: dict, guild_id: str, save_fn):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_name = guild_name
        self.welcome    = welcome
        self.guild_id   = guild_id
        self.save_fn    = save_fn
        self._build()

    def _build(self):
        self.clear_items()
        current = self.welcome.get(self.guild_id, {}).get("image", "none").capitalize()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:welcomer:1500012556633243728> Image Mode — {self.guild_name}\n"
            f"Current mode: `{current}`"
        ))
        self.add_item(header)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **User Banner** — Shows the joining member's banner\n"
            f"{e_dot} **Server Banner** — Shows the server banner\n"
            f"{e_dot} **Custom URL** — Use `welcomer image custom <url>`\n"
            f"{e_dot} **None** — No image"
        ))
        self.add_item(body)
        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Welcomer  •  Image"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Choose image mode…",
            custom_id="wlc_image_select",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="User Banner",   value="userbanner",   description="Joining member's banner"),
                discord.SelectOption(label="Server Banner", value="serverbanner", description="Your server's banner"),
                discord.SelectOption(label="None",          value="none",         description="No image"),
            ]
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return
        chosen = interaction.data["values"][0]
        self.welcome.setdefault(self.guild_id, {})["image"] = chosen
        self.save_fn(self.welcome)
        await interaction.response.edit_message(view=WelcomeSuccessLayout(
            title=f"Image Updated — {self.guild_name}",
            body_text=f"{e_dot} Image mode set to `{chosen.capitalize()}`.",
            user=interaction.user,
            footer="Assister Welcomer  •  Image",
        ))





class Welcomer(commands.Cog):
    def __init__(self, bot):
        self.bot     = bot
        self.welcome = lwelcome()

    def wsettings(self, guild_id):
        gid = str(guild_id)
        if gid not in self.welcome:
            self.welcome[gid] = dict(DEFAULT_SETTINGS)
            savewelcome(self.welcome)
        else:
            changed = False
            for k, v in DEFAULT_SETTINGS.items():
                if k not in self.welcome[gid]:
                    self.welcome[gid][k] = v
                    changed = True
            if changed:
                savewelcome(self.welcome)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)

        config = self.welcome.get(guild_id)
        if not config:
            return 
        if not config.get("enabled", False):
            return
        if not config.get("channel_id"):
            return

        channel = member.guild.get_channel(int(config["channel_id"]))
        if not channel:
            return

        banner_url = None
        if config.get("image") == "userbanner":
            try:
                fetched    = await self.bot.fetch_user(member.id)
                banner_url = fetched.banner.url if fetched.banner else None
            except discord.HTTPException:
                pass

        embed   = _build_embed(config, member, banner_url)
        content = member.mention if config.get("ping", False) else None
        await channel.send(content=content, embed=embed)




    @commands.hybrid_group(name="welcomer", aliases=["wlc"], description="Welcomer configuration commands", usage="welcomer", category="Welcomer")
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _welcomer(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix   = guild_prefix(guild_id) if guild_id else '.'

            layout = ui.LayoutView(timeout=0)

            header = ui.Container()
            header.add_item(ui.TextDisplay(
                f"## <:welcomer:1500012556633243728> Welcomer Help — {ctx.guild.name}\n"
                f"```yaml\n"
                f"- [] = optional  |  <> = required\n"
                f"- Do not type brackets in commands!\n"
                f"```"
            ))
            layout.add_item(header)

            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

            body = ui.Container()
            body.add_item(ui.TextDisplay(
                f"**<:readlist:1496885036971069450> General**\n"
                f"{e_dot} `{prefix}welcomer toggle [enable|disable]` — Enable or disable welcomer\n"
                f"{e_dot} `{prefix}welcomer setchannel <#channel>` — Set the welcome channel\n"
                f"{e_dot} `{prefix}welcomer config` — View current configuration\n"
                f"{e_dot} `{prefix}welcomer test` — Preview the welcome message\n"
                f"{e_dot} `{prefix}welcomer reset` — Reset all settings\n\n"

                f"**<a:text:1500012005514281083> Message**\n"
                f"{e_dot} `{prefix}welcomer setmessage <message>` — Set welcome message\n"
                f"{e_dot} `{prefix}welcomer settitle <title|none>` — Set or remove embed title\n"
                f"{e_dot} `{prefix}welcomer setauthor <text>` — Set embed author\n"
                f"{e_dot} `{prefix}welcomer setfooter <text>` — Set embed footer\n"
                f"{e_dot} `{prefix}welcomer setcolor <#hex|reset>` — Set embed color\n\n"

                f"**<:reactping:1500012117926084638> Ping**\n"
                f"{e_dot} `{prefix}welcomer ping` — Toggle with buttons\n"
                f"{e_dot} `{prefix}welcomer ping enable` — Enable member ping\n"
                f"{e_dot} `{prefix}welcomer ping disable` — Disable member ping\n\n"

                f"**<:media:1496895701609742387> Thumbnail**\n"
                f"{e_dot} `{prefix}welcomer thumbnail` — Pick mode with dropdown\n"
                f"{e_dot} `{prefix}welcomer thumbnail user` — Use member avatar\n"
                f"{e_dot} `{prefix}welcomer thumbnail server` — Use server icon\n"
                f"{e_dot} `{prefix}welcomer thumbnail custom <url>` — Use custom URL\n"
                f"{e_dot} `{prefix}welcomer thumbnail none` — Remove thumbnail\n\n"

                f"**<:media:1496895701609742387> Image**\n"
                f"{e_dot} `{prefix}welcomer image` — Pick mode with dropdown\n"
                f"{e_dot} `{prefix}welcomer image userbanner` — Use member banner\n"
                f"{e_dot} `{prefix}welcomer image serverbanner` — Use server banner\n"
                f"{e_dot} `{prefix}welcomer image custom <url>` — Use custom URL\n"
                f"{e_dot} `{prefix}welcomer image none` — Remove image\n\n"

                f"**<:media:1263382905745440821> Variables** (usable in message, title, footer)\n"
                f"{WELCOME_VARS}"
            ))
            layout.add_item(body)

            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            layout.add_item(ui.TextDisplay(
                f"-# Requested by {ctx.author.display_name}  •  Assister Welcomer"
            ))

            await ctx.reply(view=layout, mention_author=False)




    @_welcomer.command(name="toggle", aliases=['on', 'off', 'enable', 'disable'], description="Enable or disable the welcomer", usage="welcomer toggle [enable|disable]", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(state="Enable or disable the welcomer (optional)")
    async def welcomer_toggle(self, ctx: commands.Context, state: str = None):
        self.wsettings(ctx.guild.id)
        guild_id = str(ctx.guild.id)

        if state is not None:
            state = state.lower()
            if state not in ("enable", "disable", "on", "off"):
                embed = discord.Embed(description=f"{grey} | Invalid option. Use `enable` or `disable`.", color=colour)
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)
                return
            value = state in ("enable", "on")
            self.welcome[guild_id]["enabled"] = value
            savewelcome(self.welcome)
            label = "Enabled" if value else "Disabled"
            emoji = "<a:enable:1496894249822720052>" if value else "<a:disable:1496894585035817022>"
            await ctx.reply(view=WelcomeSuccessLayout(
                title=f"Welcomer {label} — {ctx.guild.name}",
                body_text=f"{emoji} Welcomer has been **{label.lower()}**.",
                user=ctx.author,
                footer="Assister Welcomer  •  Toggle",
            ), mention_author=False)
        else:
            await ctx.reply(
                view=WelcomeToggleLayout(
                    ctx.author.id, ctx.guild.name,
                    self.welcome, guild_id, savewelcome,
                    field="enabled", label="Welcomer"
                ),
                mention_author=False
            )





    @_welcomer.command(name="setchannel", aliases=['channel', 'chnl'], description="Set the welcome channel", usage="welcomer setchannel <channel>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(channel="The channel to send welcome messages in")
    async def welcomer_setchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["channel_id"] = channel.id
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Welcome Channel Set — {ctx.guild.name}",
            body_text=f"{e_dot} **Channel:** {channel.mention}\n{e_dot} Welcome messages will now be sent there.",
            user=ctx.author,
            footer="Assister Welcomer  •  Set Channel",
        ), mention_author=False)




    @_welcomer.command(name="settitle", aliases=['title'],description="Set the embed title", usage="welcomer settitle <title|none>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(title="Supports {user}, {username}, {server}, {count} — type 'none' to remove")
    async def welcomer_settitle(self, ctx: commands.Context, *, title: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        if title.lower() == "none":
            self.wsettings(ctx.guild.id)
            self.welcome[str(ctx.guild.id)]["title"] = None
            savewelcome(self.welcome)
            await ctx.reply(view=WelcomeSuccessLayout(
                title=f"Embed Title Removed — {ctx.guild.name}",
                body_text=f"{e_dot} Embed title has been removed.",
                user=ctx.author,
                footer="Assister Welcomer  •  Set Title",
            ), mention_author=False)
            return

        if len(title) > EMBED_LIMITS["title"]:
            embed = discord.Embed(description=f"{grey} | Title is too long. Maximum is **{EMBED_LIMITS['title']} characters** (yours: `{len(title)}`).", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["title"] = title
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Embed Title Updated — {ctx.guild.name}",
            body_text=f"{e_dot} **New Title:** {title}",
            user=ctx.author,
            footer="Assister Welcomer  •  Set Title",
        ), mention_author=False)


    @_welcomer.command(name="setmessage",aliases=['message', 'msg'], description="Set a custom welcome message", usage="welcomer setmessage <message>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(message="Supports {user}, {username}, {server}, {count}")
    async def welcomer_setmessage(self, ctx: commands.Context, *, message: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        if len(message) > EMBED_LIMITS["message"]:
            embed = discord.Embed(description=f"{grey} | Message is too long. Maximum is **{EMBED_LIMITS['message']} characters** (yours: `{len(message)}`).", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["message"] = message
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Welcome Message Updated — {ctx.guild.name}",
            body_text=f"{e_dot} **New Message:**\n> {message}\n\n**Available variables:**\n{WELCOME_VARS}",
            user=ctx.author,
            footer="Assister Welcomer  •  Set Message",
        ), mention_author=False)


    @_welcomer.command(name="setfooter",aliases=['footer'], description="Set the embed footer text", usage="welcomer setfooter <text>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(text="Supports {user}, {username}, {server}, {count}")
    async def welcomer_setfooter(self, ctx: commands.Context, *, text: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        if len(text) > EMBED_LIMITS["footer"]:
            embed = discord.Embed(description=f"{grey} | Footer is too long. Maximum is **{EMBED_LIMITS['footer']} characters** (yours: `{len(text)}`).", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["footer"] = text
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Embed Footer Updated — {ctx.guild.name}",
            body_text=f"{e_dot} **New Footer:** {text}",
            user=ctx.author,
            footer="Assister Welcomer  •  Set Footer",
        ), mention_author=False)


    @_welcomer.command(name="setauthor",aliases=['author'], description="Set the embed author text", usage="welcomer setauthor <text>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(text="Supports {user}, {username}, {server}, {count}")
    async def welcomer_setauthor(self, ctx: commands.Context, *, text: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        if len(text) > EMBED_LIMITS["author"]:
            embed = discord.Embed(description=f"{grey} | Author text is too long. Maximum is **{EMBED_LIMITS['author']} characters** (yours: `{len(text)}`).", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["author"] = text
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Embed Author Updated — {ctx.guild.name}",
            body_text=(
                f"{e_dot} **Author text:** {text}\n"
                f"{e_dot} Servericon will be used as the author icon."
            ),
            user=ctx.author,
            footer="Assister Welcomer  •  Set Author",
        ), mention_author=False)





    @_welcomer.command(name="setcolor", aliases=['color', 'colour'], description="Set the embed color", usage="welcomer setcolor <hex>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(hex_color="Hex color code e.g. #ff5733 or 'reset' to use default")
    async def welcomer_setcolor(self, ctx: commands.Context, hex_color: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.wsettings(ctx.guild.id)

        if hex_color.lower() == "reset":
            self.welcome[str(ctx.guild.id)]["color"] = None
            savewelcome(self.welcome)
            await ctx.reply(view=WelcomeSuccessLayout(
                title=f"Embed Color Reset — {ctx.guild.name}",
                body_text=f"{e_dot} Embed color has been reset to default.",
                user=ctx.author,
                footer="Assister Welcomer  •  Set Color",
            ), mention_author=False)
            return

        cleaned = hex_color.strip("#")
        if len(cleaned) != 6:
            embed = discord.Embed(description=f"{grey} | Invalid hex color. Example: `#ff5733` or `ff5733`.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        try:
            int(cleaned, 16)
        except ValueError:
            embed = discord.Embed(description=f"{grey} | Invalid hex color. Example: `#ff5733`.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        self.welcome[str(ctx.guild.id)]["color"] = cleaned
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Embed Color Updated — {ctx.guild.name}",
            body_text=f"{e_dot} **New Color:** `#{cleaned}`",
            user=ctx.author,
            footer="Assister Welcomer  •  Set Color",
        ), mention_author=False)





    @_welcomer.group(name="ping", description="Toggle pinging the new member", usage="welcomer ping [enable|disable]", category="Welcomer", invoke_without_command=True)
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_ping(self, ctx: commands.Context, state: str = None):
        self.wsettings(ctx.guild.id)
        guild_id = str(ctx.guild.id)

        if state is not None:
            state = state.lower()
            if state not in ("enable", "disable", "on", "off"):
                embed = discord.Embed(description=f"{grey} | Invalid option. Use `enable` or `disable`.", color=colour)
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)
                return
            value = state in ("enable", "on")
            self.welcome[guild_id]["ping"] = value
            savewelcome(self.welcome)
            label = "Enabled" if value else "Disabled"
            emoji = "<a:enable:1496894249822720052>" if value else "<a:disable:1496894585035817022>"
            await ctx.reply(view=WelcomeSuccessLayout(
                title=f"Ping {label} — {ctx.guild.name}",
                body_text=f"{emoji} New member ping has been **{label.lower()}**.",
                user=ctx.author,
                footer="Assister Welcomer  •  Ping",
            ), mention_author=False)
        else:
            await ctx.reply(
                view=WelcomeToggleLayout(
                    ctx.author.id, ctx.guild.name,
                    self.welcome, guild_id, savewelcome,
                    field="ping", label="Member Ping"
                ),
                mention_author=False
            )

    @welcomer_ping.command(name="enable", description="Enable pinging new members", usage="welcomer ping enable", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_ping_enable(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["ping"] = True
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Ping Enabled — {ctx.guild.name}",
            body_text=f"<a:enable:1496894249822720052> New member ping has been **enabled**.",
            user=ctx.author,
            footer="Assister Welcomer  •  Ping",
        ), mention_author=False)

    @welcomer_ping.command(name="disable", description="Disable pinging new members", usage="welcomer ping disable", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_ping_disable(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["ping"] = False
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Ping Disabled — {ctx.guild.name}",
            body_text=f"<a:disable:1496894585035817022> New member ping has been **disabled**.",
            user=ctx.author,
            footer="Assister Welcomer  •  Ping",
        ), mention_author=False)





    @_welcomer.group(name="thumbnail",aliases=['thumb'], description="Set embed thumbnail mode", usage="welcomer thumbnail", category="Welcomer", invoke_without_command=True)
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_thumbnail(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        await ctx.reply(
            view=WelcomeThumbnailLayout(
                ctx.author.id, ctx.guild.name,
                self.welcome, str(ctx.guild.id), savewelcome
            ),
            mention_author=False
        )

    @welcomer_thumbnail.command(name="user", description="Use member avatar as thumbnail", usage="welcomer thumbnail user", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_thumbnail_user(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["thumbnail"] = "user"
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Thumbnail Updated — {ctx.guild.name}",
            body_text=f"{e_dot} Thumbnail set to **User Avatar**.",
            user=ctx.author, footer="Assister Welcomer  •  Thumbnail",
        ), mention_author=False)

    @welcomer_thumbnail.command(name="server", description="Use server icon as thumbnail", usage="welcomer thumbnail server", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_thumbnail_server(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["thumbnail"] = "server"
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Thumbnail Updated — {ctx.guild.name}",
            body_text=f"{e_dot} Thumbnail set to **Server Icon**.",
            user=ctx.author, footer="Assister Welcomer  •  Thumbnail",
        ), mention_author=False)

    @welcomer_thumbnail.command(name="custom", description="Use a custom URL as thumbnail", usage="welcomer thumbnail custom <url>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(url="Direct image URL to use as thumbnail")
    async def welcomer_thumbnail_custom(self, ctx: commands.Context, *, url: str):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["thumbnail"]     = "custom"
        self.welcome[str(ctx.guild.id)]["thumbnail_url"] = url
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Thumbnail Updated — {ctx.guild.name}",
            body_text=f"{e_dot} Thumbnail set to **Custom URL**.",
            user=ctx.author, footer="Assister Welcomer  •  Thumbnail",
        ), mention_author=False)

    @welcomer_thumbnail.command(name="none", description="Remove the thumbnail", usage="welcomer thumbnail none", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_thumbnail_none(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["thumbnail"] = "none"
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Thumbnail Removed — {ctx.guild.name}",
            body_text=f"{e_dot} Thumbnail has been **removed**.",
            user=ctx.author, footer="Assister Welcomer  •  Thumbnail",
        ), mention_author=False)





    @_welcomer.group(name="image",aliases=['img'], description="Set embed image mode", usage="welcomer image", category="Welcomer", invoke_without_command=True)
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_image(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        await ctx.reply(
            view=WelcomeImageLayout(
                ctx.author.id, ctx.guild.name,
                self.welcome, str(ctx.guild.id), savewelcome
            ),
            mention_author=False
        )

    @welcomer_image.command(name="userbanner", description="Use the member's banner as image", usage="welcomer image userbanner", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_image_userbanner(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["image"] = "userbanner"
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Image Updated — {ctx.guild.name}",
            body_text=f"{e_dot} Image set to **User Banner**.",
            user=ctx.author, footer="Assister Welcomer  •  Image",
        ), mention_author=False)

    @welcomer_image.command(name="serverbanner", description="Use the server banner as image", usage="welcomer image serverbanner", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_image_serverbanner(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["image"] = "serverbanner"
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Image Updated — {ctx.guild.name}",
            body_text=f"{e_dot} Image set to **Server Banner**.",
            user=ctx.author, footer="Assister Welcomer  •  Image",
        ), mention_author=False)

    @welcomer_image.command(name="custom", description="Use a custom URL as image", usage="welcomer image custom <url>", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(url="Direct image URL to use as the embed image")
    async def welcomer_image_custom(self, ctx: commands.Context, *, url: str):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["image"]     = "custom"
        self.welcome[str(ctx.guild.id)]["image_url"] = url
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Image Updated — {ctx.guild.name}",
            body_text=f"{e_dot} Image set to **Custom URL**.",
            user=ctx.author, footer="Assister Welcomer  •  Image",
        ), mention_author=False)

    @welcomer_image.command(name="none", description="Remove the embed image", usage="welcomer image none", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_image_none(self, ctx: commands.Context):
        self.wsettings(ctx.guild.id)
        self.welcome[str(ctx.guild.id)]["image"] = "none"
        savewelcome(self.welcome)
        await ctx.reply(view=WelcomeSuccessLayout(
            title=f"Image Removed — {ctx.guild.name}",
            body_text=f"{e_dot} Embed image has been **removed**.",
            user=ctx.author, footer="Assister Welcomer  •  Image",
        ), mention_author=False)





    @_welcomer.command(name="config", aliases=["show", "setup"], description="Show the current welcomer configuration", usage="welcomer config", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_config(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.wsettings(ctx.guild.id)

        config     = self.welcome[str(ctx.guild.id)]
        enabled    = "<a:enable:1496894249822720052> Enabled"   if config.get("enabled") else "<a:disable:1496894585035817022> Disabled"
        ping       = "<a:enable:1496894249822720052> On"        if config.get("ping")    else "<a:disable:1496894585035817022> Off"
        channel_id = config.get("channel_id")
        channel    = f"<#{channel_id}>" if channel_id else "`Not set`"
        thumbnail  = f"`{config.get('thumbnail', 'user').capitalize()}`"
        image      = f"`{config.get('image', 'none').capitalize()}`"
        color      = f"`#{config.get('color')}`" if config.get("color") else "`Default`"
        message    = config.get("message",  DEFAULT_MESSAGE)
        title      = config.get("title", DEFAULT_TITLE) or "`Not set`"
        footer_txt = config.get("footer",   DEFAULT_FOOTER)
        author     = config.get("author", DEFAULT_AUTHOR)

        layout = ui.LayoutView(timeout=0)
        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## <:welcomer:1500012556633243728> Welcomer Config — {ctx.guild.name}"))
        layout.add_item(header)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Status:** {enabled}\n"
            f"{e_dot} **Channel:** {channel}\n"
            f"{e_dot} **Ping:** {ping}\n"
            f"{e_dot} **Thumbnail:** {thumbnail}\n"
            f"{e_dot} **Image:** {image}\n"
            f"{e_dot} **Color:** {color}\n\n"
            f"**Title:**\n {title}\n\n"
            f"**Message:**\n {message}\n\n"
            f"**Footer:**\n {footer_txt}\n\n"
            f"**Author:**\n {author}\n\n"
            f"**Variables:**\n{WELCOME_VARS}"
        ))
        layout.add_item(body)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(f"-# Requested by {ctx.author.display_name}  •  Assister Welcomer"))
        await ctx.reply(view=layout, mention_author=False)





    @_welcomer.command(name="test", description="Preview the welcome message", usage="welcomer test", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_test(self, ctx: commands.Context):
        try:
            if ctx.interaction:
                await ctx.defer()
            else:
                await ctx.typing()
        except Exception:
            pass

        self.wsettings(ctx.guild.id)
        config = self.welcome[str(ctx.guild.id)]

        banner_url = None
        if config.get("image") == "userbanner":
            try:
                fetched    = await self.bot.fetch_user(ctx.author.id)
                banner_url = fetched.banner.url if fetched.banner else None
            except discord.HTTPException:
                pass

        embed   = _build_embed(config, ctx.author, banner_url)
        content = ctx.author.mention if config.get("ping", False) else None

        notice = discord.Embed(
            description=f"{e_dot} This is a **preview** of your welcome message.",
            color=colour
        )
        notice.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=notice, mention_author=False)
        await ctx.send(content=content, embed=embed)





    @_welcomer.command(name="reset", description="Reset all welcomer settings", usage="welcomer reset", category="Welcomer")
    
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def welcomer_reset(self, ctx: commands.Context):
        async def on_confirm(interaction: discord.Interaction):
            self.welcome[str(ctx.guild.id)] = dict(DEFAULT_SETTINGS)
            savewelcome(self.welcome)
            result = ui.LayoutView(timeout=0)
            h = ui.Container()
            h.add_item(ui.TextDisplay(f"## {tick} Welcomer Reset — {ctx.guild.name}"))
            result.add_item(h)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            b = ui.Container()
            b.add_item(ui.TextDisplay(f"{e_dot} All welcomer settings have been reset to default."))
            result.add_item(b)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            result.add_item(ui.TextDisplay(f"-# Updated by {interaction.user.display_name}  •  Assister Welcomer"))
            await interaction.response.edit_message(view=result)

        await ctx.reply(view=WelcomeConfirmLayout(
            author_id=ctx.author.id,
            title="Reset Welcomer Settings",
            body_text=(
                f"Are you sure you want to reset **all welcomer settings** for **{ctx.guild.name}**?\n\n"
                f"❗ **This action cannot be undone.**"
            ),
            on_confirm=on_confirm,
        ), mention_author=False)




async def setup(bot):
    await bot.add_cog(Welcomer(bot))