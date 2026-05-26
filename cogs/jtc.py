import discord
from discord.ext import commands
from discord.ui import Button, View
from utils.variables import *
from utils.prefixes import *
from utils.loads import *
from utils.checks import *

class JoinToCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="jointocreate", aliases=['jtc', 'j2c'],  description="Configure the Join to Create channel", usage="jtc")
    async def jointocreate(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id) if ctx.guild else None
            prefix = guild_prefix(guild_id) if guild_id else '.'

            embed = discord.Embed(
                description=f"```yaml\n- [] = optional arguments\n- <> = required arguments\n- Do Not Type [] or <> While Using Commands!```"
                            f"{blnk}\n❓ jointocreate help overview\n\n"
                            f"**Create jointocreate channel**\n`{prefix}jtc setup`\n\n"
                            f"**View jointocreate channel**\n`{prefix}jtc show`\n\n"
                            f"**Reset jointocreate channel**\n`{prefix}jtc reset`\n{blnk}",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"{ctx.bot.user.name} Join To Create", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
            await ctx.reply(embed=embed, mention_author=False)


    @jointocreate.command(name="setup", description="Set up the Join to Create channel", usage="jtc setup")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def jointocreate_setup(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = ljtc()

        if guild_id in data:
            channel_id = data[guild_id].get("channel_id")
            if channel_id:
                channel = ctx.guild.get_channel(channel_id)


                if channel and discord.utils.get(ctx.guild.categories, id=channel.category_id):
                    embed = discord.Embed(
                        description=f"❗ The JointoCreate channel is already set up.",
                        color=colour
                    )
                    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                    await ctx.reply(embed=embed, mention_author=False)
                    return
                else:

                    del data[guild_id]
                    savejtc(data)
        

        category = discord.utils.get(ctx.guild.categories, name="Voice")
        if not category:
            category = await ctx.guild.create_category("Voice")


        channel = await ctx.guild.create_voice_channel(".☘︎ Join To Create", category=category)
        data[guild_id] = {"channel_id": channel.id, "memchs": {}}
        savejtc(data)

        embed = discord.Embed(
            description=f"{tick} Successfully created the Join to Create voice channel:\n{e_dot} {channel.mention}.",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text=f"{ctx.bot.user.name} Join To Create", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        await ctx.reply(embed=embed, mention_author=False)


    @jointocreate.command(name="show", description="Show the Join to Create channel", usage="jtc show")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def jointocreate_show(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = ljtc()

        if guild_id not in data:
            embed = discord.Embed(
                description=f"❗ No JointoCreate channel has been set up yet.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        channel_id = data[guild_id]["channel_id"]
        channel = ctx.guild.get_channel(channel_id)

        if not channel:
            embed = discord.Embed(
                description=f"❗ The JointoCreate channel has been deleted or is unavailable.\n"
                            f"You can set up a new one using `{guild_prefix(guild_id)}jtc setup`.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        embed = discord.Embed(
            description=f"{e_dot} The current JointoCreate channel is:\n{e_dot} {channel.mention}.",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text=f"{ctx.bot.user.name} Join To Create", icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        await ctx.reply(embed=embed, mention_author=False)


    @jointocreate.command(name="reset", description="Reset the 'Join to Create' channel", usage="jtc reset")
    @admin()
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def jointocreate_reset(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        data = ljtc()

        if guild_id not in data:
            embed = discord.Embed(
                description=f"❗ No JointoCreate channel is set up yet.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        channel_id = data[guild_id]["channel_id"]
        channel = ctx.guild.get_channel(channel_id)

        if not channel:
            embed = discord.Embed(
                description=f"❗ The JointoCreate channel has been deleted or is unavailable.\n"
                            f"You can reset it by setting up a new one using `{guild_prefix(guild_id)}jtc setup`.",
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed(
            description="❓ Are you sure you want to **reset the JointoCreate channel?**\n"
                        "❗ This action cannot be undone. The **channel** will be **deleted**.",
            color=colour
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        view = View(timeout=60)
        yoo = Button(label="Yes", style=discord.ButtonStyle.green)
        noo = Button(label="No", style=discord.ButtonStyle.danger)
        view.add_item(yoo)
        view.add_item(noo)

        async def confirm(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return
            
            await channel.delete()
            del data[guild_id]
            savejtc(data)

            embed = discord.Embed(
                description=f"{tick} Successfully reset the JointoCreate channel.",
                color=colour
            )
            await interaction.response.edit_message(embed=embed, view=None)

        async def cancel(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This interaction is not for you.", ephemeral=True)
                return

            embed = discord.Embed(
                description=f"❗ Action canceled.",
                color=colour
            )
            await interaction.response.edit_message(embed=embed, view=None)

        yoo.callback = confirm
        noo.callback = cancel

        await ctx.send(embed=embed, view=view)


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild_id = str(member.guild.id)
        data = ljtc()

        if guild_id not in data:
            return

        guild_data = data[guild_id]
        jtc_channel_id = guild_data.get("channel_id")
        if not jtc_channel_id:
            return

        jtc_channel = member.guild.get_channel(jtc_channel_id)
        if not jtc_channel:
            del data[guild_id]
            savejtc(data)
            return

        if "memchs" not in guild_data:
            guild_data["memchs"] = {}

        memchs = guild_data["memchs"]

        if after.channel and after.channel.id == jtc_channel_id:
            member_id = str(member.id)

            if member_id in memchs:
                prev_channel = member.guild.get_channel(memchs[member_id])
                if prev_channel is None or len(prev_channel.members) == 0:
                    if prev_channel:
                        await prev_channel.delete(reason="JTC | Owner rejoined JTC, old channel empty")
                    del memchs[member_id]

            new_channel = await member.guild.create_voice_channel(
                f".☘︎ {member.display_name}'s vc",
                category=jtc_channel.category,
                reason="Join To Create"
            )
            await new_channel.set_permissions(member, connect=True, speak=True)
            await member.move_to(new_channel, reason="Join To Create")
            memchs[member_id] = new_channel.id

        if before.channel:
            stale = [
                mid for mid, cid in memchs.items()
                if member.guild.get_channel(cid) is None
                or len(member.guild.get_channel(cid).members) == 0
            ]
            for mid in stale:
                ch = member.guild.get_channel(memchs[mid])
                if ch:
                    await ch.delete(reason="JTC | Channel empty")
                del memchs[mid]

        guild_data["memchs"] = memchs
        data[guild_id] = guild_data
        savejtc(data)


async def setup(bot):
    await bot.add_cog(JoinToCreate(bot))