import discord
from discord.ui import View, Button
from typing import List, Union
from discord.ext import commands
import asyncio

class Ahm(View):
    def __init__(self, pages: List[Union[str, discord.Embed]], timeout: int = 60):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.message = None
        self.ctx = None
        self.update_buttons()

    def update_buttons(self):

        self.children[0].disabled = self.current_page == 0
        self.children[2].disabled = self.current_page == len(self.pages) - 1

    async def update_message(self):
        page = self.pages[self.current_page]

        if isinstance(page, discord.Embed):
            await self.message.edit(embed=page, content=None, view=self)

        elif isinstance(page, discord.ui.View):
            await self.message.edit(content=None, embed=None, view=page)

        else:
            await self.message.edit(content=page, embed=None, view=self)


    @discord.ui.button(emoji="<:left:1496888475922731062>", style=discord.ButtonStyle.green, row=0)
    async def left(self, interaction: discord.Interaction, button: Button):

        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Run the command by yourself.", ephemeral=True)
            return

        self.current_page -= 1
        self.update_buttons()
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(emoji="<:reacttrash:1496888674539933827>", style=discord.ButtonStyle.danger, row=0)
    async def close(self, interaction: discord.Interaction, button: Button):

        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Run the command by yourself.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(emoji="<:right:1496889463564009565>", style=discord.ButtonStyle.green, row=0)
    async def right(self, interaction: discord.Interaction, button: Button):

        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Run the command by yourself.", ephemeral=True)
            return

        self.current_page += 1
        self.update_buttons()
        await self.update_message()
        await interaction.response.defer()

    async def start(self, ctx: commands.Context):
        self.ctx = ctx

        if len(self.pages) == 0:
            raise ValueError("L pe tu")

        first = self.pages[0]

        if isinstance(first, discord.Embed):
            self.message = await ctx.reply(embed=first, view=self, mention_author=False)

        elif isinstance(first, discord.ui.View):
            self.message = await ctx.reply(view=first, mention_author=False)

        else:
            self.message = await ctx.reply(content=first, view=self, mention_author=False)
            

class YoNo(View):
    def __init__(self, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.result = None

    async def on_timeout(self):
        if self.result is None:
            self.result = False

    async def confirm(self, interaction: discord.Interaction):
        self.result = True
        await interaction.response.defer()

    async def cancel(self, interaction: discord.Interaction):
        self.result = False
        await interaction.response.defer()

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
            return
        await self.confirm(interaction)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
            return
        await self.cancel(interaction)

    async def waitt(self):
        while self.result is None:
            await asyncio.sleep(0.1)
        return self.result