import discord
from discord.ext import commands
from discord import app_commands
from utils.checks import *
from utils.variables import *
from utils.prefixes import *

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="voice", description="Manage voice channels and related features", invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def voice(self, ctx: commands.Context):
        ahm7 = self.bot.get_command('help')

        if ahm7:
            await ctx.invoke(ahm7, query='voice')
        else:
            return


    @voice.command(aliases=['deaf'], description="Deafens a member in voice channel", usage="voice deafen <member>")
    @bled()
    @commands.has_guild_permissions(deafen_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to deafen.")
    async def deafen(self, ctx: commands.Context, member: discord.Member):
        try:
            if member.voice and member.voice.deaf:
                embed = discord.Embed(
                    description=f"❗ {member.mention} is already deafened.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            await member.edit(deafen=True, reason=f"Deafened by {ctx.author}")

            ebd = discord.Embed(
                description=f"{tick} | Operation Successful",
                color=colour
            )
            ebd.add_field(name="Description:", value=f"{e_dot} Deafened {member.mention}\n{e_dot} Moderator {ctx.author.mention}")
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=ebd, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                description=f"❗ I do not have permission to deafen {member}.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(aliases=['deafall'], description="Deafens all members in a voice channel", usage="voice deafenall <channel>")
    @admin()
    @bled()
    @app_commands.describe(channel="Select the channel to deafen all members in it.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def deafenall(self, ctx: commands.Context, channel: discord.VoiceChannel):
        try:
            for member in channel.members:
                await member.edit(deafen=True, reason=f"Deafen all | Deafened by {ctx.author}")

            ebd = discord.Embed(
                title="",
                description=f"{tick} | Operation Successful",
                color=colour
            )
            ebd.add_field(name="Description:", value=f"{e_dot} Deafened all members in {channel.mention}\n{e_dot} Moderator {ctx.author.mention}")
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=ebd, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to deafen members in {channel.mention}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(aliases=['undeaf'], description="Undeafens a member", usage="voice undeafen <member>")
    @bled()
    @commands.has_guild_permissions(deafen_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to undeafen.")
    async def undeafen(self, ctx: commands.Context, member: discord.Member):
        try:
            if member.voice and not member.voice.deaf:
                embed = discord.Embed(
                    title="",
                    description=f"❗ {member.mention} is already undeafened.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            await member.edit(deafen=False, reason=f"Undeafened by {ctx.author}")

            ebd = discord.Embed(
                title="",
                description=f"{tick} | Operation Successful",
                color=colour
            )

            ebd.add_field(name="Description:", value=f"{e_dot} Undeafened {member.mention}\n{e_dot} Moderator {ctx.author.mention}")
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=ebd, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to undeafen {member.mention}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(aliases=['undeafall'], description="Undeafens all members in a voice channel", usage="voice undeafenall <channel>")
    @admin()
    @bled()
    @app_commands.describe(channel="Select the channel to undeafen all members in it.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def undeafenall(self, ctx: commands.Context, channel: discord.VoiceChannel):

        try:
            for member in channel.members:
                await member.edit(deafen=False, reason=f"Undeafen all | Undeafened by {ctx.author}")

            ebd = discord.Embed(
                title="",
                description=f"{tick} | Operation Successful",
                color=colour
            )

            ebd.add_field(name="Description:", value=f"{e_dot} Undeafened all members in {channel.mention}\n{e_dot} Moderator {ctx.author.mention}")
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=ebd, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to undeafen members in {channel.mention}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return
        
    @voice.command(name="kick", aliases=['disconnect'], description="Kick a member from voice channel", usage="voice kick <member>")
    @bled()
    @commands.has_guild_permissions(move_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to kick from voice channel")
    async def vckick(self, ctx: commands.Context, member: discord.Member):

        try:
            if member.voice:
                await member.move_to(None, reason=f"Kicked by {ctx.author}")

                ebd = discord.Embed(
                    title="",
                    description=f"{tick} | Operation Successful",
                    color=colour
                )

                ebd.add_field(name="Description:", value=f"{e_dot} Disconnected {member.mention}\n{e_dot} Moderator {ctx.author.mention}")
                ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=ebd, mention_author=False)

            else:
                embed = discord.Embed(
                    title="",
                    description=f"❗ {member.mention} is not in a voice channel",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to kick {member}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(description="Kick all members from a voice channel", usage="voice kickall <channel>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Select the channel to kick all members from.")
    async def kickall(self, ctx: commands.Context, channel: discord.VoiceChannel):

        try:
            rand = []

            if len(channel.members) == 0:
                embed = discord.Embed(
                    title="",
                    description=f"❗ No members are currently in {channel.mention}",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            for member in channel.members:
                if member.voice is None:
                    continue

                await member.move_to(None, reason=f"Kickall | Kicked by {ctx.author}")
                rand.append(member)

            if rand:
                ebd = discord.Embed(
                    title="",
                    description=f"{tick} | Operation Successful",
                    color=colour
                )
                ebd.add_field(name="Description:", value=f"{e_dot} Kicked all members from {channel.mention}\n{e_dot} Moderator {ctx.author.mention}")
                ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=ebd, mention_author=False)

            else:
                embed = discord.Embed(
                    title="",
                    description=f"❗ No members to kick from {channel.mention}",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to kick members from {channel.mention}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return

    @voice.command(description="Move a member to a specific voice channel", usage="voice move <member> <channel>")
    @bled()
    @commands.has_guild_permissions(move_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to move.", channel="Select the channel to move the member to.")
    async def move(self, ctx: commands.Context, member: discord.Member, channel: discord.VoiceChannel):

        try:
            if member.voice and member.voice.channel == channel:
                embed = discord.Embed(
                    title="",
                    description=f"❗ {member.mention} is already in {channel.mention}.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            if member.voice:
                await member.move_to(channel, reason=f"Moved by {ctx.author}")
                
                embed = discord.Embed(
                    title="",
                    description=f"{tick} | Operation Successfull",
                    color=colour
                )
                embed.add_field(name="Description:", value=f"{e_dot} Moved {member.mention} to {channel.mention}\n{e_dot} Moderator: {ctx.author.mention}")
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)

            else:
                embed = discord.Embed(
                    title="",
                    description=f"❗ {member.mention} is not connected to any voice channel.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)


        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to move {member.mention}.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(description="Move all members to a voice channel", usage="voice moveall <channel>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Select channel to move members to it.")
    async def moveall(self, ctx: commands.Context, channel: discord.VoiceChannel):

        try:
            lund = []

            for voice_channel in ctx.guild.voice_channels:
                for member in voice_channel.members:
                    if member.voice.channel != channel:
                        lund.append(member)

            if lund:
                for member in lund:
                    await member.move_to(channel, reason=f"Moveall | Moved by {ctx.author}")

                ebd = discord.Embed(
                    title="",
                    description=f"{tick} | Operation Successful",
                    color=colour
                )
                ebd.add_field(name="Description:", value=f"{e_dot} Moved all members to {channel.mention}\n{e_dot} Moderator {ctx.author.mention}")
                ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=ebd, mention_author=False)

            else:
                ebdd = discord.Embed(
                    title="",
                    description=f"❗ No members connected to any voice channel or all members are already in {channel.mention}",
                    color=colour
                )
                ebdd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=ebdd, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to move members",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(name="mute" ,description="Mute a member in a voice channel", usage="voice mute <member>")
    @bled()
    @commands.has_guild_permissions(mute_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to mute.")
    async def vmute(self, ctx: commands.Context, member: discord.Member):

        try:
            if member.voice and member.voice.mute:
                embed = discord.Embed(
                    title="",
                    description=f"❗ {member.mention} is already muted.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            if member.voice:
                await member.edit(mute=True, reason=f"Muted by {ctx.author}")

                embed = discord.Embed(
                    title="",
                    description=f"{tick} | Operation Successful",
                    color=colour
                )
                embed.add_field(name="Description:", value=f"{e_dot} Muted {member.mention}\n{e_dot} Moderator: {ctx.author.mention}")
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)

            else:
                embed = discord.Embed(
                    title="",
                    description=f"❗ {member.mention} is not connected to any voice channel.",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to mute {member.mention}.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(description="Mute all members in a voice channel", usage="voice muteall <channel>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Select the channel to mute all members in.")
    async def muteall(self, ctx: commands.Context, channel: discord.VoiceChannel):

        try:
            if not channel.members:
                embed = discord.Embed(
                    title="",
                    description=f"❗ No members are connected to {channel.mention}",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            for member in channel.members:
                await member.edit(mute=True, reason=f"Muted all members by {ctx.author}")

            embed = discord.Embed(
                description=f"{tick} | Operation Successful",
                color=colour
            )
            embed.add_field(name="Description:", value=f"{e_dot} Muted all members in {channel.mention}.\n{e_dot} Moderator: {ctx.author.mention}")
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to mute members in {channel.mention}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(name="unmute" ,description="Unmute a specific member in voice channel", usage="voice unmute <member>")
    @bled()
    @commands.has_guild_permissions(mute_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to unmute.")
    async def vunmute(self, ctx: commands.Context, member: discord.Member):

        try:
            if not member.voice.mute:
                embed = discord.Embed(
                    title="",
                    description=f"❗ {member.mention} is not muted",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            await member.edit(mute=False, reason=f"Unmuted by {ctx.author}")

            ebd = discord.Embed(
                title="",
                description=f"{tick} | Operation Successful",
                color=colour
            )
            ebd.add_field(name="Description:", value=f"{e_dot} Unmuted {member.mention}\n{e_dot} Moderator: {ctx.author.mention}")
            ebd.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=ebd, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"{cross} | I do not have permission to unmute {member.mention}.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False, delete_after=10)

        except Exception:
            return


    @voice.command(description="Unmute all members in a voice channel", usage="voice unmute <channel>")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(channel="Select the channel to unmute all members in.")
    async def unmuteall(self, ctx: commands.Context, channel: discord.VoiceChannel):

        try:
            if not channel.members:
                embed = discord.Embed(
                    title="",
                    description=f"❗ No members are connected to {channel.mention}",
                    color=colour
                )
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
                await ctx.reply(embed=embed, mention_author=False)
                return

            for member in channel.members:
                if member.voice.mute:
                    await member.edit(mute=False, reason=f"Unmuted all members by {ctx.author}")

            embed = discord.Embed(
                title="",
                description=f"{tick} | Operation Successful",
                color=colour
            )
            embed.add_field(name="Description:", value=f"{e_dot} Unmuted all members in {channel.mention}\n{e_dot} Moderator: {ctx.author.mention}")
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to unmute members in {channel.mention}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except Exception:
            return


    @voice.command(description="Pulls a member to your current voice channel", usage="voice pull <member>")
    @bled()
    @commands.has_guild_permissions(move_members=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(member="Select the member to pull.")
    async def pull(self, ctx: commands.Context, member: discord.Member):

        if not ctx.author.voice:
            embed = discord.Embed(
                title="",
                description=f"❗ You must be connected to a voice channel.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)
            return

        if not member.voice:
            embed = discord.Embed(
                title="",
                description=f"❗ {member.mention} is not connected to a voice channel.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)
            return

        try:
            chnl = ctx.author.voice.channel
            await member.move_to(chnl, reason=f"Pull | Pulled by {ctx.author}")

            embed = discord.Embed(
                title="",
                description=f"{tick} | Operation Successful",
                color=colour
            )
            embed.add_field(name="Description:", value=f"{e_dot} Pulled {member.mention} to {chnl.mention}\n{e_dot} Moderator {ctx.author.mention}")
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False)

        except discord.Forbidden:
            embed = discord.Embed(
                title="",
                description=f"❗ I do not have permission to move {member.mention}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
            await ctx.reply(embed=embed, mention_author=False, delete_after=10)

        except Exception:
            return






async def setup(bot):
    await bot.add_cog(Voice(bot))