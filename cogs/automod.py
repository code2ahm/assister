import discord
from discord import ui
from discord.ext import commands
from discord import app_commands
import asyncio
from utils.paginator import Ahm
from discord.ui import Button, View
from utils.loads import *
from utils.variables import *
from utils.checks import *
from utils.prefixes import *
from datetime import timezone, timedelta






ALL_AM_EVENTS = [
    ('Anti Link',    'antilink'),
    ('Anti Spam',    'antispam'),
    ('Anti Invites', 'antiinvites'),
    ('Anti Swear',   'antiswear'),
]



def _am_event_options():
    return [discord.SelectOption(label=l, value=v) for l, v in ALL_AM_EVENTS]



def _fmt_am_events(events: list, enabled=True) -> str:
    emoji = "<a:enable:1496894249822720052>" if enabled else "<a:disable:1496894585035817022>"
    label_map = {v: l for l, v in ALL_AM_EVENTS}
    return '\n'.join(f"{emoji} {label_map.get(e, e.title())}" for e in events)





class AmConfirmLayout(ui.LayoutView):
    def __init__(self, author_id: int, title: str, body_text: str, on_confirm, on_cancel=None):
        super().__init__(timeout=60)
        self.author_id   = author_id
        self._confirm_cb = on_confirm
        self._cancel_cb  = on_cancel
        self._build(title, body_text)

    def _build(self, title: str, body_text: str):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## <:bionic_g_caution:1261557581319508068> {title}"))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(body_text))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Automod  •  Confirm action"))

        btn_row = ui.ActionRow()
        yes = ui.Button(label="Confirm", style=discord.ButtonStyle.success, custom_id="am_confirm_yes")
        no  = ui.Button(label="Cancel",  style=discord.ButtonStyle.danger,  custom_id="am_confirm_no")
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






class AmSuccessLayout(ui.LayoutView):
    def __init__(self, title: str, events_text: str, punishment: str | None,
                 user: discord.abc.User, footer: str):
        super().__init__(timeout=0)
        self._build(title, events_text, punishment, user, footer)

    def _build(self, title, events_text, punishment, user, footer):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {title}"))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(events_text))
        self.add_item(body)

        if punishment:
            self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            pun_container = ui.Container()
            pun_container.add_item(ui.TextDisplay(
                f"<:bionic_g_ban:1261572949572321353> **Default Punishment:** `{punishment}`"
            ))
            self.add_item(pun_container)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay(
            f"-# Updated by {user.display_name}  •  {footer}"
        ))







class AmEnableLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_name: str, automod: dict, save_fn):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_name = guild_name
        self.automod    = automod
        self.save_fn    = save_fn
        self._build()

    def _build(self):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <a:enable:1496894249822720052> Enable Automod Events\n"
            f"Select individual events from the dropdown, or hit **Enable All** to activate everything at once."
        ))
        self.add_item(header)

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Server:** `{self.guild_name}`\n"
            f"{e_dot} Default punishment on enable: `Mute`"
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Automod  •  Enable"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Select events to enable…",
            custom_id="automod_enable_select",
            min_values=1,
            max_values=len(ALL_AM_EVENTS),
            options=_am_event_options(),
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

        btn_row = ui.ActionRow()
        btn = ui.Button(label="Enable All Events", style=discord.ButtonStyle.success,
                        custom_id="am_enable_all_btn")
        btn.callback = self._on_enable_all
        btn_row.add_item(btn)
        self.add_item(btn_row)

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        selected = interaction.data["values"]
        guild_id = str(interaction.guild.id)
        for event in selected:
            self.automod[guild_id][event]["enabled"] = True
        self.save_fn(self.automod)
        await interaction.response.edit_message(view=AmSuccessLayout(
            title=f"{antiemoji} Automod Enabled — {interaction.guild.name}",
            events_text=_fmt_am_events(selected, enabled=True),
            punishment="Mute (existing setting preserved)",
            user=interaction.user,
            footer="Assister Automod  •  Enable",
        ))

    async def _on_enable_all(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        guild_id = str(interaction.guild.id)
        all_vals = [v for _, v in ALL_AM_EVENTS]
        for event in all_vals:
            self.automod[guild_id][event]["enabled"] = True
        self.save_fn(self.automod)
        await interaction.response.edit_message(view=AmSuccessLayout(
            title=f"{antiemoji} All Events Enabled — {interaction.guild.name}",
            events_text=_fmt_am_events(all_vals, enabled=True),
            punishment="Mute (existing setting preserved)",
            user=interaction.user,
            footer="Assister Automod  •  Enable All",
        ))






class AmDisableLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_name: str, automod: dict, save_fn):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_name = guild_name
        self.automod    = automod
        self.save_fn    = save_fn
        self._build()

    def _build(self):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <a:disable:1496894585035817022> Disable Automod Events\n"
            f"Select individual events from the dropdown, or hit **Disable All** to turn everything off."
        ))
        self.add_item(header)

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Server:** `{self.guild_name}`\n"
            f"{e_dot} Choose which automod protections to deactivate."
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Automod  •  Disable"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Select events to disable…",
            custom_id="automod_disable_select",
            min_values=1,
            max_values=len(ALL_AM_EVENTS),
            options=_am_event_options(),
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

        btn_row = ui.ActionRow()
        btn = ui.Button(label="Disable All Events", style=discord.ButtonStyle.danger,
                        custom_id="am_disable_all_btn")
        btn.callback = self._on_disable_all
        btn_row.add_item(btn)
        self.add_item(btn_row)

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        selected = interaction.data["values"]
        guild_id = str(interaction.guild.id)
        for event in selected:
            self.automod[guild_id][event]["enabled"] = False
        self.save_fn(self.automod)
        await interaction.response.edit_message(view=AmSuccessLayout(
            title=f"{antiemoji} Events Disabled — {interaction.guild.name}",
            events_text=_fmt_am_events(selected, enabled=False),
            punishment=None,
            user=interaction.user,
            footer="Assister Automod  •  Disable",
        ))

    async def _on_disable_all(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        guild_id = str(interaction.guild.id)
        all_vals = [v for _, v in ALL_AM_EVENTS]
        for event in all_vals:
            self.automod[guild_id][event]["enabled"] = False
        self.save_fn(self.automod)
        await interaction.response.edit_message(view=AmSuccessLayout(
            title=f"{antiemoji} All Events Disabled — {interaction.guild.name}",
            events_text=_fmt_am_events(all_vals, enabled=False),
            punishment=None,
            user=interaction.user,
            footer="Assister Automod  •  Disable All",
        ))







class AmWhitelistLayout(ui.LayoutView):
    def __init__(self, author_id: int, member: discord.Member, automod: dict, save_fn):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.member    = member
        self.automod   = automod
        self.save_fn   = save_fn
        self._build()

    def _build(self):
        self.clear_items()
        guild_id    = str(self.member.guild.id)
        wl_events   = [
            e for e in [v for _, v in ALL_AM_EVENTS]
            if self.member.id in self.automod.get(guild_id, {}).get(e, {}).get("whitelist", [])
        ]

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:fn_verify:1497547412820983938> Automod Whitelist — {self.member.display_name}\n"
            f"Select which automod events to toggle for this member."
        ))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        current_status = (
            _fmt_am_events(wl_events, enabled=True)
            if wl_events
            else f"{grey} Not whitelisted from any events."
        )
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Member:** {self.member.mention}\n"
            f"{e_dot} **User ID:** `{self.member.id}`\n\n"
            f"**Currently whitelisted from:**\n{current_status}"
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Automod  •  Whitelist"))

        add_row = ui.ActionRow()
        add_sel = ui.Select(
            placeholder="Add to whitelist for events",
            custom_id="automod_wl_add_select",
            min_values=1,
            max_values=len(ALL_AM_EVENTS),
            options=_am_event_options(),
        )
        add_sel.callback = self._on_add
        add_row.add_item(add_sel)
        self.add_item(add_row)

        remove_row = ui.ActionRow()
        remove_sel = ui.Select(
            placeholder="Remove from whitelist for events",
            custom_id="automod_wl_remove_select",
            min_values=1,
            max_values=len(ALL_AM_EVENTS),
            options=_am_event_options(),
        )
        remove_sel.callback = self._on_remove
        remove_row.add_item(remove_sel)
        self.add_item(remove_row)

        btn_row = ui.ActionRow()
        add_all    = ui.Button(label="Whitelist All",   style=discord.ButtonStyle.success, custom_id="am_wl_add_all")
        remove_all = ui.Button(label="Remove All",      style=discord.ButtonStyle.danger,  custom_id="am_wl_remove_all")
        add_all.callback    = self._on_add_all
        remove_all.callback = self._on_remove_all
        btn_row.add_item(add_all)
        btn_row.add_item(remove_all)
        self.add_item(btn_row)

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return False
        return True

    async def _on_add(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        selected = interaction.data["values"]
        guild_id = str(interaction.guild.id)
        for event in selected:
            wl = self.automod[guild_id][event]["whitelist"]
            if self.member.id not in wl:
                wl.append(self.member.id)
        self.save_fn(self.automod)
        await self._respond_success(interaction, selected, added=True)

    async def _on_remove(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        selected = interaction.data["values"]
        guild_id = str(interaction.guild.id)
        for event in selected:
            wl = self.automod[guild_id][event]["whitelist"]
            if self.member.id in wl:
                wl.remove(self.member.id)
        self.save_fn(self.automod)
        await self._respond_success(interaction, selected, added=False)

    async def _on_add_all(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        guild_id = str(interaction.guild.id)
        all_vals = [v for _, v in ALL_AM_EVENTS]
        for event in all_vals:
            wl = self.automod[guild_id][event]["whitelist"]
            if self.member.id not in wl:
                wl.append(self.member.id)
        self.save_fn(self.automod)
        await self._respond_success(interaction, all_vals, added=True)

    async def _on_remove_all(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        guild_id = str(interaction.guild.id)
        all_vals = [v for _, v in ALL_AM_EVENTS]
        for event in all_vals:
            wl = self.automod[guild_id][event]["whitelist"]
            if self.member.id in wl:
                wl.remove(self.member.id)
        self.save_fn(self.automod)
        await self._respond_success(interaction, all_vals, added=False)

    async def _respond_success(self, interaction: discord.Interaction, events: list, added: bool):
        action_word = "added to" if added else "removed from"
        result = ui.LayoutView(timeout=0)

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {antiemoji} Whitelist Updated — {self.member.display_name}"))
        result.add_item(header)

        result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Member:** {self.member.mention}\n"
            f"{e_dot} **User ID:** `{self.member.id}`\n\n"
            f"**{action_word.capitalize()} whitelist:**\n{_fmt_am_events(events, enabled=added)}"
        ))
        result.add_item(body)

        result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        result.add_item(ui.TextDisplay(
            f"-# Updated by {interaction.user.display_name}  •  Assister Automod"
        ))

        await interaction.response.edit_message(view=result)







class AmPunishmentLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_id: str, guild_name: str, automod: dict, save_fn):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_id   = guild_id
        self.guild_name = guild_name
        self.automod    = automod
        self.save_fn    = save_fn
        self._build()

    def _build(self):
        self.clear_items()

        lines = []
        for _, v in ALL_AM_EVENTS:
            pun = self.automod.get(self.guild_id, {}).get(v, {}).get("punishment", "mute").capitalize()
            lines.append(f"{e_dot} **{v.replace('anti', 'Anti ').title()}:** `{pun}`")

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:punish:1499307086461538457> Automod Punishment\n"
            f"Choose a punishment to apply to **all** automod events at once."
        ))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        warn = ui.Container()
        warn.add_item(ui.TextDisplay(
            f"<:bionic_g_caution:1261557581319508068> **Warning:** This will overwrite the punishment for **every** automod event.\n\n"
            f"**Current punishments:**\n" + "\n".join(lines) + "\n\n"
            f"<:kick:1499307114185625691> **Kick** — Remove the user from the server\n"
            f"<:bionic_g_ban:1261572949572321353> **Ban** — Permanently ban the member\n"
            f"<:punishment:1499307386823901287> **Mute** — Timeout the member for 10 minutes"
        ))
        self.add_item(warn)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay("-# Assister Automod  •  Punishment"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Choose a punishment for all events…",
            custom_id="automod_punishment_select",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Kick",
                    value="kick",
                    description="Kick the offending member from the server",
                    emoji="<:kick:1499307114185625691>"
                ),
                discord.SelectOption(
                    label="Ban",
                    value="ban",
                    description="Permanently ban the offending member",
                    emoji="<:bionic_g_ban:1261572949572321353>"
                ),
                discord.SelectOption(
                    label="Mute",
                    value="mute",
                    description="Timeout the offending member for 10 minutes",
                    emoji="<:punishment:1499307386823901287>"
                ),
            ],
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return

        chosen   = interaction.data["values"][0]
        all_vals = [v for _, v in ALL_AM_EVENTS]
        for event in all_vals:
            self.automod[self.guild_id][event]["punishment"] = chosen
        self.save_fn(self.automod)

        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {tick} Punishment Updated — {self.guild_name}"))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"<:bionic_g_ban:1261572949572321353> **Punishment set to `{chosen.capitalize()}`** for all events:\n\n"
            + "\n".join(f"<a:enable:1496894249822720052> {v.replace('anti', 'Anti ').title()}" for v in all_vals)
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay(
            f"-# Updated by {interaction.user.display_name}  •  Assister Automod"
        ))

        await interaction.response.edit_message(view=self)






