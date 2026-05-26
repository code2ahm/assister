import discord
import time
import psutil
from discord.ext import commands
from utils.checks import *
from utils.variables import *
from utils.prefixes import *
from utils.helplund import lul
import datetime
from datetime import datetime, timedelta
import asyncio, aiohttp, re
import platform
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from discord import app_commands
from deep_translator import GoogleTranslator


startup_time = datetime.now()

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(description="Check the bot's API latency", usage="ping", category="General")
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def ping(self, ctx: commands.Context):

        msg = await ctx.reply("<a:loading:1497092377549209651> | Calculating ping...", mention_author=False)
        latency = round(ctx.bot.latency * 1000)

        lund = f"<:bionic_g_uptime:1261552718464417812> API Latency: {latency}ms"
        await msg.edit(content=lund)


    @commands.hybrid_command(description="Check the bot's uptime", usage="uptime", category="General")
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def uptime(self, ctx: commands.Context):

        uptime = datetime.now() - startup_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        await ctx.reply(f"<a:uptime:1497475329512439960> **{days} days, {hours} hours, {minutes} minutes, {seconds} seconds**", mention_author=False)



    @commands.hybrid_command(aliases=['prefixset'], description="Change the server's command prefix.", usage="setprefix <prefix>", category="General")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(prefix="Type the prefix you want to set for bot.")
    async def setprefix(self, ctx: commands.Context, prefix: str):

        guild_id = str(ctx.guild.id) if ctx.guild else None

        prefixes[guild_id] = prefix
        save_prefixes(prefixes)

        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully changed the prefix for **`{ctx.guild.name}`**\n{e_dot} New prefix: `{prefix}`",
            color=colour
        )
        embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(description="Displays bot's information", usage="about", category="General")
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def about(self, ctx: commands.Context):

        tsvs = len(self.bot.guilds)
        tmbs = sum(guild.member_count for guild in self.bot.guilds)
        ttc = sum(len(guild.channels) for guild in self.bot.guilds)
        tvc = sum(len(guild.voice_channels) for guild in self.bot.guilds)
        dcversion = discord.__version__
        pyversion = platform.python_version()

        # felix_link = "https://discord.com/users/921802010725060648"
        # felix = f"[felixji]({felix_link})"

        # gamer_link = "https://discord.com/users/1177645335229767680"
        # gamer = f"[bigbadgameryt]({gamer_link})"

        worsee = "https://discord.com/users/1217734448947134514"
        ahm = f"[worse4sure]({worsee})"

        # developer_team = [
        #     (f"andrewthehulk", "https://discord.com/users/1059075408668151870"),
        #     (f"eehan.barcha", "https://discord.com/users/1086331210407612468")
        # ]
        # developer_team_hyperlink = '\n'.join([f"{e_dot} [{name}]({url})" for name, url in developer_team])

        # supporter_team = [
        #     (f"santa.in", "https://discord.com/users/1033578028246257685"),
        #     (f"worse4sure", "https://discord.com/users/1217734448947134514")
        # ]
        # supporter_team_hyperlink = '\n'.join([f"{e_dot} [{name}]({url})" for name, url in supporter_team])

        assister_team_button = discord.ui.Button(style=discord.ButtonStyle.green, label="@assister", emoji="<a:bionic_g_settings:1261552651347427338>")
        websitee = discord.ui.Button(style=discord.ButtonStyle.link, label="Website", url="https://assisterbot.xyz")
        ahm_url = discord.ui.Button(style=discord.ButtonStyle.link, label="Developer", url="https://github.com/code2ahm")
        support_button = discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=support_server_link)
        invite_button = discord.ui.Button(style=discord.ButtonStyle.link, label="Invite Me", url="https://discord.com/oauth2/authorize?client_id=1496794996228231229&permissions=8&integration_type=0&scope=bot")

        loda = discord.ui.View()
        loda.add_item(assister_team_button)
        loda.add_item(websitee)
        loda.add_item(ahm_url)
        loda.add_item(invite_button)
        loda.add_item(support_button)

        embed = discord.Embed(
            title="",
            description=(
                f"## Description:\n**Assister** is a multi-tasking & user-friendly discord bot that covers antinuke, automod, autoroles, autoresponding, moderation, utility, logging, welcomer, giveaway hosting, game commands for community engagement & much more!\n"

                f"## Bot Stat(s):\n**Total Servers:** {tsvs} Guilds\n"
                f"**Total Users:** {tmbs} Users\n"
                f"**Total Channels:** {ttc + tvc} Channels\n"
                
                f"## Link(s):\n**[Privacy @assister](https://assisterbot.xyz/pp)**\n"
                f"**[Terms @assister](https://assisterbot.xyz/tos)**\n"
                f"**[Vote @assister](https://top.gg/bot/1496794996228231229/vote)**\n"

                f"## System Info:\n**discord.py Version:** {dcversion}\n"
                f"**py Version:** {pyversion}"
            ),
            color=colour
        )

        embed.set_thumbnail(url=str(ctx.bot.user.avatar.url))
        embed.set_author(name="", icon_url=ctx.bot.user.avatar.url)

        await ctx.reply(embed=embed, view=loda, mention_author=False)

        async def assister_team_callback(interaction):
            tebd = discord.Embed(
                title="",
                description=(
                    f"**The Assister bot is developed and maintained by a talented and passionate team committed to providing a seamless experience for users. Below is a list of the incredible individuals who contribute to the bot's development and community.**\n"
                    # f"## <a:crown:1309804524201967619> Owner(s):\n **{e_dot} {gamer}\n{e_dot} {felix}**\n"
                    # f"## <:staff:1246779492207165450> Team(s):\n **{developer_team_hyperlink}**\n"
                    # f"## <:early_supporter:1246779721929330770> Supporter(s):\n **{supporter_team_hyperlink}**\n"
                    f"## <:bionic_g_VerifiedBotDeveloper:1261552705697091697> Developer(s):\n {ahm}"
                ),
                color=colour
            )
            tebd.set_thumbnail(url=str(ctx.bot.user.avatar.url))
            tebd.set_author(name="Assister Team", icon_url=ctx.bot.user.avatar.url)

            home_button = discord.ui.Button(style=discord.ButtonStyle.green, label="", emoji="<:home:1496897554946855002>")
            team_view = discord.ui.View()

            team_view.add_item(home_button)

            await interaction.response.edit_message(embed=tebd, view=team_view)
            async def home_callback(interaction):
                await interaction.response.edit_message(embed=embed, view=loda)

            home_button.callback = home_callback
        assister_team_button.callback = assister_team_callback


    @commands.hybrid_command(name="botinfo", description="Shows the bot statistics", aliases=['bi', 'stats', 'st'], usage="bi", category="General")
    @bled()
    @commands.cooldown(1, 10 , commands.BucketType.user)
    async def botinfo(self, ctx: commands.Context):
        
        iebd = discord.Embed(
            title="",
            description="**<a:bionic_g_Loading:1261552738467188758> | Fetching Assister Statistics**",
            color=colour
        )
        message = await ctx.reply(embed=iebd, mention_author=False)
        
        tsvs = len(self.bot.guilds)
        tmbs = sum(guild.member_count for guild in self.bot.guilds)
        ttc = sum(len(guild.channels) for guild in self.bot.guilds)
        tvc = sum(len(guild.voice_channels) for guild in self.bot.guilds)
        channels = sum(len(guild.channels) for guild in self.bot.guilds)


        current_time = datetime.now()
        uptime = current_time - startup_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptimee = f"{days} d, {hours} h, {minutes} m, {seconds} s"

        cpu = psutil.cpu_percent(interval=1)
        musage = psutil.virtual_memory().percent

        cmds = len(self.bot.commands)
        subcmds = 0
        for command in self.bot.commands:
            if hasattr(command, 'commands'):
                subcmds += len(command.commands)
        slash = len([command for command in self.bot.tree.get_commands()])
        cmmds = sum(len(commands) for commands in lul.values())
        tcmds = len(self.bot.commands)

        ping = f"{round(self.bot.latency * 1000)} ms"
        start = time.time() 
        end = time.time()
        latency = round((end - start) * 1000, 2)
        dcversion = discord.__version__
        pyversion = platform.python_version()

        embed = discord.Embed(
            title="",
            description="**Assister** is a multi-tasking & user friendly discord bot that covers up **antinuke**, **automod**, **autoroles**, **autoresponding**, moderation, utility, **logging**, welcomer, giveaways hosting, game commands for community engagement & much more. Add **Assister** now to make your discord experience better!",
            color=colour
        )

        embed.add_field(name=f"<a:bionic_g_Loading:1261552738467188758>  Stat(s)", value=f"```py\nTotal Guilds: {tsvs}\nTotal Users: {tmbs}\nTotal Channels: {channels}\nText Channels: {ttc}\nVoice Channels: {tvc}\nTotal Commands: {cmmds}```")
        embed.add_field(name=f"<a:bionic_g_settings:1261552651347427338> System Info", value=f"```py\nPing: {ping}\nUptime: {uptimee}\nCPU Usage: {cpu}%\nMemory Usage: {musage}%\nWebhook Latency: {latency} ms\ndiscord.py Version: {dcversion}\nPy Version: {pyversion}```", inline=False)

        embed.set_author(name=f"{self.bot.user.name}'s information" , icon_url=self.bot.user.avatar.url)
        if ctx.author.avatar:
            embed.set_footer(text=f"Requested By {ctx.author}" , icon_url=ctx.author.avatar.url)
        else:
            embed.set_footer(text=f"Requested By {ctx.author}" , icon_url=ctx.author.default_avatar.url)

        lund = self.bot.user.id
        banneri = await self.bot.fetch_user(lund)
        embed.set_image(url=banneri.banner if banneri.banner else None)
        
        await message.edit(embed=embed)


    @commands.hybrid_command(description="Vote links for assister", aliases=['votelink'], usage="vote", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def vote(self, ctx: commands.Context):

        embed = discord.Embed(
            title="",
            description="<:topgg:1497301724606496960> | Vote Assister on [top.gg](https://top.gg/bot/1496794996228231229/vote)", # \n<:discordbotlist:1264584062123638805> | Vote Assister on [Discord Bot List](https://discordbotlist.com/bots/assister)",
            color=colour
        )
        topgg_button = discord.ui.Button(style=discord.ButtonStyle.link, label="top.gg", url="https://top.gg/bot/1496794996228231229/vote")
        # botlist_button = discord.ui.Button(style=discord.ButtonStyle.link, label="Bot List", url="https://discordbotlist.com/bots/assister")

        kalichut = discord.ui.View()
        kalichut.add_item(topgg_button)
        #kalichut.add_item(botlist_button)

        await ctx.reply(embed=embed, view=kalichut, mention_author=False)



    @commands.hybrid_command(aliases=['inv'], description="Invites link of bots & support server", usage="invite", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def invite(self, ctx: commands.Context):

        assister_inv = "https://discord.com/oauth2/authorize?client_id=1496794996228231229&permissions=8&integration_type=0&scope=bot"

        support_button = discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=support_server_link)
        invite_button = discord.ui.Button(style=discord.ButtonStyle.link, label="Invite Assister", url=assister_inv)

        blackchut = discord.ui.View()
        blackchut.add_item(support_button)
        blackchut.add_item(invite_button)

        ed = discord.Embed(
            title="",
            description="",
            color=colour
        )
        ed.set_thumbnail(url=self.bot.user.avatar.url)
        ed.add_field(name="<:link:1497164960621400064> Links For Assister" , value=f"→  [Invite Assister]({assister_inv})\n→  [Join Support Server]({support_server_link})", inline=False)
        ed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar.url else ctx.author.default_avatar.url)

        await ctx.reply(embed=ed, view=blackchut, mention_author=False)


    @commands.hybrid_command(name='github', aliases=['git'], description="Shows top 5 GitHub repositories", usage="github <query>", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(query="Provide the query that you want to search on github.")
    async def github(self, ctx: commands.Context, *, query: str):

        iebd = discord.Embed(
            title="",
            description=f"**<a:bionic_g_Loading:1261552738467188758> | Looking for repositories matching '{query}'**",
            color=colour
        )
        msg = await ctx.reply(embed=iebd, mention_author=False)

        try:
            response = requests.get(git, params={'q': query})
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            await msg.edit(content=f"Error: Unable to fetch data from GitHub!", embed=None)
            return

        if 'items' not in data or not data['items']:
            await msg.edit(embed=discord.Embed(title="", description=f"**{cross} | No result found for '{query}'**", color=colour))
            return

        embeds = []
        cebd = discord.Embed(title=f"", color=colour)
        if ctx.author.avatar:
            cebd.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar.url)
        else:
            cebd.set_author(name=f"{ctx.author}", icon_url=ctx.author.default_avatar.url)
        cebd.set_footer(text="Only top 5 repositories are displayed")
        
        tlength = 0
        for item in data['items'][:5]:
            repo_name = item['full_name']
            repo_url = item['html_url']
            repo_description = item['description'] or "No description provided."
            repo_stars = item['stargazers_count']

            if len(repo_description) > 800:
                repo_description = repo_description[:797] + "..."

            fvalue = (
                f"{limkkk} **[{repo_name}]({repo_url})**\n"
                f"**Description:** {repo_description}\n"
                f"**Stars:** {repo_stars}"
            )

            if tlength + len(fvalue) > 6000 or len(cebd.fields) >= 25:
                embeds.append(cebd)
                cebd = discord.Embed(title=f"", color=colour)
                cebd.set_footer(text="Continued...")
                tlength = 0

            if len(fvalue) > 1024:
                fvalue = fvalue[:1021] + "..."

            cebd.add_field(name=f"", value=fvalue, inline=False)
            tlength += len(fvalue)
        if cebd.fields:
            embeds.append(cebd)

        await msg.edit(embed=embeds[0])
        for embed in embeds[1:]:
            await ctx.send(embed=embed)


    @commands.hybrid_command(aliases=['vi', 'vci'], description="Shows the voice channels information", usage="vci <query>", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(vc="Select the voice channel you want to view details for.")
    async def vcinfo(self, ctx: commands.Context, vc: discord.VoiceChannel):

        server = ctx.guild
        category = vc.category.name if vc.category else None
        
        members_count = len(vc.members)
        
        member_info = []
        for member in vc.members:
            member_status = "🔇 | Muted" if member.voice.self_mute else "<:voice:1496896175864025118> | Unmuted"
            if member.voice.self_stream:
                member_status += " : <:streaming:1497212447403151520> | Streaming"
            member_info.append(f"{e_dot} <@{member.id}> | {member_status}")

        embed = discord.Embed(title=f"", color=colour)
        if server.icon:
            embed.set_thumbnail(url=server.icon.url)
        embed.add_field(name="Vc Name:", value=f"{vc.name}", inline=False)
        embed.add_field(name="Vc Id:", value=f"{vc.id}", inline=False)
        embed.add_field(name="Bitrate:", value=f"{vc.bitrate / 1000} kbps", inline=False)
        embed.add_field(name="Mention:", value=f"{vc.mention}", inline=False)
        embed.add_field(name="Category:", value=f"{category}", inline=False)
        embed.add_field(name="Members Connected:", value=f"{e_dot} {members_count}", inline=False)
        
        if members_count > 0:
            embed.add_field(name="Members Connected", value="\n".join(member_info), inline=False)
        
        await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(aliases=['channelinfo'], description="Shows the text channel information", usage="textinfo <channel>", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Select the channel you want to view details for.")
    async def textinfo(self, ctx: commands.Context, channel: discord.TextChannel):
        
        guild = ctx.guild
        category = channel.category.name if channel.category else None

        members_count = sum(1 for member in guild.members if channel.permissions_for(member).read_messages)
        
        embed = discord.Embed(title=f"", color=colour)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Channel name:", value=f"{channel.name}", inline=False)
        embed.add_field(name="Channel Id:", value=f"{channel.id}", inline=False)
        embed.add_field(name="Mention:", value=f"{channel.mention}", inline=False)
        embed.add_field(name="Category:", value=f"{category}", inline=False)
        embed.add_field(name="Members with Access:", value=f"{members_count}", inline=False)
        
        if channel.topic:
            embed.add_field(name="Channel Topic:", value=f"{channel.topic}", inline=False)
        else:
            embed.add_field(name="Channel Topic:", value=f"None", inline=False)    
        
        await ctx.reply(embed=embed, mention_author = False)


    @commands.command(description="Creates a poll. Note: Put title inside [] & use , to separate choices", usage="poll <[title]>, <choice1>, <choice2>, [choice3]...", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def poll(self, ctx: commands.Context, *, message):

        if not ctx.author.guild_permissions.create_polls:
            embed = discord.Embed(
                title="",
                description=f"{animated_cross} **Missing Permissions**\n{cross} You must have `create polls` permissions to use this command",
                color=colour
            )
            if ctx.author.avatar:
                embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar.url)
            else:
                embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.default_avatar.url)

            await ctx.reply(embed=embed, mention_author=False)
            return

        if message.startswith('[') and ']' in message:
            title_end_index = message.index(']')
            title = message[1:title_end_index].strip()
            choices = message[title_end_index + 1:].strip().split(',')
        else:
            title = message.split(',', 1)[0].strip()
            choices = message.split(',', 1)[1].strip().split(',')
        
        choices = [choice.strip() for choice in choices]

        if len(choices) < 2:
            await ctx.reply(embed=discord.Embed(title="", description=f"{cross} | Should have atlest 2 choices", color=colour), mention_author = False)
            return
        
        if len(choices) > 9:
            await ctx.reply(embed=discord.Embed(title="", description=f"{cross} | Should have less than 9 choices", color=colour), mention_author = False)
            return
        
        embed = discord.Embed(title=title, color=colour)
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
            embed.set_author(name=f"Poll for {ctx.guild.name}", icon_url=ctx.guild.icon.url)

        if ctx.author.avatar:
            embed.set_footer(text=f"Created By: {ctx.author}" , icon_url=ctx.author.avatar.url)
        else:
            embed.set_footer(text=f"Created By: {ctx.author}" , icon_url=ctx.author.default_avatar.url)

        for index, choice in enumerate(choices):
            emoji = f"{index+1}\u20e3"
            embed.add_field(name=f"", value=f"{emoji}   **{choice}**", inline=False)
        
        msg = await ctx.send(embed=embed)
        for index in range(len(choices)):
            emoji = f"{index+1}\u20e3"
            await msg.add_reaction(emoji)
        
        await msg.edit(embed=embed)


    @commands.hybrid_command(aliases=['tstart'], description="Creates a timer for given time.", usage="timer <duration> [title]", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(duration="Set the duration as 1m, 2h, 1d or 3d....", title="Set the title for timer embed (optional)")
    async def timer(self, ctx: commands.Context, duration: str, *, title=None):

        time_regex = re.match(r'(\d+)([smhd])$', duration.lower())

        if not time_regex:
            await ctx.reply(embed=discord.Embed(description=f"{cross} | Invalid duration format. Use `1m`, `2h`, `1d`, `30s` etc.", color=colour), mention_author=False, delete_after=10)
            return

        amount = int(time_regex.group(1))
        unit = time_regex.group(2)

        unit_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        total_seconds = amount * unit_map[unit]

        if total_seconds <= 0:
            await ctx.reply(embed=discord.Embed(description=f"{cross} | Please provide a positive duration.", color=colour), mention_author=False, delete_after=10)
            return

        end_time = datetime.now() + timedelta(seconds=total_seconds)
        end_time_timestamp = int(end_time.timestamp())
        end_time_chut = end_time.strftime("%Y-%m-%d %H:%M:%S")

        ebd = discord.Embed(
            title=title or "",
            description=f"# {clock_emoji} | **Timer ends** <t:{end_time_timestamp}:R>",
            color=colour
        )
        if ctx.guild.icon:
            ebd.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        ebd.set_footer(text=f"End time: {end_time_chut}")

        message = await ctx.reply(embed=ebd, mention_author=False)

        await asyncio.sleep(total_seconds)

        ebd = discord.Embed(
            title=title or "",
            description=f"# {clock_emoji} | **Timer ended** <t:{end_time_timestamp}:R>",
            color=colour
        )
        if ctx.guild.icon:
            ebd.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        ebd.set_footer(text="Assister Timer", icon_url=ctx.bot.user.avatar.url)

        await message.edit(embed=ebd)


    @commands.hybrid_command(aliases=['calc', 'cal'], description="Calculate a mathematical expression", usage="cal <expression>", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(expression="Provide the mathematical expression to solve.")
    async def calculate(self, ctx: commands.Context, *, expression):

        cleaned_expression = "".join(c for c in expression if c.isdigit() or c in "+-*/.() ")
        
        try:
            result = eval(cleaned_expression)
            embed = discord.Embed(
                title="",
                description=f"",
                color=colour
            )
            embed.add_field(name="Question:", value=f"```py\n{expression}```", inline=False)
            embed.add_field(name="Solution:", value=f"```js\n{result}```")
            embed.set_author(name=f"Assister Calculator", icon_url=ctx.bot.user.avatar.url)
            embed.set_footer(text=f"Requested by: {ctx.author}")

            await ctx.reply(embed=embed, mention_author=False)
        except Exception as e:
            embed = discord.Embed(
                title="",
                description=f"**Failed to evaluate expression:**\n```{expression}```\n**Error:** ```{str(e)}```",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(description="Converts currency from one to another", usage="convert <amount> <fromc> <toc>", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(amount="Provide the amount to convert", fromc="Provide currency from which you have to convert", toc="Provide the currency to which you have to convert")
    async def convert(self, ctx: commands.Context, amount: float, fromc: str, toc: str):
        
        api_key = '9ed7454d2d23a106328e765f'
        url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{fromc.upper()}'
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    data = await response.json()
                    if data['result'] == 'success':
                        rate = data['conversion_rates'].get(toc.upper())
                        if rate:
                            converted_amount = amount * rate

                            embed = discord.Embed(
                                title="",
                                description=f"",
                                color=colour
                            )
                            embed.add_field(name=f"Amount:", value=f"```py\n{amount}```", inline=False)
                            embed.add_field(name="Currency Change:", value=f"```js\n{fromc.upper()} to {toc.upper()}```", inline=False)
                            embed.add_field(name=f"Final Value:", value=f"```py\n{converted_amount:.2f} {toc.upper()}```")
                            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                            await ctx.reply(embed=embed, mention_author=False)

                        else:

                            embed = discord.Embed(
                                title="",
                                description=f"",
                                color=colour
                            )
                            embed.add_field(name=f"{e_dot} Valid Codes", value=f"`INR` | `PKR` | `USD` | `EUR` | `JPY` | `GBP` | `AUD` | `CAD` | `CHF` | `CNY` | `SEK` | `NZD` | ""`BRL` | `INR` | `MXN` | `RUB` | `ZAR` | `KRW` | `SGD` | `HKD` | `TRY` | `IDR` | `PLN` | ""`NOK` | `MYR` | `AED` | `ILS` | `COP` | `SAR` | `PHP`")
                            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                            await ctx.reply(embed=embed, mention_author=False)

                    else:
                        embed = discord.Embed(
                            title="",
                            description=f"{cross} | Invalid target currency code",
                            color=colour
                        )
                        embed.add_field(name=f"Valid Codes", value=f"{e_dot} `INR` | `PKR` | `USD` | `EUR` | `JPY` | `GBP` | `AUD` | `CAD` | `CHF` | `CNY` | `SEK` | `NZD` | ""`BRL` | `INR` | `MXN` | `RUB` | `ZAR` | `KRW` | `SGD` | `HKD` | `TRY` | `IDR` | `PLN` | ""`NOK` | `MYR` | `AED` | `ILS` | `COP` | `SAR` | `PHP`")
                        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                        await ctx.reply(embed=embed, mention_author=False)

            except:
                print("lund convert")


    @commands.hybrid_command(aliases=['setreminder', 'reminderset'], description="Sets the reminder message", usage="reminder <duration> <message>", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(time="Set the time after which reminder will be sent", message="Reminder message")
    async def reminder(self, ctx: commands.Context, time: str, *, message: str):
        user = ctx.author

        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        try:
            unit = time[-1]
            duration = int(time[:-1])
            if unit not in time_units:
                raise ValueError
            seconds = duration * time_units[unit]

        except (ValueError, IndexError):
            embed = discord.Embed(
                title="",
                description=f"{cross} | The time format you provided is invalid.\n{e_dot} Use the format `10m` for 10 minutes.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        embed = discord.Embed(
            title="",
            description=f"{tick} | Reminder set successfully.\n{e_dot} I will remind you after `{duration}{unit}`",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)
        
        await asyncio.sleep(seconds)
        
        reminder_embed = discord.Embed(
            title="",
            color=colour
        )
        reminder_embed.add_field(name="Message", value=f"<:right:1496889463564009565> {message}")
        reminder_embed.set_author(name="Assister Reminder", icon_url=ctx.bot.user.avatar.url)
        
        try:
            await user.send(embed=reminder_embed)
            dm_status = f"{tick} Successful"
        except discord.Forbidden:
            dm_status = f"{cross} Unsuccessful (Unable to send DM)"
        
        channel_embed = discord.Embed(
            title="",
            color=colour
        )
        channel_embed.set_author(name="Assister Reminder", icon_url=ctx.bot.user.avatar.url)
        channel_embed.add_field(name="Message", value=f"<:right:1496889463564009565> {message}")
        channel_embed.add_field(name="DM Status", value=f"{dm_status}", inline=False)
        await ctx.send(f"{user.mention}", embed=channel_embed)


    @commands.hybrid_command(aliases=['shedulemessage', 'shedulemsg'], description="Schedules a message in a particular channel (time recieved as minutes)", usage="schedule <time> <channel> <message>", category="General")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(time="Provide the time after which message will be sent (time received in minutes). Input time as: 1 or 10 or 20...", channel="Set the channel you want to send the message into", message="Set the message you want to be sent after completing time")
    async def schedule(self, ctx: commands.Context, time: str, channel: discord.TextChannel, *, message: str):

        try:
            delta = int(time)
            schedule_time = datetime.utcnow() + timedelta(minutes=delta)
        except ValueError:
            embed = discord.Embed(
                title="",
                description=f"{cross} | Invalid time format. Use an integer number of minutes",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            
            return
        
        embed = discord.Embed(
            title="",
            description=f"{tick} | Message scheduled to be sent in {delta} minutes",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)
        
        await asyncio.sleep(delta * 60)
        await channel.send(message)


    @commands.hybrid_command(description="Fetches a meme", usage="meme", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def meme(self, ctx: commands.Context):
        url = 'https://meme-api.com/gimme'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                meme_url = data.get('url')
                
                if meme_url:

                    embed = discord.Embed(
                        title="",
                        description=f"",
                        color=colour
                    )
                    embed.set_image(url=meme_url)
                    embed.set_author(name="Assister Memes", icon_url=ctx.bot.user.avatar.url)
                    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                    await ctx.reply(embed=embed, mention_author=False)
                    
                else:
                    await ctx.reply("Couldn't fetch a meme at the moment", mention_author=False, delete_after=5)


    @commands.hybrid_command(description="Fetches a joke", usage="joke", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def joke(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://official-joke-api.appspot.com/random_joke') as response:
                if response.status == 200:
                    joke = await response.json()
                    setup = joke['setup']
                    punchline = joke['punchline']

                    embed = discord.Embed(
                        title="",
                        description=f"<:shareef:1267866685759815721> {setup}\n\n<:shareef:1267866696849428540> ||{punchline}||",
                        color=colour
                    )
                    embed.set_author(name="Assister Jokes", icon_url=ctx.bot.user.avatar.url)
                    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                    await ctx.reply(embed=embed, mention_author=False)
                else:
                    await ctx.reply("Couldn't fetch a joke at the moment.", mention_author=False, delete_after=5)


    @commands.hybrid_command(description="Fetches a quote", usage="quote", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def quote(self, ctx: commands.Context):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://favqs.com/api/qotd') as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data['quote']['body']
                        author = data['quote']['author']

                        embed = discord.Embed(
                            title="",
                            description=f'"{quote}" - **{author}**\n',
                            color=colour
                        )
                        embed.set_author(name="Assister Quotes", icon_url=ctx.bot.user.avatar.url)
                        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                        await ctx.reply(embed=embed, mention_author=False)
                    else:
                        await ctx.reply("Couldn't fetch a quote at the moment 😞", mention_author=False, delete_after=5)

        except aiohttp.ClientConnectorError:
            await ctx.reply("Unable to fetch a quote right now 😞", mention_author=False, delete_after=5)
        except aiohttp.ClientError:
            await ctx.reply(f"Unable to fetch a quote right now 😞", mention_author=False, delete_after=5)



    @commands.command(aliases=['tl'], description="Translates a replied text", usage="tl", category="General")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def translate(self, ctx: commands.Context):

        if not ctx.message.reference:
            return await ctx.reply(
                embed=discord.Embed(description=f"{cross} | Reply to a message you want to translate.", color=colour),
                mention_author=False, delete_after=10
            )

        channel = ctx.guild.get_channel(ctx.message.reference.channel_id)
        if not channel:
            return await ctx.reply(
                embed=discord.Embed(description=f"{cross} | That channel isn't accessible.", color=colour),
                mention_author=False, delete_after=10
            )

        try:
            message = await channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            return await ctx.reply(
                embed=discord.Embed(description=f"{cross} | The replied message was not found.", color=colour),
                mention_author=False, delete_after=10
            )
        except discord.Forbidden:
            return await ctx.reply(
                embed=discord.Embed(description=f"{cross} | I don't have permission to access that channel.", color=colour),
                mention_author=False, delete_after=10
            )

        tltext = message.content
        if not tltext:
            return await ctx.reply(
                embed=discord.Embed(description=f"{cross} | That message has no text to translate.", color=colour),
                mention_author=False, delete_after=10
            )

        try:
            translator = GoogleTranslator(source='auto', target='en')
            translated_text = translator.translate(tltext)
            detected = GoogleTranslator(source='auto', target='en').detect(tltext) or 'unknown'
        except Exception as e:
            return await ctx.reply(
                embed=discord.Embed(description=f"{cross} | Translation failed: `{e}`", color=colour),
                mention_author=False, delete_after=10
            )

        embed = discord.Embed(color=colour)
        embed.add_field(name="📜 Original", value=f"```{tltext[:1000]}```", inline=False)
        embed.add_field(name="📄 Translated", value=f"```{translated_text[:1000]}```", inline=False)
        embed.set_footer(text=f"Detected language: {detected} → English")
        await ctx.reply(embed=embed, mention_author=False)


    @commands.hybrid_command(description="Fetches top 5 results from google", usage="google <query>", category="General")
    @bled()
    @app_commands.describe(query="What do you want to search?")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def google(self, ctx: commands.Context, *, query):
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=8):
                    results.append(r)

            if not results:
                await ctx.reply(
                    embed=discord.Embed(description=f"{cross} | No search results found.", color=colour),
                    mention_author=False,
                    delete_after=10
                )
                return

            components = []
            components.append(discord.ui.TextDisplay(
                f"## 🔍 Search Results for '{query}'\n-# Powered by DuckDuckGo"
            ))
            components.append(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large))

            added = 0
            for result in results:
                if added >= 5:
                    break

                title   = result.get('title', 'No Title')
                link    = result.get('href', 'No Link')
                snippet = result.get('body', 'No Description')

                if contains_nsfw(title) or contains_nsfw(snippet):
                    continue

                added += 1
                components.append(discord.ui.TextDisplay(
                    f"**{added}. [{title}]({link})**\n{snippet}"
                ))

                if added < 5: 
                    components.append(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

            if added == 0:
                await ctx.reply(
                    embed=discord.Embed(
                        description=f"{cross} | nsfw has been blocked by [developers](https://github.com/code2ahm)",
                        color=colour
                    ),
                    mention_author=False
                )
                return

            container = discord.ui.Container(*components, accent_color=colour)

            class ResultView(discord.ui.LayoutView):
                pass

            view = ResultView()
            view.add_item(container)

            await ctx.reply(view=view, mention_author=False)

        except Exception as e:
            await ctx.reply("An error occurred while fetching search results.", mention_author=False, delete_after=6)


    @commands.hybrid_command(aliases=['img', 'imagine'], description="Fetches an image for provided query", usage="imagine <query>", category="General")
    @bled()
    @app_commands.describe(query="What do you want to search for?")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def image(self, ctx: commands.Context, *, query):
        try:
            headers = {
                'Authorization': "SlxLCu8vHncW2T08xRguLGWHnmIDU9RwV5e3VOKoDgVKxjwpUORphPtk"
            }
            params = {
                'query': query,
                'per_page': 1
            }

            response = requests.get(PEXELS_ENDPOINT, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                photos = data.get('photos', [])

                if photos:
                    imgurl = photos[0]['src']['large']

                    embed = discord.Embed(
                        description=f"<:streaming:1497212447403151520> | **Image search result for '{query}'**",
                        color=colour
                    )
                    embed.set_image(url=imgurl)
                    embed.set_footer(
                        text=f"Requested by {ctx.author}",
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
                    )
                    embed.set_author(name=f"Assister Image Generator", icon_url=ctx.bot.user.avatar.url)

                    await ctx.reply(embed=embed, mention_author=False)
                else:
                    await ctx.reply(embed=discord.Embed(description="No images found for your query.", color=colour), mention_author=False, delete_after=10)

            else:
                await ctx.reply(embed=discord.Embed(description="Couldn't fetch image results. Try again later.", color=colour), mention_author=False, delete_after=10)

        except requests.RequestException as e:
            print(e)
        except Exception as e:
            print(e)







            
async def setup(bot):
    await bot.add_cog(General(bot))