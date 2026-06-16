import discord
from discord import app_commands, ui
from discord.ext import commands

from utils.prefixes  import guild_prefix
from utils.variables import colour, cross, blnk
from utils.checks    import bled
from utils.helplund  import lul, lull, lulll


def _get_prefix(ctx_or_interaction) -> str:
    gid = None
    if hasattr(ctx_or_interaction, "guild") and ctx_or_interaction.guild:
        gid = str(ctx_or_interaction.guild.id)
    return guild_prefix(gid) if gid else "."


_GROUP_SECURITY = ["antinuke", "automod", "autorole", "moderation", "welcomer"]
_GROUP_UTILITY  = ["giveaway", "utility", "media", "voice", "general", "game", "extra"]


def _make_dropdown(current: str | None = None) -> ui.Select:
    return ui.Select(
        placeholder = "Browse a category …",
        custom_id   = "help_cat_select",
        options     = [
            discord.SelectOption(
                label       = cat.capitalize(),
                value       = cat,
                description = lulll[cat],
                emoji       = lull[cat],
                default     = (cat == current),
            )
            for cat in lulll
        ],
    )


    
class HelpHomeLayout(ui.LayoutView):

    def __init__(self, user: discord.abc.User, prefix: str, bot):
        super().__init__(timeout=120)
        self.user   = user
        self.prefix = prefix
        self.bot    = bot

        total_cmds = sum(len(v) for v in lul.values())
        total_cats = len(lulll)
        avatar_url = bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url

        c = ui.Container()
        c.add_item(ui.Section(
            ui.TextDisplay(
                f"### <:assister:1500016915333124106> Assister Help Overview\n\n"
                f"`{prefix}help <category>` browse a category\n"
                f"`{prefix}help <command>` look up a command\n\n"
                f"`{total_cmds}` commands across `{total_cats}` categories\n"
            ),
            accessory=ui.Thumbnail(avatar_url),
        ))
        c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        c.add_item(ui.TextDisplay(
            f"Assister is a multi-purpose moderation and utility bot designed to keep your server organised, secure, and fun. "
            f"From automated protection against raids and spam to interactive giveaways, polls, and mini-games, "
            f"Assister gives you everything you need in one clean package.\n\n"
            f"**Some useful link(s)**\n"
            f"[🡵 Full command docs](https://assisterbot.xyz/docs)\n"
            f"[🡵 Privacy Policy](https://assisterbot.xyz/pp)   [🡵 Terms of Service](https://assisterbot.xyz/tos)\n"
            f"[🡵 GitHub](https://github.com/code2ahm/assister)\n\n"
            f"**Use the dropdown below to browse a category and explore all available commands.**"
        ))
        self.add_item(c)

        self.add_item(ui.TextDisplay(f"-# Requested by {self.user.display_name}"))

        sel          = _make_dropdown()
        sel.callback = self._on_select
        row          = ui.ActionRow()
        row.add_item(sel)
        self.add_item(row)

    async def _on_select(self, interaction: discord.Interaction):
        cat = interaction.data["values"][0]
        await interaction.response.edit_message(
            view=HelpCategoryLayout(interaction.user, cat, _get_prefix(interaction), self.bot)
        )





