import discord
from discord import ui
from discord.ext import commands
from discord import app_commands
from utils.checks import *
from utils.helplund import *
from utils.loads import *
from utils.prefixes import *
from utils.variables import *
from utils.paginator import Ahm







ALL_EVENTS = [
    ('Anti Bot',            'anti_bot'),
    ('Anti Ping',           'anti_ping'),
    ('Anti Channel Create', 'anti_channel_create'),
    ('Anti Channel Delete', 'anti_channel_delete'),
    ('Anti Channel Update', 'anti_channel_update'),
    ('Anti Role Create',    'anti_role_create'),
    ('Anti Role Delete',    'anti_role_delete'),
    ('Anti Role Update',    'anti_role_update'),
    ('Anti Webhook',        'anti_webhook'),
    ('Anti Server',         'anti_server'),
    ('Anti Ban',            'anti_ban'),
    ('Anti Kick',           'anti_kick'),
]



def _event_options():
    return [discord.SelectOption(label=l, value=v) for l, v in ALL_EVENTS]

def _fmt_events(events: list, enabled=True) -> str:
    emoji = "<a:enable:1496894249822720052>" if enabled else "<a:disable:1496894585035817022>"
    return '\n'.join(f"{emoji} {e.replace('_', ' ').title()}" for e in events)







class AntiSuccessLayout(ui.LayoutView):
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

            punishment_container = ui.Container()
            punishment_container.add_item(
                ui.TextDisplay(
                    f"<:bionic_g_ban:1261572949572321353> **Punishment:** `{punishment}`"
                )
            )
            self.add_item(punishment_container)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self.add_item(ui.TextDisplay(
            f"-# Updated by {user.display_name}  •  {footer}"
        ))




class ConfirmLayout(ui.LayoutView):
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

        self.add_item(ui.TextDisplay("-# Assister Antinuke  •  Confirm action"))

        btn_row = ui.ActionRow()
        yes = ui.Button(label="Confirm", style=discord.ButtonStyle.success, custom_id="confirm_yes")
        no  = ui.Button(label="Cancel",  style=discord.ButtonStyle.danger,  custom_id="confirm_no")
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





class AntiEnableLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_name: str):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_name = guild_name
        self._build()

    def _build(self):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <a:enable:1496894249822720052> Enable Antinuke Events\n"
            f"Select individual events from the dropdown, or hit **Enable All** to turn on everything at once."
        ))
        self.add_item(header)


        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Server:** `{self.guild_name}`\n"
            f"{e_dot} Choose which antinuke protections to activate."
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        self.add_item(ui.TextDisplay("-# Assister Antinuke  •  Enable"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Select events to enable…",
            custom_id="antinuke_enable_select",
            min_values=1,
            max_values=len(ALL_EVENTS),
            options=_event_options(),
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

        btn_row = ui.ActionRow()
        btn = ui.Button(label="Enable All Events", style=discord.ButtonStyle.success,
                        custom_id="enable_all_btn")
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
        antid[guild_id] = {
            "enabled_events": selected,
            "punishment": antid.get(guild_id, {}).get("punishment", "kick"),
        }
        saveanti(antid)
        pun = antid[guild_id]["punishment"].capitalize()
        await interaction.response.edit_message(view=AntiSuccessLayout(
            title=f"{antiemoji} Antinuke Enabled — {interaction.guild.name}",
            events_text=_fmt_events(selected, enabled=True),
            punishment=pun,
            user=interaction.user,
            footer="Assister Antinuke  •  Enable",
        ))

    async def _on_enable_all(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        guild_id = str(interaction.guild.id)
        all_vals = [v for _, v in ALL_EVENTS]
        antid[guild_id] = {
            "enabled_events": all_vals,
            "punishment": antid.get(guild_id, {}).get("punishment", "kick"),
        }
        saveanti(antid)
        pun = antid[guild_id]["punishment"].capitalize()
        await interaction.response.edit_message(view=AntiSuccessLayout(
            title=f"{antiemoji} All Events Enabled — {interaction.guild.name}",
            events_text=_fmt_events(all_vals, enabled=True),
            punishment=pun,
            user=interaction.user,
            footer="Assister Antinuke  •  Enable All",
        ))




class AntiDisableLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_name: str):
        super().__init__(timeout=120)
        self.author_id  = author_id
        self.guild_name = guild_name
        self._build()

    def _build(self):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <a:disable:1496894585035817022> Disable Antinuke Events\n"
            f"Select individual events from the dropdown, or hit **Disable All** to turn everything off."
        ))
        self.add_item(header)

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Server:** `{self.guild_name}`\n"
            f"{e_dot} Choose which antinuke protections to deactivate."
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        self.add_item(ui.TextDisplay("-# Assister Antinuke  •  Disable"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Select events to disable…",
            custom_id="antinuke_disable_select",
            min_values=1,
            max_values=len(ALL_EVENTS),
            options=_event_options(),
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

        btn_row = ui.ActionRow()
        btn = ui.Button(label="Disable All Events", style=discord.ButtonStyle.danger,
                        custom_id="disable_all_btn")
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
        current  = antid.get(guild_id, {}).get("enabled_events", [])
        antid[guild_id] = {
            "enabled_events": [e for e in current if e not in selected],
            "punishment": antid.get(guild_id, {}).get("punishment", "kick"),
        }
        saveanti(antid)
        await interaction.response.edit_message(view=AntiSuccessLayout(
            title=f"{antiemoji} Events Disabled — {interaction.guild.name}",
            events_text=_fmt_events(selected, enabled=False),
            punishment=None,
            user=interaction.user,
            footer="Assister Antinuke  •  Disable",
        ))

    async def _on_disable_all(self, interaction: discord.Interaction):
        if not await self._check(interaction):
            return
        guild_id = str(interaction.guild.id)
        all_vals = [v for _, v in ALL_EVENTS]
        antid[guild_id] = {
            "enabled_events": [],
            "punishment": antid.get(guild_id, {}).get("punishment", "kick"),
        }
        saveanti(antid)
        await interaction.response.edit_message(view=AntiSuccessLayout(
            title=f"{antiemoji} All Events Disabled — {interaction.guild.name}",
            events_text=_fmt_events(all_vals, enabled=False),
            punishment=None,
            user=interaction.user,
            footer="Assister Antinuke  •  Disable All",
        ))




class PunishmentLayout(ui.LayoutView):
    def __init__(self, author_id: int, guild_id: str, current: str):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.guild_id  = guild_id
        self.current   = current
        self._build()

    def _build(self):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:punish:1499307086461538457> Antinuke Punishment\n"
            f"Choose what happens to a user who triggers an antinuke event."
        ))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Current punishment:** `{self.current}`\n\n"
            f"<:kick:1499307114185625691> **Kick** — Remove the user from the server\n"
            f"<:bionic_g_ban:1261572949572321353> **Ban** — Permanently ban the member\n"
            f"<:punishment:1499307386823901287> **Mute** — Timeout / mute the member for 24h"
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        self.add_item(ui.TextDisplay("-# Assister Antinuke  •  Punishment"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Choose a punishment…",
            custom_id="antinuke_punishment_select",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Kick", value="kick",
                                     description="Kick the offending member from the server", emoji="<:kick:1499307114185625691>"),
                discord.SelectOption(label="Ban",  value="ban",
                                     description="Permanently ban the offending member",        emoji="<:bionic_g_ban:1261572949572321353>"),
                discord.SelectOption(label="Mute", value="mute",
                                     description="Timeout / mute the offending member for 24h",         emoji="<:punishment:1499307386823901287>"),
            ],
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return
        chosen = interaction.data["values"][0]
        data   = antid.get(self.guild_id, {})
        data["punishment"] = chosen
        data.setdefault("enabled_events", [])
        antid[self.guild_id] = data
        saveanti(antid)

        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {tick} Punishment Updated"))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} Antinuke punishment set to **`{chosen.capitalize()}`**."
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        self.add_item(ui.TextDisplay(
            f"-# Updated by {interaction.user.display_name}  •  Assister Antinuke"
        ))

        await interaction.response.edit_message(view=self)



