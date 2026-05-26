import discord
import aiohttp
from discord.ext import commands
from utils.variables import *
from utils.blacklists import *


class JoinLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_webhook(self, webhook_url, embed):
        async with aiohttp.ClientSession() as session:
            webhook_payload = {
                "username": "Assister Logs",
                "embeds": [embed.to_dict()]
            }
            async with session.post(webhook_url, json=webhook_payload) as response:
                if response.status != 204:
                    print(f"Failed to send webhook: {response.status}")


    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        joinhook = "https://discord.com/api/webhooks/1497204715581079643/V0R69L2FTDq9d_cvqfPPVXwFNyv3xi8OVupxsh3yYmoZyuLpKUwwun1re8J9SoXZ-75k"

        ttlh = sum(1 for member in guild.members if not member.bot)
        ttlb = sum(1 for member in guild.members if member.bot)

        bjtime = guild.me.joined_at if guild.me else None

        svtstamp = int(guild.created_at.timestamp())
        tstamp = int(bjtime.timestamp()) if bjtime else 'N/A'

        created_at = f"<t:{svtstamp}:F>"
        bjtime = f"<t:{tstamp}:F>" if bjtime != 'N/A' else 'N/A'

        features = ", ".join(guild.features) if guild.features else "None"
        verification_level = guild.verification_level
        icon_url = guild.icon.url if guild.icon else None
        banneri = guild.banner.url if guild.banner else None

        owner = guild.owner
        ttlmembs = guild.member_count
        botmembs = ttlb
        hmembs = ttlh
        txtchs = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        rls = len(guild.roles) - 1
        ttlchnls = len(guild.channels)
        ltxts = sum(1 for channel in guild.text_channels if channel.overwrites_for(guild.default_role).read_messages is False)
        lvcs = sum(1 for channel in guild.voice_channels if channel.overwrites_for(guild.default_role).connect is False)

        chinfo = (
            f"**Total Channels:** {ttlchnls}\n"
            f"{tick} **Text Channels:** {txtchs} ({ltxts} locked)\n"
            f"{tick} **Voice Channels:** {voice_channels} ({lvcs} locked)"
        )

        rulesch = f"{'📜'} {guild.rules_channel.mention if guild.rules_channel else 'None'}"
        bootsts = f"Level: <:assister_colorboostnitro:1240047535712768100> {guild.premium_tier} [{guild.premium_subscription_count} boosts]"

        emojiss = (
            f"**Regular Emojis:** {len([emoji for emoji in guild.emojis if not emoji.animated])}\n"
            f"{tick} **Animated Emojis:** {len([emoji for emoji in guild.emojis if emoji.animated])}\n"
            f"{tick} **Total Emojis:** {len(guild.emojis)}"
        )

        embed = discord.Embed(
            title="",
            description=(
                f"## <:haromi_:1290890168324063274> {guild.name}\n"
                f"{tick} **Owner:** <@{owner.id}> [[{owner.id}](https://discord.com/users/{owner.id})]\n"
                f"{tick} **Creation Time:** {created_at}\n"
                f"{tick} **Bot Join Time:** {bjtime}\n"
                f"{tick} **Total Members:** {ttlmembs}\n"
                f"{tick} **Bot Members:** {botmembs}\n"
                f"{tick} **Human Members:** {hmembs}\n\n"
                f"{tick} {chinfo}\n\n"
                f"{tick} **Rules Channel:** {rulesch}\n"
                f"{tick} **Roles Count:** {rls}\n"
                f"{tick} **Boost Status:** {bootsts}\n\n"
                f"{tick} {emojiss}\n\n"
                f"{tick} **Features:** {features}\n"
                f"{tick} **Verification Level:** {verification_level}\n"
            ),
            color=colour
        )

        if icon_url:
            embed.set_thumbnail(url=icon_url)
        if banneri:
            embed.set_image(url=banneri)

        embed.set_footer(text=f"Server ID: {guild.id}", icon_url=self.bot.user.avatar.url)
        await self.send_webhook(joinhook, embed)

        ahm_url = discord.ui.Button(style=discord.ButtonStyle.link, label="Developer", url="https://github.com/code2ahm")
        support_button = discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=support_server_link)

        loda = discord.ui.View()
        loda.add_item(ahm_url)
        loda.add_item(support_button)

        if guild.id in blacklistedsv:
            try:
                for channel in guild.text_channels:
                    try:
                        embed = discord.Embed(
                            title="",
                            description=f"❗ **This server has been blacklisted**\n<:assister_colorserververified:1240011483560149033> You can join **{support_server}** for appealing.",
                            color=colour
                        )
                        embed.set_author(name="This is an automated message. Follow the instructions below", icon_url=self.bot.user.avatar.url)

                        await channel.send(embed=embed, view=loda)
                        break
                    except discord.Forbidden:
                        continue

                await guild.leave()
                print(f"Left blacklisted server: {guild.name}")
            except Exception as e:
                print(e)




    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        leavehook = "https://discord.com/api/webhooks/1497204893558247426/jrAYi9NEGo8McrwA4CdwTi_lPTkxuuWwcnDqP1eIWoxtV0S7zh8uOEk15L5sUWjYuUlT"

        ttlh = sum(1 for member in guild.members if not member.bot)
        ttlb = sum(1 for member in guild.members if member.bot)

        bjtime = guild.me.joined_at if guild.me else None

        svtstamp = int(guild.created_at.timestamp())
        tstamp = int(bjtime.timestamp()) if bjtime else 'N/A'

        created_at = f"<t:{svtstamp}:F>"
        bjtime = f"<t:{tstamp}:F>" if bjtime != 'N/A' else 'N/A'

        features = ", ".join(guild.features) if guild.features else "None"
        verification_level = guild.verification_level
        icon_url = guild.icon.url if guild.icon else None
        banneri = guild.banner.url if guild.banner else None

        owner = guild.owner
        ttlmembs = guild.member_count
        botmembs = ttlb
        hmembs = ttlh
        txtchs = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        rls = len(guild.roles) - 1
        ttlchnls = len(guild.channels)
        ltxts = sum(1 for channel in guild.text_channels if channel.overwrites_for(guild.default_role).read_messages is False)
        lvcs = sum(1 for channel in guild.voice_channels if channel.overwrites_for(guild.default_role).connect is False)

        chinfo = (
            f"**Total Channels:** {ttlchnls}\n"
            f"{tick} **Text Channels:** {txtchs} ({ltxts} locked)\n"
            f"{tick} **Voice Channels:** {voice_channels} ({lvcs} locked)"
        )

        rulesch = f"{'📜'} {guild.rules_channel.mention if guild.rules_channel else 'None'}"
        bootsts = f"Level: <:assister_colorboostnitro:1240047535712768100> {guild.premium_tier} [{guild.premium_subscription_count} boosts]"

        emojiss = (
            f"**Regular Emojis:** {len([emoji for emoji in guild.emojis if not emoji.animated])}\n"
            f"{tick} **Animated Emojis:** {len([emoji for emoji in guild.emojis if emoji.animated])}\n"
            f"{tick} **Total Emojis:** {len(guild.emojis)}"
        )

        embed = discord.Embed(
            title="",
            description=(
                f"## <a:bionic_g_offline:1261552732913799170> {guild.name}\n"
                f"{tick} **Owner:** {owner}\n"
                f"{tick} **Creation Time:** {created_at}\n"
                f"{tick} **Bot Join Time:** {bjtime}\n"
                f"{tick} **Total Members:** {ttlmembs}\n"
                f"{tick} **Bot Members:** {botmembs}\n"
                f"{tick} **Human Members:** {hmembs}\n\n"
                f"{tick} {chinfo}\n\n"
                f"{tick} **Rules Channel:** {rulesch}\n"
                f"{tick} **Roles Count:** {rls}\n"
                f"{tick} **Boost Status:** {bootsts}\n\n"
                f"{tick} {emojiss}\n\n"
                f"{tick} **Features:** {features}\n"
                f"{tick} **Verification Level:** {verification_level}\n"
            ),
            color=discord.Color.red()
        )

        if icon_url:
            embed.set_thumbnail(url=icon_url)
        if banneri:
            embed.set_image(url=banneri)

        embed.set_footer(text=f"Server ID: {guild.id}", icon_url=self.bot.user.avatar.url)
        await self.send_webhook(leavehook, embed)


async def setup(bot):
    await bot.add_cog(JoinLeave(bot))