class HelpCategoryLayout(ui.LayoutView):
    MAX_PER_PAGE = 6

    def __init__(self, user: discord.abc.User, category: str, prefix: str, bot=None, page: int = 1):
        super().__init__(timeout=120)
        self.user      = user
        self.category  = category
        self.prefix    = prefix
        self.bot       = bot
        self.page      = page

        self._all_cmds = list(lul.get(category, {}).items())
        self.total     = max(1, (len(self._all_cmds) + self.MAX_PER_PAGE - 1) // self.MAX_PER_PAGE)

        self._c = ui.Container()

        self._header = ui.TextDisplay("")
        self._c.add_item(self._header)

        self._slots     = []
        self._slot_seps = []
        for _ in range(self.MAX_PER_PAGE):
            sep = ui.Separator(spacing=discord.SeparatorSpacing.large)
            td  = ui.TextDisplay("")
            self._slot_seps.append(sep)
            self._slots.append(td)
            self._c.add_item(sep)
            self._c.add_item(td)

        self._c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        self._footer = ui.TextDisplay("")
        self._c.add_item(self._footer)
        self._c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        self._btn_prev = ui.Button(
            emoji="<:left:1496888475922731062>",
            style=discord.ButtonStyle.blurple,
            custom_id="cat_prev",
            disabled=True,
        )
        self._btn_home = ui.Button(
            emoji="<:home:1496897554946855002>",
            style=discord.ButtonStyle.green,
            custom_id="cat_home",
        )
        self._btn_next = ui.Button(
            emoji="<:right:1496889463564009565>",
            style=discord.ButtonStyle.blurple,
            custom_id="cat_next",
            disabled=self.total <= 1,
        )
        self._btn_prev.callback = self._on_prev
        self._btn_home.callback = self._on_home
        self._btn_next.callback = self._on_next

        nav = ui.ActionRow()
        nav.add_item(self._btn_prev)
        nav.add_item(self._btn_home)
        nav.add_item(self._btn_next)
        self._c.add_item(nav)

        sel          = _make_dropdown(category)
        sel.callback = self._on_select
        sel_row      = ui.ActionRow()
        sel_row.add_item(sel)
        self._c.add_item(sel_row)

        self._renderr()
        self.add_item(self._c)


    def _current_cmds(self):
        start = (self.page - 1) * self.MAX_PER_PAGE
        return self._all_cmds[start : start + self.MAX_PER_PAGE]

    def _renderr(self):
        emoji = lull.get(self.category, "📂")
        desc  = lulll.get(self.category, "")
        total = len(self._all_cmds)

        self._header.content = (
            f"## {emoji}  {self.category.capitalize()}\n"
            f"-# {desc}  ·  {total} commands total"
        )

        current = self._current_cmds()
        for i in range(self.MAX_PER_PAGE):
            if i < len(current):
                name, info = current[i]
                self._slots[i].content = (
                    f"**{name}**\n"
                    f"{info['description']}\n"
                    f"-# `{self.prefix}{info['usage']}`"
                )
                self._slots[i].visible     = True
                self._slot_seps[i].visible = True
            else:
                self._slots[i].content     = "\u200b"
                self._slots[i].visible     = False
                self._slot_seps[i].visible = False

        self._footer.content    = f"-# {self.user.display_name}  ·  Page {self.page}/{self.total}"
        self._btn_prev.disabled = self.page <= 1
        self._btn_next.disabled = self.page >= self.total


    async def _on_prev(self, interaction: discord.Interaction):
        self.page -= 1
        self._renderr()
        await interaction.response.edit_message(view=self)

    async def _on_home(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            view=HelpHomeLayout(interaction.user, _get_prefix(interaction), self.bot)
        )

    async def _on_next(self, interaction: discord.Interaction):
        self.page += 1
        self._renderr()
        await interaction.response.edit_message(view=self)

    async def _on_select(self, interaction: discord.Interaction):
        cat = interaction.data["values"][0]
        await interaction.response.edit_message(
            view=HelpCategoryLayout(interaction.user, cat, _get_prefix(interaction), self.bot)
        )






async def _send_command_info(ctx: commands.Context, query: str, bot: commands.Bot):
    prefix = _get_prefix(ctx)

    for category, cmds in lul.items():
        for name, info in cmds.items():
            cmd_obj = bot.get_command(name)
            aliases = [a.lower() for a in cmd_obj.aliases] if cmd_obj else []

            if name.lower() != query and query not in aliases:
                continue

            cat_emoji = lull.get(category, "📂")
            alias_str = (
                "  ".join(f"`{a}`" for a in cmd_obj.aliases)
                if cmd_obj and cmd_obj.aliases else "`none`"
            )

            layout = ui.LayoutView()
            card   = ui.Container()

            card.add_item(ui.TextDisplay(
                f"## {cat_emoji}  {name}\n"
                f"-# {category.capitalize()}  ·  {lulll.get(category, '')}"
            ))
            card.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            card.add_item(ui.TextDisplay(info["description"]))
            card.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
            card.add_item(ui.TextDisplay(
                f"**Usage**\n"
                f"```\n{prefix}{info['usage']}\n```\n\n"
                f"**Aliases:**  {alias_str}"
            ))
            card.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
            card.add_item(ui.TextDisplay(
                f"-# Requested by {ctx.author.display_name}"
            ))

            back_btn          = ui.Button(
                label     = f"{category.capitalize()}",
                emoji     = cat_emoji,
                style     = discord.ButtonStyle.grey,
                custom_id = f"cmdinfo_back_{category}",
            )
            home_btn          = ui.Button(
                label     = "",
                emoji     = "<:home:1496897554946855002>",
                style     = discord.ButtonStyle.secondary,
                custom_id = "cmdinfo_home",
            )

            async def _back(interaction: discord.Interaction, _cat=category):
                await interaction.response.edit_message(
                    view=HelpCategoryLayout(interaction.user, _cat, _get_prefix(interaction), bot)
                )

            async def _go_home(interaction: discord.Interaction):
                await interaction.response.edit_message(
                    view=HelpHomeLayout(interaction.user, _get_prefix(interaction), bot)
                )

            back_btn.callback = _back
            home_btn.callback = _go_home

            btn_row = ui.ActionRow()
            btn_row.add_item(back_btn)
            btn_row.add_item(home_btn)
            card.add_item(btn_row)

            layout.add_item(card)
            await ctx.reply(view=layout, mention_author=False)
            return

    await ctx.reply(
        embed=discord.Embed(
            description=f"{cross} `{query}` not found.",
            color=colour,
        ),
        mention_author=False,
    )






class HelpCog(commands.Cog, name="Help"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name        = "help",
        aliases     = ["h"],
        description = "Shows the help menu",
        usage       = "help [command/category]",
    )
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(query="A command or category name")
    async def help(self, ctx: commands.Context, *, query: str = None):
        prefix = _get_prefix(ctx)

        if query is None:
            await ctx.reply(view=HelpHomeLayout(ctx.author, prefix, self.bot), mention_author=False)
            return

        query = query.lower()
        if query in lulll:
            await ctx.reply(view=HelpCategoryLayout(ctx.author, query, prefix, self.bot), mention_author=False)
        else:
            await _send_command_info(ctx, query, self.bot)




async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))