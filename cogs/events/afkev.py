import discord
from discord.ext import commands
from utils.loads import lafk, saveafk, kalaloda
from utils.prefixes import *
from utils.variables import *

class AfkEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        guild_id = str(message.guild.id) if message.guild else None
        prefix = guild_prefix(guild_id) if guild_id else '.'

        fk = lafk()

        if message.content.lower().startswith(f"{prefix}afk") or message.content.lower().startswith("afk"):
            return

        if str(message.author.id) in fk:
            afk_info = fk.pop(str(message.author.id))
            saveafk(fk)

            tunix = kalaloda(afk_info['timestamp'])
            await message.reply(
                f"Welcome back, {message.author.mention}! You were AFK for <t:{tunix}:R>.",
                mention_author=False
            )
            return

        if message.mentions:
            for mention in message.mentions:
                if str(mention.id) in fk:
                    afk_info = fk[str(mention.id)]
                    tunix = kalaloda(afk_info['timestamp'])
                    await message.reply(
                        f"{mention} is AFK with reason: **{afk_info['reason']}** - <t:{tunix}:R>.",
                        mention_author=False
                    )
                    return

        if message.content.strip() == '<@1496794996228231229>':

            server_name = message.guild.name
            user_name = message.author.name

            guild_id = str(message.guild.id) if message.guild else None
            prefix = guild_prefix(guild_id) if guild_id else '.'

            embed = discord.Embed(
                title="",
                description=f"My prefix: `{prefix}`\nTry:- `{prefix}help` or `/help`\nTo get more info, type `{prefix}help <category/command>`",
                color=colour
            )
            embed.set_author(name=message.author, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)     

            inv="https://discord.com/oauth2/authorize?client_id=1496794996228231229&permissions=8&integration_type=0&scope=bot"

            sapot = discord.ui.Button(style=discord.ButtonStyle.link, label="  Support Server", url=support_server_link)
            invb = discord.ui.Button(style=discord.ButtonStyle.link, label="Invite Me", url=inv)
            web = discord.ui.Button(style=discord.ButtonStyle.link, label="Website", url="https://assisterbot.xyz/")
            
            lund = discord.ui.View()
            lund.add_item(web)
            lund.add_item(invb)
            lund.add_item(sapot)

            reference = await message.channel.fetch_message(message.id)
            await message.channel.send(embed=embed, reference=reference, view=lund , mention_author=False)

async def setup(bot):
    await bot.add_cog(AfkEvent(bot))