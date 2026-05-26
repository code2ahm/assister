import discord
from discord.ext import commands
from discord import app_commands
from utils.prefixes import *
from utils.variables import *
from utils.checks import *
from utils.loads import mdch, bymd, savemedia

class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if message.guild:
            guild_id = str(message.guild.id)
            if guild_id in mdch:
                ahn = mdch[guild_id]
                if message.channel.id in ahn:
                    ahmm = bymd.get(guild_id, [])
                    if message.author.id not in ahmm:
                        if not message.attachments and not message.embeds:
                            try:
                                await message.delete()
                                await message.channel.send(
                                    f"{cross} | **Only attachments are allowed in this channel.**",
                                    delete_after=10
                                )
                            except discord.errors.Forbidden:
                                pass



    @commands.hybrid_group(name="media", invoke_without_command=True)
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def media(self, ctx: commands.Context):
        ahm7 = self.bot.get_command('help')

        if ahm7:
            await ctx.invoke(ahm7, query='media')
        else:
            return


    @media.group(name="channel", invoke_without_command=True, description="Add a channel to media only channels", usage="media channel", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def media_channel(self, ctx: commands.Context):

        guild_id = str(ctx.guild.id) if ctx.guild else None
        prefix = guild_prefix(guild_id) if guild_id else '.'
    
        embed = discord.Embed(
            title="",
            description=f"{cross} | Wrong Syntax\n{tick} | Correct Syntax: `{prefix}media channel add or remove`",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @media_channel.command(name="add", description="Adds a channel to media only channel", usage="media channel add <channel>", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(channel="Select the channel to add to media only channel.")
    async def add_media_channel(self, ctx: commands.Context, channel: discord.TextChannel):

        guild_id = str(ctx.guild.id)
        mdch.setdefault(guild_id, [])
        if channel.id not in mdch[guild_id]:
            mdch[guild_id].append(channel.id)
            savemedia('media.json', mdch)

            embed = discord.Embed(
                title="",
                description=f"{tick} | Successfully added {channel.mention} to `media-only` channels.",
                color=colour
            )
        else:
            embed = discord.Embed(
                title="",
                description=f"{grey} | {channel.mention} is already in the `media-only` channels list.",
                color=colour
            )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @media_channel.command(name="remove", description="Removes a channel to media only channel", usage="media channel remove <channel>", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(channel="Select the channel to remove from media only channels.")
    async def remove_media_channel(self, ctx: commands.Context, channel: discord.TextChannel):

        guild_id = str(ctx.guild.id)
        if guild_id in mdch and channel.id in mdch[guild_id]:
            mdch[guild_id].remove(channel.id)
            savemedia('media.json', mdch)

            embed = discord.Embed(
                title="",
                description=f"{tick} | Successfully removed {channel.mention} from `media-only` channels.",
                color=colour
            )
        else:
            embed = discord.Embed(
                title="",
                description=f"{cross} | {channel.mention} is not in the `media-only` channels list.",
                color=colour
            )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @media_channel.command(aliases=['show', 'config'], name="list", description="Shows the media channel list for the server.", usage="media channel list", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def list_mdch(self, ctx: commands.Context):

        guild_id = str(ctx.guild.id)
        if guild_id in mdch:
            channels = [f"<#{channel}>" for channel in mdch[guild_id]]
            if channels:
                channels_list = "\n".join(f"`[{index + 1}]` - {channel}" for index, channel in enumerate(channels))
                embed = discord.Embed(
                    title="",
                    description=f"Here is the list of `media-only` channels for **{ctx.author.guild}**.",
                    color=colour
                )
                embed.add_field(name=f"{e_dot} Channels:", value=f"{channels_list}", inline=False)
            else:
                embed = discord.Embed(
                    title="",
                    description=f"{cross} | No channel configured as `media-only` channel",
                    color=colour
                )
        else:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No channel configured as `media-only` channel",
                color=colour
            )

        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @media.group(name="bypass", invoke_without_command=True, description="Add a user to media bypass list.", usage="media bypass", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe()
    async def media_bypass(self, ctx: commands.Context):

        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix = guild_prefix(guild_id) if guild_id else '.'

            embed = discord.Embed(
                title="",
                description=f"{cross} | Wrong Syntax\n{tick} | Correct Syntax: `{prefix}media bypass add or remove`",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)

        

    @media_bypass.command(name="add", description="Adds a user to media bypass list.", usage="media bypass add <member>", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(member="Select the member to be added to media bypass list.")
    async def add_bypass(self, ctx: commands.Context, member: discord.Member):

        guild_id = str(ctx.guild.id)
        bymd.setdefault(guild_id, [])
        if member.id not in bymd[guild_id]:
            bymd[guild_id].append(member.id)
            savemedia('mediabypass.json', bymd)
            
            embed = discord.Embed(
                title="",
                description=f"{tick} | Successfully added {member.mention} to `media-bypass` list",
                color=colour
            )
        else:
            embed = discord.Embed(
                title="",
                description=f"{grey} | {member.mention} is already in `media-bypass` list",
                color=colour
            )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @media_bypass.command(name="remove", description="Removes the member from media bypass list.", usage="media bypass remove <member>", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(member="Select the member to be removed from media bypass list.")
    async def remove_bypass(self, ctx: commands.Context, member: discord.Member):
        guild_id = str(ctx.guild.id)
        
        if guild_id in bymd and member.id in bymd[guild_id]:
            bymd[guild_id].remove(member.id)
            savemedia('mediabypass.json', bymd)

            embed = discord.Embed(
                title="",
                description=f"{tick} | Successfully removed {member.mention} from `media-bypass` list",
                color=colour
            )
        else:
            embed = discord.Embed(
                title="",
                description=f"{grey} | {member.mention} is not in `media-bypass` list",
                color=colour
            )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)


    @media_bypass.command(name="list", description="Shows the members in media bypass list.", usage="media bypass list", category="Media")
    @aboveb()
    @admin()
    @bled()
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe()
    async def list_bypass(self, ctx: commands.Context):

        guild_id = str(ctx.guild.id)
        if guild_id in bymd:
            membs = [f"<@{member}>" for member in bymd[guild_id]]
            if membs:
                memby = "\n".join(f"`[{index + 1}]` - {member}" for index, member in enumerate(membs))
                embed = discord.Embed(
                    title="",
                    description=f"Here is the list of `media-bypass` member for **{ctx.author.guild}**.",
                    color=colour
                )
                embed.add_field(name=f"{e_dot} membs:", value=f"{memby}", inline=False)
            else:
                embed = discord.Embed(
                    title="",
                    description=f"{cross} | No member in `media-bypass` list",
                    color=colour
                )
        else:
            embed = discord.Embed(
                title="",
                description=f"{cross} | No member in `media-bypass` list",
                color=colour
            )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.reply(embed=embed, mention_author=False)



async def setup(bot):
    await bot.add_cog(Media(bot))