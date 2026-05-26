import discord
import re
from utils.loads import *
from utils.variables import *
from utils.checks import *
from utils.prefixes import *
from utils.paginator import Ahm
from discord.ui import Button, View
from discord import app_commands

class Extra(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ard = ard

    def savear(self):
        saveard()
    def saveareactd(self):
        saveareactd()


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        guild_id = str(message.guild.id) if message.guild else None
        if guild_id and guild_id in ard:
            for trigger, response in ard[guild_id].items():
                if re.search(r'\b' + re.escape(trigger) + r'\b', message.content, re.IGNORECASE):
                    if message.channel.permissions_for(message.guild.me).read_message_history:
                        try:
                            gand = await message.channel.fetch_message(message.id)
                            await message.channel.send(response, reference=gand, mention_author=False)
                        except discord.HTTPException as e:
                            print(e)
                    else:
                        return
                    break

        if guild_id and guild_id in areactd:
            for trigger, emoji in areactd[guild_id].items():
                if trigger in message.content:
                    try:
                        await message.add_reaction(emoji)
                    except discord.HTTPException as e:
                        print(e)
                    break




    @commands.hybrid_command(aliases=['pr', 'badge', 'badges'], name="profile", description="View the profile of a user.", usage="profile [user]", category="Extra")
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(user="Select the user you want to view badges for.")
    async def profile(self, ctx: commands.Context, user: discord.User = None):
        user = user or ctx.author
        
        bionic = 1497166042894700637
        randiz = {
            "<:crown:1497545970714542162> Owner": 1497193237343899739,
            "<:Red_Crown_1:1497546159353368667> Founder": 1497193257489399860,
            "🏳️‍⚧️ LGBTQ+ Supporter": 1497193249025294426,
            "<:bionic_g_VerifiedBotDeveloper:1261552705697091697> Developer": 1497605451196661911,
            "<:admin:1497546447778873384> Admin": 1497193234013622384,
            "<:hypesquad_events:1497546705359343747> Moderator": 1497193230507442247,
            "<:break_heart:1497546835089162371> Admirer": 1497193225398648843,
            "<:early:1497546978081505391> Supporter": 1497193210919911426,
            "<:Discord_partner:1497547092166447225> Partner": 1497193207652679781,
            "<:members:1497547178309058682> Member": 1497193204179533895
        }

        guild = self.bot.get_guild(bionic)
        if guild is None:
            return

        member = guild.get_member(user.id)
        if not member:
            ll = discord.Embed(
                description=f"❓ **{user.name}** must be in **{support_server}** to view their profile.\n"
                            f"<:fn_verify:1497547412820983938> Join now to get a badge",
                color=colour
            )
            ll.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=ll, mention_author=False)
            return

        embed = discord.Embed(
            title=f"",
            description=f"",
            color=colour
        )
        embed.set_author(name=f"{ctx.bot.user.name} Profile", icon_url=ctx.bot.user.avatar.url)
        embed.set_footer(text=f"{ctx.author}'s {ctx.bot.user.name} profile", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

        rtitle = []

        for title, rid in randiz.items():
            if rid in [role.id for role in member.roles]:
                rtitle.append(title)
        if not rtitle:
            rtitle.append("<:members:1497547178309058682> Member")

        chutt = "\n".join([f"**{title}**" for title in rtitle])
        embed.description += "\n" + chutt
        embed.description += "\n\nYou're a valued member of the community\n"
        embed.description += "Thank you for being part of the community!\n"
        await ctx.reply(embed=embed, mention_author=False)





    @commands.hybrid_group(name="autoresponder", aliases=["ar"], description="Manage autoresponders", usage="ar" , category="Extra", invoke_without_command=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def _autoresponder(self, ctx: commands.Context):

        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix = guild_prefix(guild_id) if guild_id else '.'
        
        embed = discord.Embed(
            title="",
            description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                        f"{blnk}\n❓ Autoresponder help overview\n\n"
                        f"**Add autoresponder:**\n`{prefix}ar add <trigger> <autoresponse>`\n\n"
                        f"**Remove autoresponder:**\n`{prefix}ar remove <trigger> <autoresponse>`\n\n"
                        f"**View autoresponder:**\n`{prefix}ar list`\n\n"
                        f"**❗ Note: To add line breaks, use ```\\n```**{blnk}",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text=f"{ctx.bot.user.name} Autoresponder", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        await ctx.reply(embed=embed, mention_author=False)

    @_autoresponder.command(name="add", description="Adds an autoresponder trigger", usage="ar add <trigger> <autoresponse>", category="Extra")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(trigger="Set the trigger you want to add autoresponse for.", autoresponse="Set autoresponse message for trigger text.")
    async def add_autoresponder(self, ctx, trigger: str, *, autoresponse: str):
        guild_id = str(ctx.guild.id)

        self.ard.setdefault(guild_id, {})
        trigger = trigger.strip()
        autoresponse = autoresponse.strip().replace("\\n", "\n")

        if trigger in self.ard[guild_id]:
            embed = discord.Embed(
                title="",
                description=f"❓ `{trigger}` already has an autoresponse.\n{e_dot} Choose a different trigger.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        self.ard[guild_id][trigger] = autoresponse
        self.savear()

        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully added autoresponder for **{trigger}**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @_autoresponder.command(name="remove", description="Removes an autoresponder trigger", usage="ar remove <trigger>", category="Extra")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(trigger="Set the trigger you want to add autoresponse for.")
    async def remove_autoresponder(self, ctx, trigger: str):

        guild_id = str(ctx.guild.id)
        if guild_id in self.ard and trigger in self.ard[guild_id]:
            del self.ard[guild_id][trigger]
            self.savear()

            embed = discord.Embed(
                title="",
                description=f"{tick} | Successfully removed autoresponder for **{trigger}**.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                title="",
                description=f"❓ No autoresponder found for `{trigger}`",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)


    @_autoresponder.command(name="list", aliases=['show', 'config'], description="Lists all autoresponders", usage="ar list", category="Extra")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def list_autoresponders(self, ctx: commands.Context):

        guild_id = str(ctx.guild.id)
        if guild_id in self.ard and self.ard[guild_id]:
            atlist = [f"`[{index + 1}]`   **{trigger}** : {response}" for index, (trigger, response) in enumerate(self.ard[guild_id].items())]

            arss = [atlist[i:i + 5] for i in range(0, len(atlist), 5)]

            pages = []
            total_pages = len(arss)
            for page_num, arpage in enumerate(arss, start=1):
                embed = discord.Embed(
                    title="",
                    description=f"**{e_dot} Autoresponders for {ctx.guild.name}\n{e_dot} Total `[{len(atlist)}]` Autoresponders:**\n\n" + "\n ".join(arpage),
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                embed.set_footer(text=f"{ctx.bot.user.name} Autoresponding • Page {page_num}/{total_pages}", icon_url=ctx.bot.user.avatar)
                pages.append(embed)

            paginator = Ahm(pages)
            await paginator.start(ctx)

        else:
            embed = discord.Embed(
                title="",
                description=f"❓ No autoresponders have been set in **{ctx.guild.name}** yet.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

    @_autoresponder.command(name="reset", description="Reset all autoresponders", usage="ar reset", category="Extra")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reset_autoresponders(self, ctx: commands.Context):
        
        embed = discord.Embed(
            title="",
            description="❓ Are you sure you want to reset all autoresponders?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yob = Button(label="Yes", style=discord.ButtonStyle.green)
        nob = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        
        view.add_item(yob)
        view.add_item(nob)

        async def yoo(interaction: discord.Interaction):

            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            guild_id = str(ctx.guild.id)
            if guild_id in self.ard:
                self.ard[guild_id].clear()
                self.savear()

                ebd = discord.Embed(
                    title="",
                    description=f"{tick} Successfully reset all autoresponders",
                    color=colour
                )
                ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await interaction.response.edit_message(embed=ebd, view=None)
            else:
                ebd = discord.Embed(
                    title="",
                    description=f"{grey} No autoresponders found to reset.",
                    color=colour
                )
                await interaction.response.edit_message(embed=ebd, view=None)

        async def noo(interaction: discord.Interaction):

            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return
            
            anhhh = discord.Embed(
                title="",
                description=f"{cross} Action canceled. No changes made.",
                color=colour
            )
            await interaction.response.edit_message(embed=anhhh, view=None)

        yob.callback = yoo
        nob.callback = noo
        await ctx.reply(embed=embed, mention_author=False, view=view)



    @commands.hybrid_group(name="autoreact", aliases=['areact', 'art'] ,description="Manage autoreactions", usage="autoreact", invoke_without_command=True, category="Extra")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def autoreact(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        prefix = guild_prefix(guild_id) if guild_id else '.'

        embed = discord.Embed(
            title="",
            description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                        f"{blnk}\n❓ Autoreact help overview\n\n"
                        f"**Add autoreaction:**\n`{prefix}autoreact add <trigger> <emoji>`\n\n"
                        f"**Remove autoreaction:**\n`{prefix}autoreact remove <trigger>`\n\n"
                        f"**View autoreactions:**\n`{prefix}autoreact list`\n\n"
                        f"**Reset autoreactions:**\n`{prefix}autoreact reset`\n\n"
                        f"**❗ Note: Use emoji codes like `:smile:` or custom emojis as well.**\n{blnk}",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text=f"{ctx.bot.user.name} Autoreact", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        await ctx.reply(embed=embed, mention_author=False)

    @autoreact.command(name="add", description="Add an autoreaction for a trigger", usage="autoreact add <trigger> <emoji>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(trigger="Set the trigger text to react to.", emoji="The emoji that will react to the trigger.")
    async def add_autoreact(self, ctx, trigger: str, emoji: str):
        guild_id = str(ctx.guild.id)

        areactd.setdefault(guild_id, {})

        trigger = trigger.strip()
        emoji = emoji.strip()

        if trigger in areactd[guild_id]:
            embed = discord.Embed(
                title="",
                description=f"❓ `{trigger}` already has an autoreaction.\n{e_dot} Choose a different trigger.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        areactd[guild_id][trigger] = emoji
        self.saveareactd()

        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully added autoreaction for **{trigger}** with emoji **{emoji}**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @autoreact.command(name="remove", description="Remove an autoreaction for a trigger", usage="autoreact remove <trigger>", category="Extra")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(trigger="The trigger you want to remove the autoreaction for.")
    async def remove_autoreact(self, ctx, trigger: str):
        guild_id = str(ctx.guild.id)

        if guild_id in areactd and trigger in areactd[guild_id]:
            del areactd[guild_id][trigger]
            self.saveareactd()

            embed = discord.Embed(
                title="",
                description=f"{tick} | Successfully removed autoreaction for **{trigger}**.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                title="",
                description=f"❓ No autoreaction found for `{trigger}`",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

    @autoreact.command(name="list", aliases=['show', 'config'], description="List all autoreactions", usage="autoreact list", category="Extra")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def list_autoreacts(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)

        if guild_id in areactd and areactd[guild_id]:
            arlist = [f"`[{index + 1}]`   **{trigger}** : {emoji}" for index, (trigger, emoji) in enumerate(areactd[guild_id].items())]

            arpages = [arlist[i:i + 5] for i in range(0, len(arlist), 5)] 

            pages = []
            total_pages = len(arpages)
            for page_num, arpage in enumerate(arpages, start=1):
                embed = discord.Embed(
                    title="",
                    description=f"**{e_dot} Autoreactions for {ctx.guild.name}\n{e_dot} Total `[{len(arlist)}]` Autoreactions:**\n\n" + "\n ".join(arpage),
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                embed.set_footer(text=f"{ctx.bot.user.name} Autoreacting • Page {page_num}/{total_pages}", icon_url=ctx.bot.user.avatar)
                pages.append(embed)

            paginator = Ahm(pages)
            await paginator.start(ctx)

        else:
            embed = discord.Embed(
                title="",
                description=f"❓ No autoreactions have been set in **{ctx.guild.name}** yet.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

    @autoreact.command(name="reset", description="Reset all autoreactions", usage="autoreact reset", category="Extra")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reset_autoreactions(self, ctx: commands.Context):
        embed = discord.Embed(
            title="",
            description="❓ Are you sure you want to reset all autoreactions?\n❗ **This action cannot be undone.**",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        yob = Button(label="Yes", style=discord.ButtonStyle.green)
        nob = Button(label="No", style=discord.ButtonStyle.danger)

        view = View(timeout=60)
        view.add_item(yob)
        view.add_item(nob)

        async def yoo(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            guild_id = str(ctx.guild.id)
            if guild_id in areactd:
                areactd[guild_id].clear()
                self.saveareactd()

                ebd = discord.Embed(
                    title="",
                    description=f"{tick} Successfully reset all autoreactions.",
                    color=colour
                )
                ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await interaction.response.edit_message(embed=ebd, view=None)
            else:
                ebd = discord.Embed(
                    title="",
                    description=f"{grey} No autoreactions found to reset.",
                    color=colour
                )
                await interaction.response.edit_message(embed=ebd, view=None)

        async def noo(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            anhhh = discord.Embed(
                title="",
                description=f"{cross} Action canceled. No changes made.",
                color=colour
            )
            await interaction.response.edit_message(embed=anhhh, view=None)

        yob.callback = yoo
        nob.callback = noo
        await ctx.reply(embed=embed, mention_author=False, view=view)



async def setup(bot):
    await bot.add_cog(Extra(bot))