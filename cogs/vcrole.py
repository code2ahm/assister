import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands
from utils.checks import *
from utils.loads import *
from utils.variables import *
from utils.prefixes import *

class Vcrole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="vcrole", aliases=['voicerole'], description="Manage voice channel roles", usage="vcrole <subcommand>")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def vcrole(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix = guild_prefix(guild_id) if guild_id else '.'

            embed = discord.Embed(
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ Vcrole help overview\n\n"
                            f"**View vcrole config for both**\n`{prefix}vcrole show`\n\n"
                            f"**Reset vcrole config for both**\n`{prefix}vcrole reset`\n\n"
                            f"**Add vcrole for humans**\n`{prefix}vcrole humans add <role>`\n\n"
                            f"**Remove vcrole for humans**\n`{prefix}vcrole humans remove <role>`\n\n"
                            f"**View vcrole configuration for humans**\n`{prefix}vcrole humans show`\n\n"
                            f"**Reset vcrole configuration for humans**\n`{prefix}vcrole humans reset`\n\n"
                            f"**Add vcrole for bots**\n`{prefix}vcrole bots add <role>`\n\n"
                            f"**Remove vcrole for bots**\n`{prefix}vcrole bots remove <role>`\n\n"
                            f"**View vcrole configuration for bots**\n`{prefix}vcrole bots show`\n\n"
                            f"**Reset vcrole configuration for bots**\n`{prefix}vcrole bots reset`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"{ctx.bot.user.name} Vcrole", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)

    @vcrole.group(name="humans", description="Configure vcrole for humans", usage="vcrole humans")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:

            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix = guild_prefix(guild_id) if guild_id else '.'

            embed = discord.Embed(
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ Vcrole help overview\n\n"
                            f"**Add vcrole for humans**\n`{prefix}vcrole humans add <role>`\n\n"
                            f"**Remove vcrole for humans**\n`{prefix}vcrole humans remove <role>`\n\n"
                            f"**View vcrole configuration for humans**\n`{prefix}vcrole humans show`\n\n"
                            f"**Reset vcrole configuration for humans**\n`{prefix}vcrole humans reset`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"{ctx.bot.user.name} Vcrole", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)


    @humans.command(name="add", description="Add a role for humans to be assigned in voice channels", usage="vcrole humans add <role>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(role="Select the role to add to vcroles")
    async def humans_add(self, ctx: commands.Context, role: discord.Role):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id not in data:
            data[guild_id] = {"humans": [], "bots": []}

        if len(data[guild_id]["humans"]) < 3:
            if role.id not in data[guild_id]["humans"]:
                data[guild_id]["humans"].append(role.id)
                savevcrole(data)

                embed = discord.Embed(
                    description=f"{tick} Successfully added {role.mention} to humans vcrole.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)

            else:
                embed = discord.Embed(
                    description=f"{grey} {role.mention} is already configured for humans.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)

        else:
            embed = discord.Embed(
                description=f"{grey} Only 3 roles can be configured.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @humans.command(name="remove", description="Remove a role for humans from voice channels", usage="vcrole humans remove <role>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(role="Select the role you want to remove from vcrole")
    async def humans_remove(self, ctx: commands.Context, role: discord.Role):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id in data and role.id in data[guild_id]["humans"]:
            data[guild_id]["humans"].remove(role.id)
            savevcrole(data)

            embed = discord.Embed(
                description=f"{tick} Successfully removed {role.mention} from humans vcrole.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        else:
            embed = discord.Embed(
                description=f"{grey} {role.mention} is not configured for humans.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @humans.command(name="show", description="Show the configured roles for humans", usage="vcrole humans show")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans_show(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id in data and data[guild_id]["humans"]:
            roles = [ctx.guild.get_role(int(role_id)) for role_id in data[guild_id]["humans"]]
            roles_mentions = "\n".join(f"`[{index + 1}]` {role.mention}" if role else f"`{index + 1}` (Role not found)" for index, role in enumerate(roles))

            embed = discord.Embed(
                description=f"{e_dot} Configured vcroles for humans:\n\n{roles_mentions}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        else:
            embed = discord.Embed(
                description=f"{grey} No roles configured for humans.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @humans.command(name="reset", description="Reset all configured roles for humans", usage="vcrole humans reset")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def humans_reset(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id not in data or not data[guild_id]["humans"]:
            embed = discord.Embed(
                description="No roles to reset for humans.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            description="❓ Are you sure you want to reset all configured roles for humans?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirm(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            data[guild_id]["humans"] = []
            savevcrole(data)

            ebd = discord.Embed(
                description=f"{tick} Successfully reset all configured roles for humans.",
                color=colour
            )
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            ebd.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=ebd, view=None)

        async def cancel(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            ebd = discord.Embed(
                description=f"{grey} Action canceled.",
                color=colour
            )
            await interaction.response.edit_message(embed=ebd, view=None)

        yoo.callback = confirm
        noo.callback = cancel

        await ctx.reply(embed=embed, view=view, mention_author=False)





    @vcrole.group(name="bots", description="Configure vcrole for bots", usage="vcrole bots <subcommand>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ Vcrole help overview\n\n"
                            f"**Add vcrole for bots**:\n `vcrole bots add <role>`\n\n"
                            f"**Remove vcrole for bots**:\n `vcrole bots remove <role>`\n\n"
                            f"**Show configured vcroles for bots**:\n `vcrole bots show`\n\n"
                            f"**Reset vcroles for bots**:\n `vcrole bots reset`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @bots.command(name="add", description="Add a role for bots to be assigned in voice channels", usage="vcrole bots add <role>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(role="Select the role you want to add to vcrole")
    async def bots_add(self, ctx: commands.Context, role: discord.Role):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id not in data:
            data[guild_id] = {"humans": [], "bots": []}

        if len(data[guild_id]["bots"]) < 3:
            if role.id not in data[guild_id]["bots"]:
                data[guild_id]["bots"].append(role.id)
                savevcrole(data)

                embed = discord.Embed(
                    description=f"{tick} Successfully added {role.mention} to bots vcrole.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)

            else:
                embed = discord.Embed(
                    description=f"{grey} {role.mention} is already configured for bots.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.reply(embed=embed, mention_author=False)

        else:
            embed = discord.Embed(
                description=f"{grey} You can only configure up to 3 roles for bots.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @bots.command(name="remove", description="Remove a role for bots from voice channels", usage="vcrole bots remove <role>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(role="Select the role you want to remove from vcrole")
    async def bots_remove(self, ctx: commands.Context, role: discord.Role):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id in data and role.id in data[guild_id]["bots"]:
            data[guild_id]["bots"].remove(role.id)
            savevcrole(data)

            embed = discord.Embed(
                description=f"{tick} Successfully removed {role.mention} from bots vcrole.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        else:
            embed = discord.Embed(
                description=f"{grey} {role.mention} is not configured for bots.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @bots.command(name="show", description="Show the configured roles for bots", usage="vcrole bots show")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots_show(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id in data and data[guild_id]["bots"]:
            roles = [ctx.guild.get_role(role_id) for role_id in data[guild_id]["bots"]]
            roles_mentions = "\n".join(f"`[{index + 1}]` {role.mention}" if role else f"`{index + 1}` (Role not found)" for index, role in enumerate(roles))

            embed = discord.Embed(
                description=f"{e_dot} Configured vcroles for bots:\n\n{roles_mentions}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        else:
            embed = discord.Embed(
                description=f"{grey} No roles configured for bots.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @bots.command(name="reset", description="Reset all configured roles for bots", usage="vcrole bots reset")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bots_reset(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id not in data or not data[guild_id]["bots"]:
            embed = discord.Embed(
                description="No roles to reset for bots.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            description="❓ Are you sure you want to reset all configured roles for bots?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirm(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            data[guild_id]["bots"] = []
            savevcrole(data)

            ebd = discord.Embed(
                description=f"{tick} Successfully reset all configured roles for bots.",
                color=colour
            )
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            ebd.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=ebd, view=None)

        async def cancel(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            ebd = discord.Embed(
                description="Action canceled.",
                color=colour
            )
            await interaction.response.edit_message(embed=ebd, view=None)

        yoo.callback = confirm
        noo.callback = cancel

        await ctx.reply(embed=embed, view=view, mention_author=False)




    @vcrole.command(name="show", aliases=['config', 'view', 'list'] , description="Show all configured vcroles for humans and bots", usage="vcrole show")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def vcrole_show(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        humanroles = []
        botroles = []

        if guild_id in data:
            if data[guild_id]["humans"]:
                humanroles = [ctx.guild.get_role(role_id) for role_id in data[guild_id]["humans"]]
                hroles = "\n".join(f"`[{index + 1}]` {role.mention}" if role else f"`{index + 1}` (Role not found)" for index, role in enumerate(humanroles))
            else:
                hroles = f"{grey} No roles configured for humans."

            if data[guild_id]["bots"]:
                botroles = [ctx.guild.get_role(role_id) for role_id in data[guild_id]["bots"]]
                broles = "\n".join(f"`[{index + 1}]` {role.mention}" if role else f"`{index + 1}` (Role not found)" for index, role in enumerate(botroles))
            else:
                broles = f"{grey} No roles configured for bots."

            embed = discord.Embed(
                description=f"{e_dot} **Configured vcroles for Humans:**\n\n{hroles}\n\n"
                            f"{e_dot} **Configured vcroles for Bots:**\n\n{broles}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                description=f"{grey} No vcroles are configured for either humans or bots.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @vcrole.command(name="reset", description="Reset vcroles for both humans and bots", usage="vcrole reset")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def vcrole_reset(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = lvcrole()

        if guild_id not in data or (not data[guild_id]["humans"] and not data[guild_id]["bots"]):
            embed = discord.Embed(
                description=f"{grey} No roles to reset for humans or bots.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            description="❓ Are you sure you want to reset **all** configured vcroles for humans and bots?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirm(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            data[guild_id]["humans"] = []
            data[guild_id]["bots"] = []
            savevcrole(data)

            ebd = discord.Embed(
                description=f"{tick} Successfully reset all configured vcroles for humans and bots.",
                color=colour
            )
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            ebd.set_footer(text=f"Reset by {ctx.author}", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await interaction.response.edit_message(embed=ebd, view=None)

        async def cancel(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            ebd = discord.Embed(
                description="Action canceled.",
                color=colour
            )
            await interaction.response.edit_message(embed=ebd, view=None)

        yoo.callback = confirm
        noo.callback = cancel

        await ctx.reply(embed=embed, view=view, mention_author=False)



    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = str(member.guild.id)
        data = lvcrole()

        if guild_id not in data:
            return

        human_roles = data[guild_id]["humans"]
        bot_roles = data[guild_id]["bots"]

        if before.channel != after.channel:
            if after.channel:
                if member.bot:
                    for role_id in bot_roles:
                        role = member.guild.get_role(role_id)
                        if role and role not in member.roles:
                            await member.add_roles(role)
                else:
                    for role_id in human_roles:
                        role = member.guild.get_role(role_id)
                        if role and role not in member.roles:
                            await member.add_roles(role)

            elif before.channel:
                if member.bot:
                    for role_id in bot_roles:
                        role = member.guild.get_role(role_id)
                        if role in member.roles:
                            await member.remove_roles(role)
                else:
                    for role_id in human_roles:
                        role = member.guild.get_role(role_id)
                        if role in member.roles:
                            await member.remove_roles(role)


async def setup(bot):
    await bot.add_cog(Vcrole(bot))