class WhitelistAddLayout(ui.LayoutView):
    def __init__(self, author_id: int, member: discord.Member):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.member    = member
        self._build()

    def _build(self):
        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:fn_verify:1497547412820983938> Whitelist — {self.member.display_name}\n"
            f"Select which antinuke events to exempt this member from."
        ))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Member:** {self.member.mention}\n"
            f"{e_dot} **User ID:** `{self.member.id}`"
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        self.add_item(ui.TextDisplay("-# Assister Antinuke  •  Whitelist"))

        row = ui.ActionRow()
        sel = ui.Select(
            placeholder="Select events to whitelist…",
            custom_id="antinuke_wl_select",
            min_values=1,
            max_values=len(ALL_EVENTS),
            options=_event_options(),
        )
        sel.callback = self._on_select
        row.add_item(sel)
        self.add_item(row)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This interaction isn't for you.", ephemeral=True)
            return
        selected  = interaction.data["values"]
        guild_id  = str(interaction.guild.id)
        whitelist = antid.get(guild_id, {}).get("whitelist", {})

        if str(self.member.id) not in whitelist:
            whitelist[str(self.member.id)] = []
        for event in selected:
            if event not in whitelist[str(self.member.id)]:
                whitelist[str(self.member.id)].append(event)

        antid.setdefault(guild_id, {})["whitelist"] = whitelist
        saveanti(antid)

        status = _fmt_events(whitelist[str(self.member.id)], enabled=True)

        self.clear_items()

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {antiemoji} Whitelist Updated — {self.member.display_name}"))
        self.add_item(header)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} **Member:** {self.member.mention}\n"
            f"{e_dot} **User ID:** `{self.member.id}`\n\n"
            f"**Whitelisted Events:**\n{status}"
        ))
        self.add_item(body)

        self.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        self.add_item(ui.TextDisplay(
            f"-# Updated by {interaction.user.display_name}  •  Assister Antinuke"
        ))

        await interaction.response.edit_message(view=self)



