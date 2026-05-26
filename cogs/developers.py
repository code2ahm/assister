import discord
from discord.ext import commands
from utils.prefixes import *
from utils.paginator import Ahm
from utils.checks import *
from utils.variables import *
from utils.blacklists import *

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    ###################################### NO PREFIX ############################################


    @commands.group(aliases=['np'], invoke_without_command=True)
    @is_developer()
    async def noprefix(self, ctx):
        embed = discord.Embed(
            title="",
            description=f"{grey} | **Subcommands** : `add`, `remove`, `show`",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)

    @noprefix.command(name='add')
    @is_developer()
    async def noprefix_add(self, ctx, user: discord.User):
        if user.id in noprefix:
            embed = discord.Embed(
                title="",
                description=f"{grey} | `{user.name}` is already in the noprefix list.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        noprefix.add(user.id)
        save_noprefix(noprefix)
        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully added `{user.name}` to the noprefix list.",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)

    @noprefix.command(name='remove')
    @is_developer()
    async def noprefix_remove(self, ctx, user: discord.User):
        if user.id not in noprefix:
            embed = discord.Embed(
                title="",
                description=f"{grey} | `{user.name}` is not in the noprefix list.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        noprefix.remove(user.id)
        save_noprefix(noprefix)
        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully removed `{user.name}` from the noprefix list.",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)


    @noprefix.command(name='show', aliases=['view', 'list'])
    @is_developer()
    async def noprefix_show(self, ctx: commands.Context):
        if not noprefix:
            embed = discord.Embed(
                title="",
                description=f"{grey} | The noprefix list is currently empty.",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        nplist = list(noprefix)
        tpage = 10
        pages = [nplist[i:i + tpage] for i in range(0, len(nplist), tpage)]

        def lodass(page_index):
            page = pages[page_index]
            description = "\n".join(
                f"`[{index + 1}]` | <@{user_id}> [[{user_id}](https://discord.com/users/{user_id})]"
                for index, user_id in enumerate(page, start=page_index * tpage)
            )
            embed = discord.Embed(
                title="",
                description=description,
                color=colour
            )
            embed.set_footer(text=f"Page {page_index + 1}/{len(pages)}")
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            return embed

        page_embeds = [lodass(page_index) for page_index in range(len(pages))]

        paginator = Ahm(page_embeds)
        await paginator.start(ctx)



    ############################## BLACKLIST USERS ####################################


    @commands.group(aliases=['bl'], invoke_without_command=True)
    @is_developer()
    async def blacklist(self, ctx: commands.Context):
        embed=discord.Embed(
            title="",
            description=f"{grey} | **Valid subcommands** : `add`, `remove`, `show`",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)

    @blacklist.command(name='add')
    @is_developer()
    async def blacklist_add(self, ctx: commands.Context, user: discord.User):
        if user.id in blacklisted_users:
            embed=discord.Embed(
                title="",
                description=f"{grey} | Already blacklisted",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        blacklisted_users.add(user.id)
        save_blacklist()
        embed=discord.Embed(
            title="",
            description=f"{tick} | Successfully blacklisted `{user.name}`",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)

    @blacklist.command(name='remove')
    @is_developer()
    async def blacklist_remove(self, ctx: commands.Context, user: discord.User):
        if user.id not in blacklisted_users:
            embed=discord.Embed(
                title="",
                description=f"{grey} | User not blacklisted",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        blacklisted_users.remove(user.id)
        save_blacklist()
        embed=discord.Embed(
            title="",
            description=f"{tick} | Successfully unblacklisted `{user.name}`",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)


    @blacklist.command(name='show', aliases=['list', 'view'])
    @is_developer()
    async def blacklist_show(self, ctx: commands.Context):
        if not blacklisted_users:
            embed = discord.Embed(
                title="",
                description=f"{grey} | No user is blacklisted",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        users = [f"{user_id}" for user_id in blacklisted_users]
        tpage = 10
        maxpages = (len(users) + tpage - 1) // tpage

        def lodass(page):
            stidx = page * tpage
            endidx = min((page + 1) * tpage, len(users))
            description = "\n".join(
                f"`[{index + 1}]` | <@{users[index]}> | [[{users[index]}](https://discord.com/users/{users[index]})]" 
                for index in range(stidx, endidx)
            )
            embed = discord.Embed(
                title="",
                description=description,
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Assister Blacklisted Users | Page {page + 1}/{maxpages}", icon_url=ctx.bot.user.avatar.url)
            return embed

        page_embeds = [lodass(page_index) for page_index in range(maxpages)]
        paginator = Ahm(page_embeds)
        await paginator.start(ctx)




    ################################### BLACKLIST SERVERS ########################################


    @commands.group(aliases=['blserver', 'blsv'], invoke_without_command=True)
    @is_developer()
    async def blacklistserver(self, ctx: commands.Context):
        embed = discord.Embed(
            title="",
            description=f"{grey} | **Valid subcommands** : `add`, `remove`, `show`",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)

    @blacklistserver.command(name='add')
    @is_developer()
    async def blacklistserver_add(self, ctx: commands.Context, server: discord.Guild, *, reason: str = "No reason provided"):
        server_id = server.id

        if server_id in blacklistedsv:
            embed = discord.Embed(
                title="",
                description=f"{grey} | Server ID `{server_id}` is already blacklisted",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        blacklistedsv.add(server_id)
        save_blacklistedsv(blacklistedsv)

        ahm_url = discord.ui.Button(style=discord.ButtonStyle.link, label="Developer", url="https://github.com/code2ahm")
        support_button = discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=support_server_link)

        loda = discord.ui.View()
        loda.add_item(ahm_url)
        loda.add_item(support_button)

        embed = discord.Embed(
            title="",
            description=f"❗ **This server has been blacklisted due to:** `{reason}`\n<:assister_colorserververified:1240011483560149033> You can join our **{support_server}** for appealing",
            color=colour
        )
        embed.set_author(name="This is an automated message.", icon_url=ctx.bot.user.avatar.url)

        for channel in server.text_channels:
            try:
                await channel.send(embed=embed, view=loda)
                break
            except discord.Forbidden:
                continue

        try:
            await server.leave()
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully added server to blacklist",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)


    @blacklistserver.command(name='remove')
    @is_developer()
    async def blacklistserver_remove(self, ctx: commands.Context, server: int):
        if server not in blacklistedsv:
            embed = discord.Embed(
                title="",
                description=f"{grey} | Server is not blacklisted",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        blacklistedsv.remove(server)
        save_blacklistedsv(blacklistedsv)
        embed = discord.Embed(
            title="",
            description=f"{tick} | Successfully removed server from blacklist.",
            color=colour
        )
        await ctx.reply(embed=embed, mention_author=False)

    @blacklistserver.command(name='show', aliases=['list', 'view'])
    @is_developer()
    async def blacklistserver_show(self, ctx: commands.Context):
        if not blacklistedsv:
            embed = discord.Embed(
                title="",
                description=f"{grey} | No server blacklisted",
                color=colour
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        svs = [str(server_id) for server_id in blacklistedsv]
        tpage = 10
        maxpages = len(svs) // tpage + (1 if len(svs) % tpage > 0 else 0)

        def lodass(page):
            stidx = page * tpage
            endidx = min((page + 1) * tpage, len(svs))
            description = "\n".join(f"`[{index + 1}]` | Server ID `{svs[index]}`" for index in range(stidx, endidx))
            embed = discord.Embed(
                title="",
                description=description,
                color=colour
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.set_footer(text=f"Assister Blacklisted Servers | Page {page + 1}/{maxpages}", icon_url=ctx.bot.user.avatar.url)
            return embed

        pages = [lodass(page) for page in range(maxpages)]
        paginator = Ahm(pages)
        await paginator.start(ctx)


    ######################################## SERVER LEAVE | SERVER INVITE #########################################

    @commands.command(aliases=['sinv'])
    @is_developer()
    async def serverinvite(self, ctx: commands.Context, server_id: int):

        if not ctx.author.id in developer_team_ids:
            return

        guild = ctx.bot.get_guild(server_id)
        if guild is None:
            await ctx.reply(f"{cross} | Guild not found", mention_author=False, delete_after=5)
            return
        
        if not guild.me.guild_permissions.create_instant_invite:
            await ctx.reply(f"{cross} | No perms", mention_author=False, delete_after=5)
            return

        text_channels = guild.text_channels
        if not text_channels:
            await ctx.reply(f"{cross} | No channel found", mention_author=False, delete_after=5)
            return

        channel = text_channels[0]
        
        try:
            invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)
            await ctx.reply(f"{invite.url}")
        except discord.Forbidden:
            await ctx.reply("No perms", mention_author=False, delete_after=5)
        except Exception as e:
            await ctx.reply(f"Error: {str(e)}", mention_author=False, delete_after=10)


    @commands.command()
    @is_developer()
    async def leavesv(self, ctx: commands.Context, gid: int):

        guild = ctx.bot.get_guild(gid)
        
        if guild is None:
            await ctx.reply("Server not found", mention_author=False)
            return

        await guild.leave()
        await ctx.reply(f"**{tick} | Successfully left the server: `{guild.name}` (ID: {gid})**", mention_author=False)



async def setup(bot):
    await bot.add_cog(Developer(bot))