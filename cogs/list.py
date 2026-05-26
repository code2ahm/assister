import discord
from discord.ext import commands
from utils.paginator import *
from utils.variables import *
from utils.checks import *
from utils.prefixes import *
from utils.loads import *
from discord import app_commands


class Listt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_group(name="list", description="Shows list help", usage="list" , invoke_without_command=True)
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def listt(self, ctx: commands.Context):
        ahm7 = self.bot.get_command('help')

        if ahm7:
            await ctx.invoke(ahm7, query='utility')
        else:
            return 

    @listt.command(name="emojis", aliases=['emoji'], description="Shows the list of emojis in the server.", usage="list emojis")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def emojis(self, ctx: commands.Context):
        emojis = ctx.guild.emojis
        if not emojis:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No emojis found in this server.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(emojis), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, emoji in enumerate(emojis[sti:endi], start=sti):
                embed.description += f"`{index + 1}.` - {emoji}︰`{emoji}`\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Emojis in {ctx.guild.name} - {len(emojis)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Emojis in {ctx.guild.name} - {len(emojis)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @listt.command(name="admins", description="Shows the admins in the server", usage="list admins")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ladmins(self, ctx: commands.Context):
        admins = [member for member in ctx.guild.members if member.guild_permissions.administrator]

        if not admins:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No admins found in this server.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(admins), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, admin in enumerate(admins[sti:endi], start=sti):
                adminj = int(admin.joined_at.timestamp()) if admin.joined_at else 0
                embed.description += f"`{index + 1}.` - {admin.mention}︰<t:{adminj}:D>\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Admins in {ctx.guild.name} - {len(admins)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Admins in {ctx.guild.name} - {len(admins)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @listt.command(name="mods", description="Shows the moderators in the server", usage="list mods")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lmods(self, ctx: commands.Context):
        mods = [member for member in ctx.guild.members if member.guild_permissions.kick_members]

        if not mods:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No moderators found in this server.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(mods), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, mod in enumerate(mods[sti:endi], start=sti):
                modj = int(mod.joined_at.timestamp()) if mod.joined_at else 0
                embed.description += f"`{index + 1}.` - {mod.mention}︰<t:{modj}:D>\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Moderators in {ctx.guild.name} - {len(mods)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Moderators in {ctx.guild.name} - {len(mods)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @listt.command(name="bans", description="Shows the banned members in the server", usage="list bans")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lbans(self, ctx: commands.Context):
        try:
            bans = []
            async for entry in ctx.guild.bans():
                if entry.user:
                    bans.append(entry)

            if not bans:
                embed = discord.Embed(
                    title="",
                    description=f"{cross} | No banned members found in this server.",
                    color=colour
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            perpage = 10
            pages = []
            for i in range(0, len(bans), perpage):
                sti = i
                endi = i + perpage
                embed = discord.Embed(
                    title="",
                    color=colour
                )

                embed.description = ""
                for index, entry in enumerate(bans[sti:endi], start=sti):
                    user = entry.user
                    if user:
                        embed.description += f"`{index + 1}` - [{user.name}](https://discord.com/users/{user.id})︰{entry.reason or 'No reason provided'}\n"

                if ctx.guild.icon:
                    embed.set_author(name=f"Banned Members in {ctx.guild.name} - {len(bans)}", icon_url=ctx.guild.icon.url)
                else:
                    embed.set_author(name=f"Banned Members in {ctx.guild.name} - {len(bans)}")
                embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

                pages.append(embed)

            paginator = Ahm(pages)
            await paginator.start(ctx)

        except Exception:
            embed = discord.Embed(
                title="",
                description=f"{cross} | An error occurred while fetching banned members.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False, delete_after=10)


    @listt.command(name="roles", description="Shows the roles in the server", usage="list roles")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lroles(self, ctx: commands.Context):
        roles = sorted(ctx.guild.roles[1:], key=lambda role: role.position, reverse=True)

        if not roles:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No roles found in this server.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(roles), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, role in enumerate(roles[sti:endi], start=sti):
                color_hex = f"#{role.color.value:06x}"
                embed.description += f"`{index + 1}.` - {role.mention}︰`{role.id}`︰{color_hex}\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Roles in {ctx.guild.name} - {len(roles)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Roles in {ctx.guild.name} - {len(roles)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)

    @listt.command(name="bots", description="Shows the bots in the server", usage="list bots")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lbots(self, ctx: commands.Context):
        bots = [member for member in ctx.guild.members if member.bot]

        if not bots:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No bots found in this server.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(bots), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, bot in enumerate(bots[sti:endi], start=sti):
                cbot = int(bot.created_at.timestamp()) if bot.created_at else 0
                embed.description += f"`{index + 1}.` - {bot.mention}︰<t:{cbot}:D>\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Bots in {ctx.guild.name} - {len(bots)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Bots in {ctx.guild.name} - {len(bots)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @listt.command(name="boosters", description="Shows the boosters in the server", usage="list boosters")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lboosters(self, ctx: commands.Context):
        boosters = [member for member in ctx.guild.members if member.premium_since]

        if not boosters:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No boosters found in this server.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(boosters), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, booster in enumerate(boosters[sti:endi], start=sti):
                embed.description += f"`{index + 1}.` - {booster.mention}\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Boosters in {ctx.guild.name} - {len(booster)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Boosters in {ctx.guild.name} - {len(booster)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @listt.command(name="invoice", description="Shows members connected to voice channels", usage="list invoice")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def linvoice(self, ctx: commands.Context):
        voice_members = [member for member in ctx.guild.members if member.voice]

        if not voice_members:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No members are currently connected to voice channels.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(voice_members), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, member in enumerate(voice_members[sti:endi], start=sti):
                voice_channel = member.voice.channel if member.voice else "Unknown"
                embed.description += f"`{index + 1}.` - {member.mention}︰{voice_channel.mention}\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Members in Voice Channels in {ctx.guild.name} - {len(voice_members)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Members in Voice Channels in {ctx.guild.name} - {len(voice_members)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)


    @listt.command(name="inrole", description="Shows members with a specific role", usage="list inrole <role>")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(role="Select the role you want to view details for.")
    async def linrole(self, ctx: commands.Context, role: discord.Role):
        
        if role is None:
            embed = discord.Embed(
                title="",
                description=f"{cross} | '{role}' not found.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False, delete_after=10)
            return

        memrole = [member for member in ctx.guild.members if role in member.roles]

        if not memrole:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No members found with the {role.mention} role.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(memrole), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, member in enumerate(memrole[sti:endi], start=sti):
                memj = int(member.joined_at.timestamp()) if member.joined_at else 0
                embed.description += f"`{index + 1}.` - {member.mention}︰<t:{memj}:D>\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Members with {role.name} role in {ctx.guild.name} - {len(memrole)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Members with {role.name} role in {ctx.guild.name} - {len(memrole)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)



    @listt.command(name="earlymembers", aliases=["earlymembs"], description="Shows the earliest joined members in the server", usage="list earlymembers")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def learlymembers(self, ctx: commands.Context):
        
        membs = sorted(
            [member for member in ctx.guild.members if member.joined_at],
            key=lambda member: member.joined_at
        )

        if not membs:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No members found in this server.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        perpage = 10
        pages = []
        for i in range(0, len(membs), perpage):
            sti = i
            endi = i + perpage
            embed = discord.Embed(
                title="",
                color=colour
            )

            embed.description = ""
            for index, member in enumerate(membs[sti:endi], start=sti):
                memj = int(member.joined_at.timestamp())
                embed.description += f"`{index + 1}.` - {member.mention}︰<t:{memj}:D>\n"

            if ctx.guild.icon:
                embed.set_author(name=f"Earliest Members in {ctx.guild.name} - {len(membs)}", icon_url=ctx.guild.icon.url)
            else:
                embed.set_author(name=f"Earliest Members in {ctx.guild.name} - {len(membs)}")
            embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

            pages.append(embed)

        paginator = Ahm(pages)
        await paginator.start(ctx)



async def setup(bot):
    await bot.add_cog(Listt(bot))