class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot   = bot


    @commands.hybrid_group(name='antinuke', aliases=['anti'], invoke_without_command=True,
                           description="Antinuke overview", usage="antinuke")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke(self, ctx: commands.Context):
        ahm7 = self.bot.get_command('help')
        if ahm7:
            await ctx.invoke(ahm7, query='antinuke')


    @antinuke.command(name='enable', description="Enable antinuke events", usage="antinuke enable")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_enable(self, ctx: commands.Context):
        await ctx.reply(view=AntiEnableLayout(ctx.author.id, ctx.guild.name), mention_author=False)


    @antinuke.command(name='disable', description="Disable antinuke events", usage="antinuke disable")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_disable(self, ctx: commands.Context):
        await ctx.reply(view=AntiDisableLayout(ctx.author.id, ctx.guild.name), mention_author=False)

    @antinuke.command(name='show', aliases=['view', 'config', 'setup'],
                      description="Shows antinuke configuration", usage="antinuke config")
    @admin()
    @aboveb()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_show(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        guild_id = str(ctx.guild.id)
        data = antid.get(guild_id, {})

        layout = ui.LayoutView(timeout=0)

        if not data:
            c = ui.Container()
            c.add_item(ui.TextDisplay(
                f"## {cross} Antinuke Not Configured\n"
                f"{e_dot} Antinuke hasn't been set up for **{ctx.guild.name}** yet."
            ))
            layout.add_item(c)
            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            layout.add_item(ui.TextDisplay(
                f"-# Requested by {ctx.author.display_name}  •  Assister Antinuke"
            ))
            await ctx.reply(view=layout, mention_author=False)
            return

        enabled_events = data.get("enabled_events", [])
        punishment     = data.get("punishment", "kick").capitalize()
        enblev = _fmt_events(enabled_events, enabled=True) if enabled_events else "❗ No events enabled"

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"##  <:security:1496893471401836695> Antinuke Config — {ctx.guild.name}"))
        layout.add_item(header)

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"**{list_emoji} Enabled Events:**\n{enblev}"
        ))
        layout.add_item(body)

        chut = ui.Container()
        chut.add_item(ui.TextDisplay(f"<:bionic_g_ban:1261572949572321353> **Punishment:** `{punishment}`"))
        layout.add_item(chut)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        layout.add_item(ui.TextDisplay(
            f"-# Requested by {ctx.author.display_name}  •  Assister Antinuke"
        ))

        await ctx.reply(view=layout, mention_author=False)

    @antinuke.group(name='punishment', aliases=['punish'], invoke_without_command=True,
                    description="Set antinuke punishment", usage="antinuke punishment")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_punishment(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        current = antid.get(guild_id, {}).get("punishment", "kick").capitalize()
        await ctx.reply(view=PunishmentLayout(ctx.author.id, guild_id, current), mention_author=False)

    @antinuke_punishment.command(name='set', description="Set punishment type",
                                 usage="antinuke punishment set kick|ban|mute")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(punishment="'kick', 'ban', or 'mute'")
    async def antinuke_punishment_set(self, ctx: commands.Context, punishment: str):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        layout = ui.LayoutView(timeout=0)

        if punishment not in ('kick', 'ban', 'mute'):
            c = ui.Container()
            c.add_item(ui.TextDisplay(
                f"## {cross} Invalid Punishment\n"
                f"Valid options are: `kick`, `ban`, `mute`."
            ))
            layout.add_item(c)
            await ctx.reply(view=layout, mention_author=False)
            return

        guild_id = str(ctx.guild.id)
        data = antid.get(guild_id, {})
        data["punishment"] = punishment
        data.setdefault("enabled_events", [])
        antid[guild_id] = data
        saveanti(antid)

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## {tick} Punishment Set"))
        layout.add_item(header)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"{e_dot} Antinuke punishment set to **`{punishment.capitalize()}`**."
        ))
        layout.add_item(body)
        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Updated by {ctx.author.display_name}  •  Assister Antinuke"
        ))
        await ctx.reply(view=layout, mention_author=False)

    @antinuke_punishment.command(name='show', aliases=['view'],
                                 description="Shows current antinuke punishment",
                                 usage="antinuke punishment show")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_punishment_show(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        guild_id = str(ctx.guild.id)
        data = antid.get(guild_id, {})

        layout = ui.LayoutView(timeout=0)
        c = ui.Container()

        if data and "punishment" in data:
            c.add_item(ui.TextDisplay(f"## <:punish:1499307086461538457> Current Punishment"))
            layout.add_item(c)
            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            body = ui.Container()
            body.add_item(ui.TextDisplay(
                f"{e_dot} Punishment type: **`{data['punishment'].capitalize()}`**"
            ))
            layout.add_item(body)
        else:
            c.add_item(ui.TextDisplay(
                f"## {cross} Not Set\n"
                f"Antinuke punishment hasn't been configured for this server."
            ))
            layout.add_item(c)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Requested by {ctx.author.display_name}  •  Assister Antinuke"
        ))
        await ctx.reply(view=layout, mention_author=False)

    @antinuke_punishment.command(name='reset', description="Resets punishment to 'kick'",
                                 usage="antinuke punishment reset")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_punishment_reset(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        guild_id = str(ctx.guild.id)

        layout = ui.LayoutView(timeout=0)
        c = ui.Container()

        if guild_id in antid:
            antid[guild_id]["punishment"] = "kick"
            saveanti(antid)

            c.add_item(ui.TextDisplay(f"## {tick} Punishment Reset"))
            layout.add_item(c)
            layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            body = ui.Container()
            body.add_item(ui.TextDisplay(
                f"{e_dot} Antinuke punishment has been reset to **`Kick`**."
            ))
            layout.add_item(body)
        else:
            c.add_item(ui.TextDisplay(
                f"## {cross} Not Configured\n"
                f"Antinuke hasn't been set up for this server yet."
            ))
            layout.add_item(c)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Updated by {ctx.author.display_name}  •  Assister Antinuke"
        ))
        await ctx.reply(view=layout, mention_author=False)

    # ── whitelist ─────────────────────────────────────────────────────────────

    @antinuke.group(name='whitelist', aliases=['wl'], invoke_without_command=True,
                    description="Antinuke whitelisting", usage="antinuke whitelist")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_whitelist(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        prefix   = guild_prefix(guild_id) if guild_id else '.'

        layout = ui.LayoutView(timeout=0)

        header = ui.Container()
        header.add_item(ui.TextDisplay(
            f"## <:fn_verify:1497547412820983938> Antinuke Whitelist\n"
            f"```py\n"
            f"- [] = optional  |  <> = required\n"
            f"- Do not type brackets in commands!\n"
            f"```"
        ))
        layout.add_item(header)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        body.add_item(ui.TextDisplay(
            f"**Add to whitelist**\n`{prefix}antinuke whitelist add <member>`\n\n"
            f"**Remove from whitelist**\n`{prefix}antinuke whitelist remove <member>`\n\n"
            f"**View member's whitelisted events**\n`{prefix}antinuke whitelist show <member>`"
        ))
        body.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        body.add_item(ui.TextDisplay(
            f"**View all whitelisted members**\n`{prefix}antinuke whitelist showall`\n\n"
            f"**Reset entire whitelist**\n`{prefix}antinuke whitelist reset`"
        ))
        layout.add_item(body)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Requested by {ctx.author.display_name}  •  Assister Antinuke"
        ))

        await ctx.reply(view=layout, mention_author=False)

    @antinuke_whitelist.command(name='add', description="Adds a member to whitelist",
                                usage="antinuke whitelist add <member>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Member to whitelist")
    async def antinuke_whitelist_add(self, ctx: commands.Context, member: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        await ctx.reply(view=WhitelistAddLayout(ctx.author.id, member), mention_author=False)

    @antinuke_whitelist.command(name='remove', description="Removes a member from whitelist",
                                usage="antinuke whitelist remove <member>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Member to remove from whitelist")
    async def antinuke_whitelist_remove(self, ctx: commands.Context, member: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        guild_id  = str(ctx.guild.id)
        whitelist = antid.get(guild_id, {}).get("whitelist", {})

        if str(member.id) not in whitelist:
            layout = ui.LayoutView(timeout=0)
            c = ui.Container()
            c.add_item(ui.TextDisplay(
                f"## {cross} Not Whitelisted\n"
                f"**{member.display_name}** is not on the whitelist."
            ))
            layout.add_item(c)
            await ctx.reply(view=layout, mention_author=False)
            return

        async def on_confirm(interaction: discord.Interaction):
            current_wl = antid.get(guild_id, {}).get("whitelist", {})
            if str(member.id) in current_wl:
                del current_wl[str(member.id)]
            antid.setdefault(guild_id, {})["whitelist"] = current_wl
            saveanti(antid)

            result = ui.LayoutView(timeout=0)
            h = ui.Container()
            h.add_item(ui.TextDisplay(f"## {antiemoji} Whitelist Updated"))
            result.add_item(h)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            b = ui.Container()
            b.add_item(ui.TextDisplay(
                f"{e_dot} **{member.display_name}** has been removed from all whitelist events."
            ))
            result.add_item(b)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            result.add_item(ui.TextDisplay(
                f"-# Updated by {interaction.user.display_name}  •  Assister Antinuke"
            ))
            await interaction.response.edit_message(view=result)

        await ctx.reply(view=ConfirmLayout(
            author_id=ctx.author.id,
            title="Remove from Whitelist",
            body_text=(
                f"{e_dot} Remove **{member.mention}** from **all** whitelist events?\n\n"
                f"❗ **This action cannot be undone.**"
            ),
            on_confirm=on_confirm,
        ), mention_author=False)

    @antinuke_whitelist.command(name='show', aliases=['view', 'list'],
                                description="Shows a member's whitelisted events",
                                usage="antinuke whitelist show <member>")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Member to check")
    async def antinuke_whitelist_show(self, ctx: commands.Context, member: discord.Member):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        guild_id = str(ctx.guild.id)
        wld = antid.get(guild_id, {}).get("whitelist", {}).get(str(member.id), [])

        layout = ui.LayoutView(timeout=0)

        header = ui.Container()
        header.add_item(ui.TextDisplay(f"## <:fn_verify:1497547412820983938> Whitelist — {member.display_name}"))
        layout.add_item(header)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        body = ui.Container()
        if wld:
            body.add_item(ui.TextDisplay(
                f"{e_dot} **Member:** {member.mention}\n"
                f"{e_dot} **User ID:** `{member.id}`\n"
                f"{e_dot} **Profile:** [{member.name}](https://discord.com/users/{member.id})\n\n"
                f"**{antiemoji} Whitelisted Events:**\n{_fmt_events(wld, enabled=True)}"
            ))
        else:
            body.add_item(ui.TextDisplay(
                f"{grey} **{member.display_name}** is not whitelisted from any events."
            ))
        layout.add_item(body)

        layout.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        layout.add_item(ui.TextDisplay(
            f"-# Requested by {ctx.author.display_name}  •  Assister Antinuke Whitelisting"
        ))

        await ctx.reply(view=layout, mention_author=False)

    @antinuke_whitelist.command(name='showall', 
                                description="Shows all whitelisted users", 
                                usage="antinuke whitelist show all")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_whitelist_show_all(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        wld = antid.get(guild_id, {}).get("whitelist", {})

        pages = []
        ttl = len(wld)

        if ttl == 0:
            embed = discord.Embed(
                description=f"{grey}  No members are whitelisted.",
                color=colour
            )
            embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        for idx, (member_id, events) in enumerate(wld.items(), 1):
            member = ctx.guild.get_member(int(member_id))
            if not member:
                try:
                    member = await ctx.bot.fetch_user(int(member_id))
                except discord.NotFound:
                    member = None

            enblev = '\n'.join([f"<a:enable:1496894249822720052> {event.replace('_', ' ').title()}" for event in events])
            embed = discord.Embed(
                title=f"<:fn_verify:1497547412820983938> Whitelist Status for {member.name if member else 'User (Not in Server)'} - [{idx}/{ttl}]",
                description=(
                    f"{e_dot} Mention: {member.mention if member else 'N/A'}\n"
                    f"{e_dot} User ID: {member.id if member else 'N/A'}\n"
                    f"{e_dot} URL: [{member.name if member else 'User'}](https://discord.com/users/{member.id if member else 'N/A'})\n\n"
                    f"{list_emoji} **| Whitelisted events:**\n{enblev}"
                ),
                color=colour
            )
            
            embed.set_author(name=f"{ttl} users whitelisted", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Page {idx}/{ttl} | Use the buttons below to view other whitelisted users.", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @antinuke_whitelist.command(name='reset', description="Resets all users from whitelist",
                                usage="antinuke whitelist reset")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def antinuke_whitelist_reset_all(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        guild_id = str(ctx.guild.id)

        async def on_confirm(interaction):
            antid.setdefault(guild_id, {})["whitelist"] = {}
            saveanti(antid)

            result = ui.LayoutView(timeout=0)
            h = ui.Container()
            h.add_item(ui.TextDisplay(f"## {tick} Whitelist Reset"))
            result.add_item(h)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            b = ui.Container()
            b.add_item(ui.TextDisplay(
                f"{e_dot} All users have been removed from the antinuke whitelist."
            ))
            result.add_item(b)
            result.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            result.add_item(ui.TextDisplay(
                f"-# Updated by {interaction.user.display_name}  •  Assister Antinuke"
            ))
            await interaction.response.edit_message(view=result)

        await ctx.reply(view=ConfirmLayout(
            author_id=ctx.author.id,
            title="Reset Entire Whitelist",
            body_text=(
                f"Are you sure you want to remove **all users** from the whitelist?\n\n"
                f"❗ **This action cannot be undone.**"
            ),
            on_confirm=on_confirm,
        ), mention_author=False)





async def setup(bot):
    await bot.add_cog(Antinuke(bot))