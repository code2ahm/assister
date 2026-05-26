import discord
from discord.ext import commands
import re
from discord.ui import Button, View
from discord import app_commands
from utils.loads import *
from utils.variables import *
from utils.prefixes import *
from utils.checks import *
from utils.paginator import Ahm
from typing import Union

autoroleconfig = lautorole()

class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def getrole(ctx, rinput):
        if isinstance(rinput, discord.Role):
            return rinput

        menrole = re.match(r"<@&(\d+)>", rinput)
        if menrole:
            rid = int(menrole.group(1))
            return discord.utils.get(ctx.guild.roles, id=rid)
        
        elif rinput.isdigit():
            return discord.utils.get(ctx.guild.roles, id=int(rinput))
        
        return discord.utils.get(ctx.guild.roles, name=rinput)
    

    @commands.hybrid_group(name="autorole", invoke_without_command=True, description="Setup autorole for your server", usage="autorole", category="Autorole")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def autorole(self, ctx: commands.Context):
        ahm7 = self.bot.get_command('help')

        if ahm7:
            await ctx.invoke(ahm7, query='autorole')
        else:
            return

    @autorole.group(name="humans", invoke_without_command=True, description="Setup autorole for humans", usage="autorole humans", category="Autorole")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans(self, ctx: commands.Context):

        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix = guild_prefix(guild_id) if guild_id else '.'
        
        embed = discord.Embed(
            title="",
            description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                        f"{blnk}\n❓ Autorole help overview\n\n"
                        f"**Add autorole for humans**\n`{prefix}autorole humans add <role>`\n\n"
                        f"**Remove autorole for humans**\n`{prefix}autorole humans remove <role>`\n\n"
                        f"**Autorole configuration for humans**\n`{prefix}autorole humans show`\n\n"
                        f"**Reset autorole configuration for humans**\n`{prefix}autorole humans reset`\n{blnk}",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text=f"{ctx.bot.user.name} Autoroles", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        await ctx.reply(embed=embed, mention_author=False)

    @humans.command(name="add", description="Add a role to be assigned to human members on join", usage="autorole humans add <role>", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @app_commands.describe(role="Select the role to be added to members on joining.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans_add(self, ctx: commands.Context, *, role: discord.Role):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        if guild_id not in autoroleconfig:
            autoroleconfig[guild_id] = {'humans': [], 'bots': []}

        role = Autorole.getrole(ctx, role)
        if role:
            if role.permissions.administrator:
                embed = discord.Embed(
                    description=f"{cross} | Roles with administrative permissions cannot be added to autorole configuration!",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)
                return

            if role >= ctx.guild.me.top_role:
                embed = discord.Embed(
                    description=f"{cross} | Roles higher than or equal to my top role!",
                    color=colour
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            if role.id not in autoroleconfig[guild_id]['humans']:
                autoroleconfig[guild_id]['humans'].append(role.id)
                saveautorole(autoroleconfig)

                embed = discord.Embed(
                    description=f"{tick} Successfully added to humans autorole configuration\n{e_dot} {role.mention} will now be assigned to humans on joining",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                embed.set_footer(text=f"Added by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
                await ctx.reply(embed=embed, mention_author=False)
            else:
                embed = discord.Embed(
                    description=f"{grey} | Already configured as an autorole for humans!",
                    color=colour
                )
                await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                description=f"{cross} | Role not found or it is higher than my top role!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)

    @humans.command(name="remove", description="Remove a role from being assigned to human members", usage="autorole humans remove <role>", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @app_commands.describe(role="Select a role to remove from autorole humans configuration.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans_remove(self, ctx: commands.Context, *, role: discord.Role):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        if guild_id not in autoroleconfig or not autoroleconfig[guild_id]['humans']:
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for humans to remove!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        role = Autorole.getrole(ctx, role)
        if role and role.id in autoroleconfig[guild_id]['humans']:
            autoroleconfig[guild_id]['humans'].remove(role.id)
            saveautorole(autoroleconfig)

            embed = discord.Embed(
                description=f"{tick} Successfully removed from humans autorole configuration\n{e_dot} {role.mention} won't be to assigned humands on joining",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Removed by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                description=f"{cross} | This role is not configured as an autorole for humans!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)

    @humans.command(name="show", aliases=['view', 'list', 'config'], description="Show the list of roles assigned to humans on join", usage="autorole humans show", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans_show(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        if guild_id not in autoroleconfig or not autoroleconfig[guild_id]['humans']:
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for humans!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        rolemen = []
        for index, rid in enumerate(autoroleconfig[guild_id]['humans'], start=1):
            role = discord.utils.get(ctx.guild.roles, id=rid)
            if role:
                rolemen.append(f"{index}. {role.mention}")

        rshow = [rolemen[i:i + 10] for i in range(0, len(rolemen), 10)]

        pages = []
        for chunk in rshow:
            loda = "\n".join(chunk)
            embed = discord.Embed(
                description=f"{e_dot} **Autoroles configured for humans:**\n{loda}",
                color=colour
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"{ctx.bot.user.name} Autoroles", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @humans.command(name="reset", description="Reset all autoroles configured for humans", usage="autorole humans reset", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans_reset(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)

        if guild_id not in autoroleconfig or not autoroleconfig[guild_id]['humans']:
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for humans to reset!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            title="",
            description="❓ Are you sure you want to reset all autoroles configured for humans?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirmreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            autoroleconfig[guild_id]['humans'] = []
            saveautorole(autoroleconfig)

            ebd = discord.Embed(
                title="",
                description=f"{tick} Successfully reset all autoroles for humans",
                color=colour
            )
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            ebd.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=ebd, view=None)

        async def cancelreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            ebd = discord.Embed(
                title="",
                description=f"{grey} Action canceled",
                color=colour
            )
            await interaction.response.edit_message(embed=ebd, view=None)

        yoo.callback = confirmreset
        noo.callback = cancelreset

        await ctx.reply(embed=embed, mention_author=False, view=view)





    @autorole.group(name="bots", invoke_without_command=True, description="Setup autorole for bots", usage="autorole bots", category="Autorole")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix = guild_prefix(guild_id) if guild_id else '.'
        
        embed = discord.Embed(
            title="",
            description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                        f"{blnk}\n❓ Autorole help overview\n\n"
                        f"**Add autorole for bots**\n`{prefix}autorole bots add <role>`\n\n"
                        f"**Remove autorole for bots**\n`{prefix}autorole bots remove <role>`\n\n"
                        f"**Autorole configuration for bots**\n`{prefix}autorole bots show`\n\n"
                        f"**Reset autorole configuration for bots**\n`{prefix}autorole bots reset`\n{blnk}",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text=f"{ctx.bot.user.name} Autoroles", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        await ctx.reply(embed=embed, mention_author=False)

    @bots.command(name="add", description="Add a role to be assigned to bot members on join", usage="autorole bots add <role>", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @app_commands.describe(role="Select the role to be added to bots on joining.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots_add(self, ctx: commands.Context, *, role: discord.Role):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        if guild_id not in autoroleconfig:
            autoroleconfig[guild_id] = {'humans': [], 'bots': []}

        role = Autorole.getrole(ctx, role)
        if role:
            if role.permissions.administrator:
                embed = discord.Embed(
                    description=f"{cross} | Roles with administrative permissions cannot be added to autorole configuration!",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)
                return

            if role >= ctx.guild.me.top_role:
                embed = discord.Embed(
                    description=f"{cross} | Roles higher than or equal to my top role!",
                    color=colour
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            if role.id not in autoroleconfig[guild_id]['bots']:
                autoroleconfig[guild_id]['bots'].append(role.id)
                saveautorole(autoroleconfig)

                embed = discord.Embed(
                    description=f"{tick} Successfully added to bots autorole configuration\n{e_dot} {role.mention} will now be assigned to bots on joining",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                embed.set_footer(text=f"Added by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
                await ctx.reply(embed=embed, mention_author=False)
            else:
                embed = discord.Embed(
                    description=f"{grey} | Already configured as an autorole for bots!",
                    color=colour
                )
                await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                description=f"{cross} | Role not found or it is higher than my top role!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)

    @bots.command(name="remove", description="Remove a role from being assigned to bot members", usage="autorole bots remove <role>", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @app_commands.describe(role="Select a role to remove from autorole bots configuration.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots_remove(self, ctx: commands.Context, *, role: discord.Role):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        if guild_id not in autoroleconfig or not autoroleconfig[guild_id]['bots']:
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for bots to remove!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        role = Autorole.getrole(ctx, role)
        if role and role.id in autoroleconfig[guild_id]['bots']:
            autoroleconfig[guild_id]['bots'].remove(role.id)
            saveautorole(autoroleconfig)

            embed = discord.Embed(
                description=f"{tick} Successfully removed from bots autorole configuration\n{e_dot} {role.mention} won't be assigned to bots on joining",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Removed by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                description=f"{cross} | This role is not configured as an autorole for bots!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)

    @bots.command(name="show", aliases=['view', 'list', 'config'], description="Show the list of roles assigned to bots on join", usage="autorole bots show", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots_show(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        if guild_id not in autoroleconfig or not autoroleconfig[guild_id]['bots']:
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for bots!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        rolemen = []
        for index, rid in enumerate(autoroleconfig[guild_id]['bots'], start=1):
            role = discord.utils.get(ctx.guild.roles, id=rid)
            if role:
                rolemen.append(f"{index}. {role.mention}")

        pages = []
        for i in range(0, len(rolemen), 10):
            chunk = rolemen[i:i + 10]
            lodaa = "\n".join(chunk)
            embed = discord.Embed(
                description=f"{e_dot} **Autoroles configured for humans:**\n{lodaa}",
                color=colour
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"{ctx.bot.user.name} Autoroles", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            pages.append(embed)

        if not pages:
            embed = discord.Embed(
                description=f"{cross} | No roles assigned for bots!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        paginator = Ahm(pages)
        await paginator.start(ctx)

    @bots.command(name="reset", description="Reset all autoroles configured for bots", usage="autorole bots reset", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots_reset(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)

        if guild_id not in autoroleconfig or not autoroleconfig[guild_id]['bots']:
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for bots to reset!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            title="",
            description="❓ Are you sure you want to reset all autoroles configured for bots?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirmreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            autoroleconfig[guild_id]['bots'] = []
            saveautorole(autoroleconfig)
            embed = discord.Embed(
                description=f"{tick} | Successfully reset autoroles configured for bots!",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=embed, view=None)

        async def cancelreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return
            embed = discord.Embed(
                description=f"{cross} | Reset operation canceled!",
                color=colour
            )
            await interaction.response.edit_message(embed=embed, view=None)

        yoo.callback = confirmreset
        noo.callback = cancelreset

        await ctx.reply(embed=embed, view=view, mention_author=False)


    @autorole.command(name="config", aliases=['show', 'view', 'setup'], description="Show the autoroles configuration details", usage="autorole config", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def autoroleconfig(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in autoroleconfig:
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for this server!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        humans_count = len(autoroleconfig[guild_id].get('humans', []))
        bots_count = len(autoroleconfig[guild_id].get('bots', []))
        total_count = humans_count + bots_count

        ahm1 = discord.Embed(
            description=f"**{e_dot} Autoroles Configuration for `{ctx.guild.name}`**\n"
                        f"```js\nTotal    -   {total_count}\n"
                        f"Humans   -   {humans_count}\n"
                        f"Bots     -   {bots_count}```",
            color=colour
        )
        ahm1.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        ahm1.set_footer(text=f"{ctx.bot.user.name} Autoroles", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)

        role_mentions = []

        if 'humans' in autoroleconfig[guild_id]:
            for index, rid in enumerate(autoroleconfig[guild_id]['humans'], start=1):
                role = discord.utils.get(ctx.guild.roles, id=rid)
                if role:
                    role_mentions.append(f"`[{index}]` {role.mention} [Configured For Humans]")

        if 'bots' in autoroleconfig[guild_id]:
            for index, rid in enumerate(autoroleconfig[guild_id]['bots'], start=len(autoroleconfig[guild_id]['humans']) + 1):
                role = discord.utils.get(ctx.guild.roles, id=rid)
                if role:
                    role_mentions.append(f"`[{index}]` {role.mention} [Configured For Bots]")

        chunki = [role_mentions[i:i + 10] for i in range(0, len(role_mentions), 10)]

        pages = [ahm1]
        for chunk in chunki:
            rlist = "\n".join(chunk)
            embed = discord.Embed(
                description=f"{e_dot} **Autoroles Configuration for {ctx.guild.name}**\n\n{rlist}",
                color=colour
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"{ctx.bot.user.name} Autoroles", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @autorole.group(name="reset", description="Reset autoroles configuration", usage="autorole reset", category="Autorole")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def autorole_reset(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix = guild_prefix(guild_id) if guild_id else '.'

        embed = discord.Embed(
            title="",
            description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                        f"{blnk}\n❓ Autorole reset help overview\n\n"
                        f"**Reset autorole for all**\n`{prefix}autorole reset all`\n\n"
                        f"**Reset autorole for humans**\n`{prefix}autorole reset humans`\n\n"
                        f"**Reset autorole for bots**\n`{prefix}autorole reset bots`\n\n",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text=f"{ctx.bot.user.name} Autoroles", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        await ctx.reply(embed=embed, mention_author=False)


    @autorole_reset.command(name="all", description="Reset all autoroles (both humans and bots)", usage="autorole reset all")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reset_all(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)

        if guild_id not in autoroleconfig or not (autoroleconfig[guild_id].get('humans') or autoroleconfig[guild_id].get('bots')):
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for humans or bots to reset!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            title="",
            description="❓ Are you sure you want to reset **all autoroles configured** for both humans and bots?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirmreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            if guild_id in autoroleconfig:
                autoroleconfig[guild_id]['humans'] = []
                autoroleconfig[guild_id]['bots'] = []
                saveautorole(autoroleconfig)

            embed = discord.Embed(
                description=f"{tick} | Successfully reset **both humans' and bots'** autoroles!",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=embed, view=None)

        async def cancelreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            embed = discord.Embed(
                description=f"{cross} | Reset operation canceled!",
                color=colour
            )
            await interaction.response.edit_message(embed=embed, view=None)

        yoo.callback = confirmreset
        noo.callback = cancelreset
        await ctx.reply(embed=embed, view=view, mention_author=False)


    @autorole_reset.command(name="humans", description="Reset autoroles for humans only", usage="autorole reset humans")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reset_humans(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)

        if guild_id not in autoroleconfig or not autoroleconfig[guild_id].get('humans'):
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for humans to reset!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            title="",
            description="❓ Are you sure you want to reset **all autoroles configured** for humans?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirmreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            if guild_id in autoroleconfig:
                autoroleconfig[guild_id]['humans'] = [] 
                saveautorole(autoroleconfig) 
            embed = discord.Embed(
                description=f"{tick} | Successfully reset **humans'** autoroles!",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=embed, view=None)

        async def cancelreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            embed = discord.Embed(
                description=f"{cross} | Reset operation canceled!",
                color=colour
            )
            await interaction.response.edit_message(embed=embed, view=None)

        yoo.callback = confirmreset
        noo.callback = cancelreset
        await ctx.reply(embed=embed, view=view, mention_author=False)


    @autorole_reset.command(name="bots", description="Reset autoroles for bots only", usage="autorole reset bots")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reset_bots(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()
        guild_id = str(ctx.guild.id)

        if guild_id not in autoroleconfig or not autoroleconfig[guild_id].get('bots'):
            embed = discord.Embed(
                description=f"{cross} | No autoroles configured for bots to reset!",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            title="",
            description="❓ Are you sure you want to reset **all autoroles configured** for bots?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirmreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return
            if guild_id in autoroleconfig:
                autoroleconfig[guild_id]['bots'] = []
                saveautorole(autoroleconfig)

            embed = discord.Embed(
                description=f"{tick} | Successfully reset **bots'** autoroles!",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=embed, view=None)

        async def cancelreset(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            embed = discord.Embed(
                description=f"{cross} | Reset operation canceled!",
                color=colour
            )
            await interaction.response.edit_message(embed=embed, view=None)

        yoo.callback = confirmreset
        noo.callback = cancelreset

        await ctx.reply(embed=embed, view=view, mention_author=False)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)

        if guild_id in self.config:
            role_config = self.config[guild_id]

            if member.bot:
                for brid in role_config.get("bots", []):
                    brole = discord.utils.get(member.guild.roles, id=brid)
                    if brole:
                        await member.add_roles(brole)

            else:
                for hrid in role_config.get("humans", []):
                    hrole = discord.utils.get(member.guild.roles, id=hrid)
                    if hrole:
                        await member.add_roles(hrole)




    @commands.Cog.listener()
    async def on_member_join(self, member):

        guild_id = str(member.guild.id)
        if guild_id in autoroleconfig:
            ahmm = autoroleconfig[guild_id]

            if ahmm.get('humans') and not member.bot:
                for role_id in ahmm['humans']:
                    role = discord.utils.get(member.guild.roles, id=role_id)
                    if role:
                        await member.add_roles(role, reason="Assister Autorole | Humans")

            if ahmm.get('bots') and member.bot:
                for role_id in ahmm['bots']:
                    role = discord.utils.get(member.guild.roles, id=role_id)
                    if role:
                        await member.add_roles(role, reason="Assister Autorole | Bots")



async def setup(bot):
    await bot.add_cog(Autorole(bot))