class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automod = lautomod()
        self.antiswear = lantiswear()

    def amsettings(self, guild_id):
        if str(guild_id) not in self.automod:
            self.automod[str(guild_id)] = {
                "antilink":    {"enabled": False, "punishment": "mute", "whitelist": []},
                "antispam":    {"enabled": False, "punishment": "mute", "whitelist": []},
                "antiinvites": {"enabled": False, "punishment": "mute", "whitelist": []},
                "antiswear":   {"enabled": False, "punishment": "mute", "whitelist": []}
            }
            saveauto(self.automod)




    async def amviolate(self, message):
        if message.guild is None:
            return
        guild_id = str(message.guild.id)
        self.amsettings(message.guild.id)

        member = message.guild.get_member(message.author.id)
        if member is None:
            return

        cfg = self.automod.get(guild_id, {})

        if cfg.get("antiswear", {}).get("enabled") and \
        message.author.id not in cfg["antiswear"].get("whitelist", []) and \
        await self.checkswear(message, guild_id):
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await self.applypunish(member, cfg["antiswear"]["punishment"], message.channel, "Using Swear Words")
                await message.delete()
                await message.channel.send(f"{message.author.mention} **watch your language**", delete_after=7)

        if cfg.get("antilink", {}).get("enabled") and \
        message.author.id not in cfg["antilink"].get("whitelist", []) and \
        ('https://' in message.content or 'http://' in message.content):
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await self.applypunish(member, cfg["antilink"]["punishment"], message.channel, "Posting Links")
                await message.delete()

        elif cfg.get("antispam", {}).get("enabled") and \
            message.author.id not in cfg["antispam"].get("whitelist", []) and \
            await self.checkspam(message):
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await self.applypunish(member, cfg["antispam"]["punishment"], message.channel, "Spamming")
                await message.delete()

        elif cfg.get("antiinvites", {}).get("enabled") and \
            message.author.id not in cfg["antiinvites"].get("whitelist", []) and \
            ('discord.gg/' in message.content or 'discord.com/invite/' in message.content):
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await self.applypunish(member, cfg["antiinvites"]["punishment"], message.channel, "Posting Invites")
                await message.delete()


    async def checkspam(self, message):
        guild_id  = str(message.guild.id)
        author_id = str(message.author.id)
        now       = datetime.now(timezone.utc)
        winsize   = timedelta(seconds=2)

        if guild_id not in msgs:
            msgs[guild_id] = {}
        if author_id not in msgs[guild_id]:
            msgs[guild_id][author_id] = []

        msgs[guild_id][author_id].append(now)
        msgs[guild_id][author_id] = [
            t for t in msgs[guild_id][author_id]
            if (now - t) <= winsize
        ]

        if not msgs[guild_id][author_id]:
            del msgs[guild_id][author_id]
        if not msgs[guild_id]:
            del msgs[guild_id]

        return len(msgs.get(guild_id, {}).get(author_id, [])) > 3


    async def checkswear(self, message, guild_id):
        blocked = self.antiswear.get(guild_id, [])
        mysage  = message.content.lower().split()
        return any(word in blocked for word in mysage)


    async def applypunish(self, member: discord.Member, punishment, channel, reason=None):
        guild = member.guild
        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully punished {member.mention}",
            color=colour
        )
        embed.add_field(name="Description:", value=f"{e_dot} **Punishment:** `{punishment}`\n{e_dot} **Reason:** {reason}", inline=False)
        embed.set_author(name=f"{self.bot.user.name} Automod", icon_url=self.bot.user.avatar.url)

        try:
            if punishment == 'mute' and guild.me.guild_permissions.mute_members:
                await member.timeout(timedelta(seconds=600), reason=f"Automod Violation: {reason}")
            elif punishment == 'kick' and guild.me.guild_permissions.kick_members:
                await member.kick(reason=f"Automod Violation: {reason}")
            elif punishment == 'ban' and guild.me.guild_permissions.ban_members:
                await member.ban(reason=f"Automod Violation: {reason}")
        except discord.errors.Forbidden:
            return

        await channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        if message.author.bot:
            return
        await self.amviolate(message)





    @commands.hybrid_group(aliases=['am'], name="automod", description="Automod configuration commands", usage="automod", category="Automod")
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _automod(self, ctx: commands.Context):
        ahm7 = self.bot.get_command('help')
        if ahm7:
            await ctx.invoke(ahm7, query='automod')




    @_automod.command(name="enable", description="Enable automod events interactively", usage="automod enable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def automod_enable(self, ctx: commands.Context):
        self.amsettings(ctx.guild.id)
        await ctx.reply(
            view=AmEnableLayout(ctx.author.id, ctx.guild.name, self.automod, saveauto),
            mention_author=False
        )


    @_automod.command(name="disable", description="Disable automod events interactively", usage="automod disable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def automod_disable(self, ctx: commands.Context):
        self.amsettings(ctx.guild.id)
        await ctx.reply(
            view=AmDisableLayout(ctx.author.id, ctx.guild.name, self.automod, saveauto),
            mention_author=False
        )



    @_automod.command(aliases=['show', 'setup'], name="config", description="Show the current automod configuration", usage="automod config", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def automod_config(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)

        config = self.automod[str(ctx.guild.id)]
        layout = ui.LayoutView(timeout=0)

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {antiemoji} Automod Config — {ctx.guild.name}"))
        layout.add_item(header)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        lines = []
        for event, settings in config.items():
            status = "<a:enable:1496894249822720052> Enabled" if settings["enabled"] else "<a:disable:1496894585035817022> Disabled"
            pun    = settings["punishment"].capitalize()
            lines.append(f"**{event.replace('anti','Anti ').title()}** — {status}\n{e_dot} Punishment: `{pun}`")

        body = ui.Container()
        body.add_item(ui.TextDisplay("\n\n".join(lines)))
        layout.add_item(body)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Requested by {ctx.author.display_name}  •  Assister Automod"
        ))

        await ctx.reply(view=layout, mention_author=False)




    @_automod.command(aliases=['punish'], name="punishment", description="Set punishment for all automod events at once", usage="automod punishment", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def automod_punishment(self, ctx: commands.Context):
        self.amsettings(ctx.guild.id)
        guild_id = str(ctx.guild.id)
        await ctx.reply(
            view=AmPunishmentLayout(ctx.author.id, guild_id, ctx.guild.name, self.automod, saveauto),
            mention_author=False
        )




    @_automod.group(aliases=['wl'], name="whitelist", invoke_without_command=True, usage="automod whitelist", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(member="Select the member you want to manage in the automod whitelist.")
    async def automod_whitelist(self, ctx: commands.Context, member: discord.Member = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        self.amsettings(ctx.guild.id)

        if member is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix   = guild_prefix(guild_id) if guild_id else '.'

            layout = ui.LayoutView(timeout=0)
            header = ui.Container()
            header.add_item(ui.TextDisplay(
                f"## <:fn_verify:1497547412820983938> Automod Whitelist\n"
                f"```py\n"
                f"- [] = optional  |  <> = required\n"
                f"- Do not type brackets in commands!\n"
                f"```"
            ))
            layout.add_item(header)

            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

            body = ui.Container()
            body.add_item(ui.TextDisplay(
                f"**Toggle whitelist for a member:**\n`{prefix}automod whitelist <member>`\n\n"
                f"**View whitelisted members:**\n`{prefix}automod whitelist show`\n\n"
                f"**Reset all whitelisted members:**\n`{prefix}automod whitelist reset`"
            ))
            layout.add_item(body)

            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            layout.add_item(ui.TextDisplay(
                f"-# Requested by {ctx.author.display_name}  •  Assister Automod"
            ))
            await ctx.reply(view=layout, mention_author=False)
        else:
            await ctx.reply(
                view=AmWhitelistLayout(ctx.author.id, member, self.automod, saveauto),
                mention_author=False
            )

    async def addwl(self, ctx: commands.Context, member: discord.Member):
        guild_id = str(ctx.guild.id)
        self.amsettings(ctx.guild.id)
        for event in ["antilink", "antispam", "antiinvites", "antiswear"]:
            if member.id not in self.automod[guild_id][event]["whitelist"]:
                self.automod[guild_id][event]["whitelist"].append(member.id)
        saveauto(self.automod)

    async def removewl(self, ctx: commands.Context, member: discord.Member):
        guild_id = str(ctx.guild.id)
        self.amsettings(ctx.guild.id)
        for event in ["antilink", "antispam", "antiinvites", "antiswear"]:
            if member.id in self.automod[guild_id][event]["whitelist"]:
                self.automod[guild_id][event]["whitelist"].remove(member.id)
        saveauto(self.automod)


    @automod_whitelist.command(aliases=['list'], name="show", description="Show the whitelisted users for each automod event", usage="automod whitelist show", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def automod_whitelist_show(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        config = self.automod[str(ctx.guild.id)]

        evwl = {}
        for event, settings in config.items():
            if settings["whitelist"]:
                memwl = [f"`{index + 1}.` <@{user_id}>  [[{user_id}](https://discord.com/users/{user_id})]" for index, user_id in enumerate(settings["whitelist"])]
                evwl[event] = memwl
            else:
                evwl[event] = [" No users whitelisted."]

        wlpages = []
        cpage   = ""

        for event, users in evwl.items():
            cpage += f"{e_dot} **{event.capitalize()} Whitelist:**\n"
            for user in users:
                cpage += f"{user}\n"
            cpage += "\n"
            if cpage.count("\n") > 10:
                wlpages.append(cpage.strip())
                cpage = ""

        if cpage:
            wlpages.append(cpage.strip())

        epages = []
        for page in wlpages:
            embed = discord.Embed(title="", description=page, color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text="Assister automod config • Page {}/{}".format(wlpages.index(page) + 1, len(wlpages)), icon_url=ctx.bot.user.avatar)
            epages.append(embed)

        paginator = Ahm(pages=epages)
        await paginator.start(ctx)

    @automod_whitelist.error
    async def automod_whitelist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                description=f"{grey} | Member not found. Please mention a valid member.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        elif isinstance(error, commands.MissingRequiredArgument):
            pass

    @automod_whitelist.command(name="reset", description="Reset the whitelist for all events", usage="automod whitelist reset", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def automod_whitelist_reset(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        async def on_confirm(interaction: discord.Interaction):
            self.amsettings(ctx.guild.id)
            for event in self.automod[str(ctx.guild.id)]:
                self.automod[str(ctx.guild.id)][event]["whitelist"] = []
            saveauto(self.automod)

            result = ui.LayoutView(timeout=0)
            h = ui.Container()
            h.add_item(ui.TextDisplay(f"## {tick} Whitelist Reset"))
            result.add_item(h)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            b = ui.Container()
            b.add_item(ui.TextDisplay(f"{e_dot} All users have been removed from the automod whitelist."))
            result.add_item(b)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            result.add_item(ui.TextDisplay(f"-# Updated by {interaction.user.display_name}  •  Assister Automod"))
            await interaction.response.edit_message(view=result)

        await ctx.reply(view=AmConfirmLayout(
            author_id=ctx.author.id,
            title="Reset Entire Whitelist",
            body_text=(
                f"Are you sure you want to remove **all users** from the whitelist for all events?\n\n"
                f"❗ **This action cannot be undone.**"
            ),
            on_confirm=on_confirm,
        ), mention_author=False)




    @_automod.group(name="antilink", description="Enable or Disable the antilink feature", usage="automod antilink", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _antilink(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix   = guild_prefix(guild_id) if guild_id else '.'
            embed = discord.Embed(
                title="",
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ Automod antilink help overview\n\n"
                            f"**Enable antilink:**\n`{prefix}automod antilink enable`\n\n"
                            f"**Disable antilink:**\n`{prefix}automod antilink disable`\n\n"
                            f"**Whitelisting:**\n`{prefix}automod antilink whitelist add <member>`\n`{prefix}automod antilink whitelist remove <member>`\n\n"
                            f"**Punishment:**\n`{prefix}automod antilink punishment mute or kick or ban`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"{ctx.bot.user.name} Automod", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)


    @_antilink.command(name="enable", description="Enable antilink", usage="automod antilink enable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antilink_enable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if self.automod.get(str(ctx.guild.id), {}).get("antilink", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antilink` is already enabled for **{ctx.guild.name}**", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antilink"]["enabled"] = True
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully enabled `automod-antilink` for **{ctx.guild.name}**", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antilink.command(name="disable", description="Disable antilink", usage="automod antilink disable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antilink_disable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if not self.automod.get(str(ctx.guild.id), {}).get("antilink", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antilink` is already disabled for **{ctx.guild.name}**.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antilink"]["enabled"] = False
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully disabled `automod-antilink` for **{ctx.guild.name}**.", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antilink.command(aliases=['wl'], name="whitelist", description="Manage the whitelist for antilink", usage="automod antilink whitelist add|remove <member>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(action="Set either to 'add' or 'remove'", member="Select the member you want to add or remove")
    async def antilink_whitelist(self, ctx: commands.Context, action: str, member: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix   = guild_prefix(guild_id) if guild_id else '.'
        embed    = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        action   = action.lower()
        if action == "add":
            if member.id not in self.automod[str(ctx.guild.id)]["antilink"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antilink"]["whitelist"].append(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully added {member.mention} to `antilink-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is already in `antilink-whitelist`"
        elif action == "remove":
            if member.id in self.automod[str(ctx.guild.id)]["antilink"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antilink"]["whitelist"].remove(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully removed {member.mention} from `antilink-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is not in `antilink-whitelist`"
        else:
            embed.description = f"**❓ Whitelisting:**\n`{prefix}automod antilink whitelist add <member>`\n`{prefix}automod antilink whitelist remove <member>`\n\n"
        await ctx.reply(embed=embed, mention_author=False)


    @_antilink.command(aliases=['punish'], name="punishment", description="Set punishment for antilink", usage="automod antilink punishment <punishment>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(punishment="Set the punishment for antilink: 'mute', 'kick', 'ban'")
    async def antilink_punishment(self, ctx: commands.Context, punishment: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        valid_punishments = ["mute", "kick", "ban"]
        embed = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        if punishment.lower() in valid_punishments:
            self.amsettings(ctx.guild.id)
            self.automod[str(ctx.guild.id)]["antilink"]["punishment"] = punishment.lower()
            saveauto(self.automod)
            embed.description = f"{tick} | Successfully set the punishment for `antilink` to **{punishment.lower()}**."
        else:
            embed.description = f"❓ Invalid punishment. Valid punishments are: **'mute'**, **'kick'**, or **'ban'**."
        await ctx.reply(embed=embed, mention_author=False)





    @_automod.group(name="antispam", description="Enable or Disable the antispam feature", usage="automod antispam", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _antispam(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix   = guild_prefix(guild_id) if guild_id else '.'
            embed = discord.Embed(
                title="",
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ Automod antispam help overview\n\n"
                            f"**Enable antispam:**\n`{prefix}automod antispam enable`\n\n"
                            f"**Disable antispam:**\n`{prefix}automod antispam disable`\n\n"
                            f"**Whitelisting:**\n`{prefix}automod antispam whitelist add <member>`\n`{prefix}automod antispam whitelist remove <member>`\n\n"
                            f"**Punishment:**\n`{prefix}automod antispam punishment mute or kick or ban`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"{ctx.bot.user.name} Automod", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)


    @_antispam.command(name="enable", description="Enable antispam", usage="automod antispam enable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antispam_enable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if self.automod.get(str(ctx.guild.id), {}).get("antispam", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antispam` is already enabled for **{ctx.guild.name}**.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antispam"]["enabled"] = True
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully enabled `automod-antispam` for **{ctx.guild.name}**.", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antispam.command(name="disable", description="Disable antispam", usage="automod antispam disable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antispam_disable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if not self.automod.get(str(ctx.guild.id), {}).get("antispam", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antispam` is already disabled for **{ctx.guild.name}**.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antispam"]["enabled"] = False
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully disabled `automod-antispam` for **{ctx.guild.name}**.", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antispam.command(aliases=['wl'], name="whitelist", description="Manage the whitelist for antispam", usage="automod antispam whitelist add|remove <member>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(action="Set either to 'add' or 'remove'", member="Select the member you want to add or remove")
    async def antispam_whitelist(self, ctx: commands.Context, action: str, member: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix   = guild_prefix(guild_id) if guild_id else '.'
        embed    = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        action   = action.lower()
        if action == "add":
            if member.id not in self.automod[str(ctx.guild.id)]["antispam"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antispam"]["whitelist"].append(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully added {member.mention} to `antispam-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is already in `antispam-whitelist`"
        elif action == "remove":
            if member.id in self.automod[str(ctx.guild.id)]["antispam"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antispam"]["whitelist"].remove(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully removed {member.mention} from `antispam-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is not in `antispam-whitelist`"
        else:
            embed.description = f"**❓ Whitelisting:**\n`{prefix}automod antispam whitelist add <member>`\n`{prefix}automod antispam whitelist remove <member>`\n\n"
        await ctx.reply(embed=embed, mention_author=False)


    @_antispam.command(aliases=['punish'], name="punishment", description="Set punishment for antispam", usage="automod antispam punishment <punishment>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(punishment="Set the punishment for antispam: 'mute', 'kick', 'ban'")
    async def antispam_punishment(self, ctx: commands.Context, punishment: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        valid_punishments = ["mute", "kick", "ban"]
        embed = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        if punishment.lower() in valid_punishments:
            self.amsettings(ctx.guild.id)
            self.automod[str(ctx.guild.id)]["antispam"]["punishment"] = punishment.lower()
            saveauto(self.automod)
            embed.description = f"{tick} | Successfully set the punishment for `antispam` to **{punishment.lower()}**."
        else:
            embed.description = f"{grey} | Invalid punishment. Valid punishments are: **'mute'**, **'kick'**, or **'ban'**."
        await ctx.reply(embed=embed, mention_author=False)





    @_automod.group(name="antiinvites", description="Enable or Disable the antiinvites feature", usage="automod antiinvites", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _antiinvites(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix   = guild_prefix(guild_id) if guild_id else '.'
            embed = discord.Embed(
                title="",
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ Automod antiinvites help overview\n\n"
                            f"**Enable antiinvites:**\n`{prefix}automod antiinvites enable`\n\n"
                            f"**Disable antiinvites:**\n`{prefix}automod antiinvites disable`\n\n"
                            f"**Whitelisting:**\n`{prefix}automod antiinvites whitelist add <member>`\n`{prefix}automod antiinvites whitelist remove <member>`\n\n"
                            f"**Punishment:**\n`{prefix}automod antiinvites punishment mute or kick or ban`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"{ctx.bot.user.name} Automod", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)


    @_antiinvites.command(name="enable", description="Enable antiinvites", usage="automod antiinvites enable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antiinvites_enable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if self.automod.get(str(ctx.guild.id), {}).get("antiinvites", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antiinvites` is already enabled for **{ctx.guild.name}**.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antiinvites"]["enabled"] = True
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully enabled `automod-antiinvites` for **{ctx.guild.name}**.", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antiinvites.command(name="disable", description="Disable antiinvites", usage="automod antiinvites disable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antiinvites_disable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if not self.automod.get(str(ctx.guild.id), {}).get("antiinvites", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antiinvites` is already disabled for **{ctx.guild.name}**.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antiinvites"]["enabled"] = False
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully disabled `automod-antiinvites` for **{ctx.guild.name}**.", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antiinvites.command(aliases=['wl'], name="whitelist", description="Manage the whitelist for antiinvites", usage="automod antiinvites whitelist add|remove <member>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(action="Set either to 'add' or 'remove'", member="Select the member you want to add or remove")
    async def antiinvites_whitelist(self, ctx: commands.Context, action: str, member: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix   = guild_prefix(guild_id) if guild_id else '.'
        embed    = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        action   = action.lower()
        if action == "add":
            if member.id not in self.automod[str(ctx.guild.id)]["antiinvites"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antiinvites"]["whitelist"].append(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully added {member.mention} to `antiinvites-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is already in `antiinvites-whitelist`"
        elif action == "remove":
            if member.id in self.automod[str(ctx.guild.id)]["antiinvites"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antiinvites"]["whitelist"].remove(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully removed {member.mention} from `antiinvites-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is not in `antiinvites-whitelist`"
        else:
            embed.description = f"**❓ Whitelisting:**\n`{prefix}automod antiinvites whitelist add <member>`\n`{prefix}automod antiinvites whitelist remove <member>`\n\n"
        await ctx.reply(embed=embed, mention_author=False)


    @_antiinvites.command(aliases=['punish'], name="punishment", description="Set punishment for antiinvites", usage="automod antiinvites punishment <punishment>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(punishment="Set the punishment for antiinvites: 'mute', 'kick', 'ban'")
    async def antiinvites_punishment(self, ctx: commands.Context, punishment: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        valid_punishments = ["mute", "kick", "ban"]
        embed = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        if punishment.lower() in valid_punishments:
            self.amsettings(ctx.guild.id)
            self.automod[str(ctx.guild.id)]["antiinvites"]["punishment"] = punishment.lower()
            saveauto(self.automod)
            embed.description = f"{tick} | Successfully set the punishment for `antiinvites` to **{punishment.lower()}**."
        else:
            embed.description = f"{grey} | Invalid punishment. Valid punishments are: **'mute'**, **'kick'**, or **'ban'**."
        await ctx.reply(embed=embed, mention_author=False)





    @_automod.group(name="antiswear", description="Enable or Disable the antiswear feature", usage="automod antiswear", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _antiswear(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix   = guild_prefix(guild_id) if guild_id else '.'
            embed = discord.Embed(
                title="",
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ Automod antiswear help overview\n\n"
                            f"**Enable antiswear:**\n`{prefix}automod antiswear enable`\n\n"
                            f"**Disable antiswear:**\n`{prefix}automod antiswear disable`\n\n"
                            f"**Add words to blocklist:**\n`{prefix}automod antiswear add <word>`\n\n"
                            f"**Remove words from blocklist:**\n`{prefix}automod antiswear remove <word>`\n\n"
                            f"**View blocklist:**\n`{prefix}automod antiswear show`\n\n"
                            f"**Reset blocklist:**\n`{prefix}automod antiswear reset`\n\n"
                            f"**Whitelisting:**\n`{prefix}automod antiswear whitelist add <member>`\n`{prefix}automod antiswear whitelist remove <member>`\n\n"
                            f"**Punishment:**\n`{prefix}automod antiswear punishment mute or kick or ban`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"{ctx.bot.user.name} Automod", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(name="enable", description="Enable antiswear", usage="automod antiswear enable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antiswear_enable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if self.automod.get(str(ctx.guild.id), {}).get("antiswear", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antiswear` is already enabled for **{ctx.guild.name}**.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antiswear"]["enabled"] = True
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully enabled `automod-antiswear` for **{ctx.guild.name}**.", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(name="disable", description="Disable antiswear", usage="automod antiswear disable", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def antiswear_disable(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        if not self.automod.get(str(ctx.guild.id), {}).get("antiswear", {}).get("enabled", False):
            embed = discord.Embed(description=f"{grey} | `automod-antiswear` is already disabled for **{ctx.guild.name}**.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        self.automod[str(ctx.guild.id)]["antiswear"]["enabled"] = False
        saveauto(self.automod)
        embed = discord.Embed(description=f"{tick} | Successfully disabled `automod-antiswear` for **{ctx.guild.name}**.", color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(name="add", description="Add a swear word to blocklist", usage="automod antiswear add <word>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(word="Type the word you want to add to swear word blocklist")
    async def add_antiswear(self, ctx: commands.Context, *, word: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        word     = word.lower()
        if guild_id not in self.antiswear:
            self.antiswear[guild_id] = []
        if word not in self.antiswear[guild_id]:
            self.antiswear[guild_id].append(word)
            saveantiswear(self.antiswear)
            embed = discord.Embed(description=f"{tick} | Successfully added `{word}` to blocklist in **`{ctx.guild.name}`**", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(description=f"{grey} | '{word}' is already blocklisted", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(name="remove", description="Remove a swear word from blocklist", usage="automod antiswear remove <word>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(word="Type the word you want to remove from swear word blocklist")
    async def remove_antiswear(self, ctx: commands.Context, *, word: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        word     = word.lower()
        if guild_id in self.antiswear and word in self.antiswear[guild_id]:
            self.antiswear[guild_id].remove(word)
            saveantiswear(self.antiswear)
            embed = discord.Embed(description=f"{tick} | Successfully removed `{word}` from blocklist", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(description=f"{grey} | '{word}' isn't blocklisted.", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(aliases=['list'], name="show", description="Shows the swear word blocklist", usage="automod antiswear show")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def show_antiswear(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        words    = self.antiswear.get(guild_id, [])
        if words:
            lund  = "  ".join(f"`{index + 1}.` {word}" for index, word in enumerate(words))
            embed = discord.Embed(description=f"{e_dot} Blocked swear words in **{ctx.guild.name}**:\n{lund}", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(description=f"❓ No word blocklisted in **{ctx.guild.name}**", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(name="reset", description="Reset antiswear words blocklist", usage="automod antiswear reset", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def reset_antiswear(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        if guild_id in self.antiswear:
            del self.antiswear[guild_id]
            saveantiswear(self.antiswear)
            embed = discord.Embed(description=f"{tick} | Successfully reset swear word blocklist", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(description=f"{grey} | No blocked words found for **{ctx.guild.name}**", color=colour)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(aliases=['wl'], name="whitelist", description="Manage the whitelist for antiswear", usage="automod antiswear whitelist add|remove <member>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(action="Set either to 'add' or 'remove'", member="Select the member you want to add or remove")
    async def antiswear_whitelist(self, ctx: commands.Context, action: str, member: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        self.amsettings(ctx.guild.id)
        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix   = guild_prefix(guild_id) if guild_id else '.'
        embed    = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        action   = action.lower()
        if action == "add":
            if member.id not in self.automod[str(ctx.guild.id)]["antiswear"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antiswear"]["whitelist"].append(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully added {member.mention} to `antiswear-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is already in `antiswear-whitelist`"
        elif action == "remove":
            if member.id in self.automod[str(ctx.guild.id)]["antiswear"]["whitelist"]:
                self.automod[str(ctx.guild.id)]["antiswear"]["whitelist"].remove(member.id)
                saveauto(self.automod)
                embed.description = f"{tick} | Successfully removed {member.mention} from `antiswear-whitelist`"
            else:
                embed.description = f"{grey} | {member.mention} is not in `antiswear-whitelist`"
        else:
            embed.description = f"**❓ Whitelisting:**\n`{prefix}automod antiswear whitelist add <member>`\n`{prefix}automod antiswear whitelist remove <member>`\n\n"
        await ctx.reply(embed=embed, mention_author=False)


    @_antiswear.command(aliases=['punish'], name="punishment", description="Set punishment for antiswear", usage="automod antiswear punishment <punishment>", category="Automod")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(punishment="Set the punishment for antiswear: 'mute', 'kick', 'ban'")
    async def antiswear_punishment(self, ctx: commands.Context, punishment: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        valid_punishments = ["mute", "kick", "ban"]
        embed = discord.Embed(color=colour)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        if punishment.lower() in valid_punishments:
            self.amsettings(ctx.guild.id)
            self.automod[str(ctx.guild.id)]["antiswear"]["punishment"] = punishment.lower()
            saveauto(self.automod)
            embed.description = f"{tick} | Successfully set the punishment for `antiswear` to **{punishment.lower()}**."
        else:
            embed.description = f"{grey} | Invalid punishment. Valid punishments are: **'mute'**, **'kick'**, or **'ban'**."
        await ctx.reply(embed=embed, mention_author=False)






async def setup(bot):
    await bot.add_cog(Automod(bot))