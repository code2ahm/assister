import discord
from discord.ext import commands
from discord import app_commands
from utils.variables import *
import random
import asyncio
import time
import aiohttp


#  HELPERS

def _game_embed(description: str, author: str, icon_url: str = None,
                footer: str = None, footer_icon: str = None, color=None) -> discord.Embed:
    e = discord.Embed(description=description, color=color or colour)
    e.set_author(name=author, icon_url=icon_url)
    if footer:
        e.set_footer(text=footer, icon_url=footer_icon)
    return e


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot  = bot
        self.games: dict[int, object] = {}   # channel_id → game object/sentinel

    def _channel_busy(self, ctx: commands.Context) -> bool:
        return ctx.channel.id in self.games

    def _free(self, channel_id: int):
        self.games.pop(channel_id, None)

    #  TIC-TAC-TOE  — improved: win highlight, timeout, draw detection fix

    @commands.hybrid_command(name="tictactoe", aliases=["ttt"],
                             description="Play Tic-Tac-Toe with someone",
                             usage="ttt <user>")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(opponent="Who do you want to play against?")
    async def tictactoe(self, ctx: commands.Context, opponent: discord.Member):
        if self._channel_busy(ctx):
            return await ctx.reply("❌ A game is already running here!", mention_author=False, delete_after=5)
        if opponent.bot or opponent == ctx.author:
            return await ctx.reply("❌ Invalid opponent.", mention_author=False, delete_after=5)

        board   = [["" for _ in range(3)] for _ in range(3)]
        marks   = {ctx.author: "❌", opponent: "⚪"}
        players = [ctx.author, opponent]
        turn    = 0
        outer   = self

        WINNING_LINES = [
            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],  # rows
            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],  # cols
            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],                        # diags
        ]

        def check_winner():
            for line in WINNING_LINES:
                vals = [board[r][c] for r, c in line]
                if vals[0] and vals.count(vals[0]) == 3:
                    return vals[0], line
            return None, None

        def check_draw():
            return all(board[r][c] for r in range(3) for c in range(3))

        class TTTView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)
                self._build_buttons()

            def _build_buttons(self):
                for i in range(3):
                    for j in range(3):
                        self.add_item(TTTButton(i, j))
                self.add_item(StopButton())

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user not in players:
                    await interaction.response.send_message("❌ You're not in this game.", ephemeral=True)
                    return False
                return True

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await msg.edit(
                        embed=_game_embed(
                            f"⏰ Game timed out. {players[turn].mention} took too long.",
                            "Tic-Tac-Toe",
                        ),
                        view=self,
                    )
                except Exception:
                    pass
                outer._free(ctx.channel.id)

        class TTTButton(discord.ui.Button):
            def __init__(self, row, col):
                super().__init__(label="\u200b", style=discord.ButtonStyle.secondary, row=row)
                self.brow = row
                self.bcol = col

            async def callback(self, interaction: discord.Interaction):
                nonlocal turn
                if interaction.user != players[turn]:
                    return await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)

                mark = marks[interaction.user]
                board[self.brow][self.bcol] = mark
                self.label    = mark
                self.disabled = True
                self.style    = discord.ButtonStyle.success if mark == "❌" else discord.ButtonStyle.primary

                winner_mark, win_line = check_winner()
                if winner_mark:
                    winner = players[turn]
                    # Highlight winning cells green
                    for item in self.view.children:
                        if isinstance(item, TTTButton):
                            if (item.brow, item.bcol) in win_line:
                                item.style   = discord.ButtonStyle.success
                                item.disabled = True
                            else:
                                item.disabled = True
                    await interaction.response.edit_message(
                        embed=_game_embed(
                            f"## 🏆 {winner.mention} wins!\n"
                            f"{marks[players[0]]} {players[0].mention} vs {marks[players[1]]} {players[1].mention}",
                            "Tic-Tac-Toe",
                            icon_url=winner.display_avatar.url,
                        ),
                        view=self.view,
                    )
                    outer._free(ctx.channel.id)
                    return

                if check_draw():
                    for item in self.view.children:
                        item.disabled = True
                    await interaction.response.edit_message(
                        embed=_game_embed("## 🤝 It's a draw!", "Tic-Tac-Toe"),
                        view=self.view,
                    )
                    outer._free(ctx.channel.id)
                    return

                turn = 1 - turn
                await interaction.response.edit_message(
                    embed=_game_embed(
                        f"## {marks[players[turn]]} {players[turn].mention}'s turn!",
                        "Tic-Tac-Toe",
                        footer=f"{players[0].display_name} ❌  vs  ⚪ {players[1].display_name}",
                    ),
                    view=self.view,
                )

        class StopButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Stop Game", style=discord.ButtonStyle.danger, emoji="⛔", row=3)

            async def callback(self, interaction: discord.Interaction):
                if interaction.user not in players:
                    return await interaction.response.send_message("❌ Only players can stop the game.", ephemeral=True)
                for item in self.view.children:
                    item.disabled = True
                await interaction.response.edit_message(
                    embed=_game_embed(f"## 🛑 Game stopped by {interaction.user.mention}.", "Tic-Tac-Toe"),
                    view=self.view,
                )
                outer._free(ctx.channel.id)

        view = TTTView()
        self.games[ctx.channel.id] = view
        embed = _game_embed(
            f"## ❌ {players[0].mention}'s turn!\n"
            f"❌ {players[0].mention}  vs  ⚪ {players[1].mention}",
            "Tic-Tac-Toe",
            footer=f"Tap a cell to place your mark • Timeout: 120s",
        )
        msg = await ctx.reply(embed=embed, view=view, mention_author=False)

    #  ROCK PAPER SCISSORS  — improved: rematch button, cleaner result embed

    @commands.hybrid_command(name="rockpaperscissors", aliases=["rps"],
                             description="Play Rock-Paper-Scissors with someone",
                             usage="rps <user>")
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(opponent="Who do you want to play against?")
    async def rockpaperscissors(self, ctx: commands.Context, opponent: discord.Member):
        if self._channel_busy(ctx):
            return await ctx.reply("❌ A game is already running here!", mention_author=False, delete_after=5)
        if opponent.bot or opponent == ctx.author:
            return await ctx.reply("❌ Invalid opponent.", mention_author=False, delete_after=5)

        players = [ctx.author, opponent]
        outer   = self

        BEATS   = {"🪨": "✂️", "📄": "🪨", "✂️": "📄"}
        LABELS  = {"🪨": "🪨 Rock", "📄": "📄 Paper", "✂️": "✂️ Scissors"}

        async def run_game(reply_target, edit_msg=None):
            choices: dict[discord.Member, str] = {}
            self.games[ctx.channel.id] = choices

            class RPSView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.message = None
                    for emoji in ["🪨", "📄", "✂️"]:
                        self.add_item(RPSButton(emoji))
                    self.add_item(StopButton())

                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    if interaction.user not in players:
                        await interaction.response.send_message("❌ You're not in this game.", ephemeral=True)
                        return False
                    return True

                async def on_timeout(self):
                    for item in self.children:
                        item.disabled = True
                    missing = [p.display_name for p in players if p not in choices]
                    try:
                        await self.message.edit(
                            embed=_game_embed(
                                f"⏰ Timed out — **{', '.join(missing)}** didn't pick in time.",
                                "🪨📄✂️ Rock-Paper-Scissors",
                            ),
                            view=self,
                        )
                    except Exception:
                        pass
                    outer._free(ctx.channel.id)

            class RPSButton(discord.ui.Button):
                def __init__(self, emoji):
                    super().__init__(label=LABELS[emoji], style=discord.ButtonStyle.primary)
                    self.pick = emoji

                async def callback(self, interaction: discord.Interaction):
                    if interaction.user in choices:
                        return await interaction.response.send_message("✅ You already picked!", ephemeral=True)
                    choices[interaction.user] = self.pick
                    remaining = [p for p in players if p not in choices]
                    await interaction.response.send_message(
                        f"✅ Locked in: **{LABELS[self.pick]}**"
                        + (f"\n⌛ Waiting for {remaining[0].mention}…" if remaining else ""),
                        ephemeral=True,
                    )
                    if len(choices) == 2:
                        p1, p2 = players
                        c1, c2 = choices[p1], choices[p2]

                        if c1 == c2:
                            result = "## 🤝 It's a draw!"
                            winner = None
                        elif BEATS[c1] == c2:
                            result = f"## 🏆 {p1.mention} wins!"
                            winner = p1
                        else:
                            result = f"## 🏆 {p2.mention} wins!"
                            winner = p2

                        for item in self.view.children:
                            if not isinstance(item, RematchButton):
                                item.disabled = True

                        # Add rematch button
                        self.view.add_item(RematchButton())

                        rebd = discord.Embed(color=colour)
                        rebd.set_author(
                            name="🪨📄✂️ Rock-Paper-Scissors",
                            icon_url=winner.display_avatar.url if winner else ctx.bot.user.avatar.url,
                        )
                        rebd.description = (
                            f"{result}\n\n"
                            f"**Choices:**\n"
                            f"{e_dot} {LABELS[c1]}  →  {p1.mention}\n"
                            f"{e_dot} {LABELS[c2]}  →  {p2.mention}"
                        )
                        rebd.set_footer(text="Click Rematch for another round!")
                        await self.view.message.edit(embed=rebd, view=self.view)
                        outer._free(ctx.channel.id)

            class RematchButton(discord.ui.Button):
                def __init__(self):
                    super().__init__(label="Rematch", style=discord.ButtonStyle.success, emoji="🔄", row=1)

                async def callback(self, interaction: discord.Interaction):
                    if interaction.user not in players:
                        return await interaction.response.send_message("❌ Only players can rematch.", ephemeral=True)
                    await interaction.response.defer()
                    # Disable this view entirely
                    for item in self.view.children:
                        item.disabled = True
                    await self.view.message.edit(view=self.view)
                    await run_game(reply_target=None, edit_msg=self.view.message)

            class StopButton(discord.ui.Button):
                def __init__(self):
                    super().__init__(label="Stop", style=discord.ButtonStyle.danger, emoji="⛔", row=1)

                async def callback(self, interaction: discord.Interaction):
                    if interaction.user not in players:
                        return await interaction.response.send_message("❌ Only players can stop.", ephemeral=True)
                    for item in self.view.children:
                        item.disabled = True
                    await interaction.response.edit_message(
                        embed=_game_embed(f"## 🛑 Game stopped by {interaction.user.mention}.", "🪨📄✂️ Rock-Paper-Scissors"),
                        view=self.view,
                    )
                    outer._free(ctx.channel.id)

            view = RPSView()
            embed = discord.Embed(color=colour)
            embed.set_author(name="🪨📄✂️ Rock-Paper-Scissors", icon_url=ctx.bot.user.avatar.url)
            embed.description = (
                f"## {ctx.author.mention} vs {opponent.mention}\n\n"
                f"Both players pick secretly — choose below!"
            )
            embed.set_footer(text="Picks are hidden until both players choose • Timeout: 60s")

            if edit_msg:
                m = await edit_msg.reply(embed=embed, view=view, mention_author=False)
            elif reply_target:
                m = await reply_target.reply(embed=embed, view=view, mention_author=False)
            else:
                m = await ctx.channel.send(embed=embed, view=view)

            view.message = m

        await run_game(reply_target=ctx.message)

    #  QUICK REACTION  — improved: leaderboard for multiple rounds, faster UX

    @commands.hybrid_command(name="reaction", description="Quick emoji reaction game",
                             usage="reaction [rounds]")
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(rounds="Number of rounds to play (1–5, default 1)")
    async def reaction(self, ctx: commands.Context, rounds: int = 1):
        if self._channel_busy(ctx):
            return await ctx.reply("❌ A game is already running here!", mention_author=False, delete_after=5)

        rounds = max(1, min(rounds, 5))
        emojis = ["<a:stolen_emoji_blaze:1499732756265963602>", "<:haromi_:1290890168324063274>",
                  "<:Doggy:1346169435060306021>", "<:shareef:1499463506205081632>"]

        self.games[ctx.channel.id] = True
        scores: dict[discord.Member, int] = {}

        msg = await ctx.reply(
            embed=_game_embed(
                f"⚡ **Quick Reaction Game — {rounds} round{'s' if rounds > 1 else ''}**\n"
                f"React to the correct emoji as fast as possible!",
                "Quick Reaction",
                icon_url=ctx.bot.user.avatar.url,
            ),
            mention_author=False,
        )

        for rnd in range(1, rounds + 1):
            target = random.choice(emojis)
            decoys  = [e for e in emojis if e != target]
            shown   = random.sample(decoys, k=min(2, len(decoys))) + [target]
            random.shuffle(shown)

            countdown_embed = _game_embed(
                f"**Round {rnd}/{rounds}**\n\n"
                f"Adding reactions… get ready!",
                "Quick Reaction",
                icon_url=ctx.bot.user.avatar.url,
            )
            await msg.edit(embed=countdown_embed)

            # Add reactions
            for e in shown:
                try:
                    await msg.add_reaction(e)
                except Exception:
                    pass

            # Countdown
            for t in [3, 2, 1]:
                await asyncio.sleep(1)
                await msg.edit(embed=_game_embed(
                    f"**Round {rnd}/{rounds}** — React in `{t}`…",
                    "Quick Reaction",
                    icon_url=ctx.bot.user.avatar.url,
                ))

            reveal_embed = _game_embed(
                f"**Round {rnd}/{rounds}** — React to → {target}",
                "Quick Reaction",
                icon_url=ctx.bot.user.avatar.url,
                footer="First correct reaction wins the round!",
            )
            await msg.edit(embed=reveal_embed)
            start = time.time()

            def check(reaction, user):
                return (
                    reaction.message.id == msg.id
                    and str(reaction.emoji) == target
                    and not user.bot
                )

            try:
                reaction, winner = await ctx.bot.wait_for("reaction_add", timeout=10.0, check=check)
                elapsed = time.time() - start
                scores[winner] = scores.get(winner, 0) + 1

                round_embed = _game_embed(
                    f"**Round {rnd}/{rounds}** — {target}\n\n"
                    f"🏆 {winner.mention} reacted in **{elapsed:.2f}s**!",
                    "Quick Reaction",
                    icon_url=winner.display_avatar.url,
                )
                await msg.edit(embed=round_embed)
            except asyncio.TimeoutError:
                await msg.edit(embed=_game_embed(
                    f"**Round {rnd}/{rounds}** — {target}\n\n⏰ Nobody reacted in time!",
                    "Quick Reaction",
                    icon_url=ctx.bot.user.avatar.url,
                ))

            # Clear reactions between rounds
            try:
                await msg.clear_reactions()
            except Exception:
                pass

            if rnd < rounds:
                await asyncio.sleep(2)

        # Final leaderboard
        self._free(ctx.channel.id)
        if scores:
            board = "\n".join(
                f"{'🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else '▫️'} "
                f"{member.mention} — **{pts} pt{'s' if pts > 1 else ''}**"
                for i, (member, pts) in enumerate(sorted(scores.items(), key=lambda x: -x[1]))
            )
            final_embed = _game_embed(
                f"## 🏁 Game Over!\n\n**Leaderboard:**\n{board}",
                "Quick Reaction — Results",
                icon_url=ctx.bot.user.avatar.url,
            )
        else:
            final_embed = _game_embed("## 🏁 Game Over!\nNobody scored a single point. 💀",
                                      "Quick Reaction — Results",
                                      icon_url=ctx.bot.user.avatar.url)
        await msg.edit(embed=final_embed)


    HANGMAN_STAGES = [
        "```\n  +---+\n      |\n      |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  O   |\n      |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  O   |\n  |   |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  O   |\n /|   |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  O   |\n /|\\  |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  O   |\n /|\\  |\n /    |\n      |\n      |\n=========```",
        "```\n  +---+\n  O   |\n /|\\  |\n / \\  |\n      |\n      |\n=========```",
    ]

    WORD_LIST = [
        "python", "discord", "hangman", "keyboard", "monitor", "variable",
        "function", "database", "algorithm", "framework", "interface",
        "penguin", "elephant", "volcano", "gravity", "quantum", "oxygen",
        "library", "network", "protocol", "lightning", "skeleton",
        "satellite", "marathon", "champion", "treasure", "adventure",
    ]

    @commands.hybrid_command(name="hangman", description="Play Hangman in the channel",
                             usage="hangman")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def hangman(self, ctx: commands.Context):
        if self._channel_busy(ctx):
            return await ctx.reply("❌ A game is already running here!", mention_author=False, delete_after=5)

        word     = random.choice(self.WORD_LIST)
        guessed  = set()
        wrong    = []
        max_wrong = len(self.HANGMAN_STAGES) - 1
        outer    = self

        self.games[ctx.channel.id] = True

        def display_word():
            return " ".join(c if c in guessed else r"\_" for c in word)

        def make_embed():
            stage    = len(wrong)
            won      = all(c in guessed for c in word)
            lost     = stage >= max_wrong
            progress = display_word()
            wrong_str = " ".join(f"`{c}`" for c in wrong) or "None yet"

            if won:
                desc = (
                    f"## 🎉 You got it!\n"
                    f"The word was **`{word}`**!\n\n"
                    f"Wrong guesses: {wrong_str}"
                )
            elif lost:
                desc = (
                    f"## 💀 Game over!\n"
                    f"The word was **`{word}`**\n\n"
                    f"{self.HANGMAN_STAGES[stage]}"
                )
            else:
                desc = (
                    f"{self.HANGMAN_STAGES[stage]}\n"
                    f"**Word:** {progress}\n\n"
                    f"{e_dot} Wrong guesses ({stage}/{max_wrong}): {wrong_str}\n"
                    f"{e_dot} Use the buttons below to guess a letter!"
                )
            return _game_embed(desc, "Hangman", icon_url=ctx.bot.user.avatar.url,
                               footer=f"Requested by {ctx.author.display_name}")

        class HangmanView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.message = None
                self._build()

            def _build(self):
                # A-Z across rows of 5
                alphabet = "abcdefghijklmnopqrstuvwxyz"
                row = 0
                for i, letter in enumerate(alphabet):
                    if i > 0 and i % 5 == 0:
                        row += 1
                    if row > 4:
                        break   # Discord max 5 rows
                    self.add_item(LetterButton(letter, row))

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(
                        embed=_game_embed(
                            f"⏰ Game timed out! The word was **`{word}`**.",
                            "Hangman",
                            icon_url=ctx.bot.user.avatar.url,
                        ),
                        view=self,
                    )
                except Exception:
                    pass
                outer._free(ctx.channel.id)

        class LetterButton(discord.ui.Button):
            def __init__(self, letter, row):
                super().__init__(label=letter.upper(),
                                 style=discord.ButtonStyle.secondary,
                                 row=row)
                self.letter = letter

            async def callback(self, interaction: discord.Interaction):
                if self.letter in guessed or self.letter in wrong:
                    return await interaction.response.send_message("Already guessed!", ephemeral=True)

                if self.letter in word:
                    guessed.add(self.letter)
                    self.style    = discord.ButtonStyle.success
                    self.disabled = True
                else:
                    wrong.append(self.letter)
                    self.style    = discord.ButtonStyle.danger
                    self.disabled = True

                won  = all(c in guessed for c in word)
                lost = len(wrong) >= max_wrong

                if won or lost:
                    for item in self.view.children:
                        item.disabled = True
                    outer._free(ctx.channel.id)

                await interaction.response.edit_message(embed=make_embed(), view=self.view)

        view = HangmanView()
        self.games[ctx.channel.id] = True
        msg  = await ctx.reply(embed=make_embed(), view=view, mention_author=False)
        view.message = msg


    #  HIGHER OR LOWER  — number guessing game

    @commands.hybrid_command(name="higherorlower", aliases=["hol", "guess"],
                             description="Guess the secret number — higher or lower?",
                             usage="higherorlower [max]")
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(maximum="Upper bound for the number (default 100)")
    async def higherorlower(self, ctx: commands.Context, maximum: int = 100):
        if self._channel_busy(ctx):
            return await ctx.reply("❌ A game is already running here!", mention_author=False, delete_after=5)

        maximum = max(10, min(maximum, 1000))
        secret  = random.randint(1, maximum)
        attempts = 0
        outer   = self
        self.games[ctx.channel.id] = True

        embed = _game_embed(
            f"## 🔢 Guess the number!\n\n"
            f"I'm thinking of a number between **1** and **{maximum}**.\n"
            f"Type your guess in chat! You have **60 seconds** per guess.\n\n"
            f"Type `stop` to quit.",
            "Higher or Lower",
            icon_url=ctx.bot.user.avatar.url,
        )
        await ctx.reply(embed=embed, mention_author=False)

        def check(m: discord.Message):
            return m.channel == ctx.channel and m.author == ctx.author

        while True:
            try:
                msg = await ctx.bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send(embed=_game_embed(
                    f"⏰ You took too long! The number was **`{secret}`**.",
                    "Higher or Lower",
                    icon_url=ctx.bot.user.avatar.url,
                ))
                break

            if msg.content.lower() == "stop":
                await ctx.channel.send(embed=_game_embed(
                    f"🛑 Game stopped. The number was **`{secret}`**.",
                    "Higher or Lower",
                    icon_url=ctx.bot.user.avatar.url,
                ))
                break

            try:
                guess = int(msg.content.strip())
            except ValueError:
                await ctx.channel.send("❌ That's not a valid number — try again.", delete_after=4)
                continue

            attempts += 1

            if guess == secret:
                await ctx.channel.send(embed=_game_embed(
                    f"## 🎉 {ctx.author.mention} got it!\n\n"
                    f"The number was **`{secret}`** — found in **{attempts} guess{'es' if attempts > 1 else ''}**!",
                    "Higher or Lower",
                    icon_url=ctx.author.display_avatar.url,
                ))
                break
            elif guess < secret:
                hint = "📈 **Higher!**"
            else:
                hint = "📉 **Lower!**"

            await ctx.channel.send(embed=_game_embed(
                f"{hint}\nYour guess: `{guess}` | Attempts: `{attempts}`",
                "Higher or Lower",
                icon_url=ctx.bot.user.avatar.url,
            ), delete_after=10)

        self._free(ctx.channel.id)

    #  WORD SCRAMBLE

    SCRAMBLE_WORDS = [
        "python", "discord", "server", "channel", "member", "message",
        "keyboard", "monitor", "network", "browser", "penguin", "volcano",
        "gravity", "quantum", "library", "timeout", "webhook", "command",
        "reaction", "mention", "profile", "sticker", "nitro",
    ]

    @commands.hybrid_command(name="wordscramble", aliases=["scramble"],
                             description="Unscramble the word before time runs out",
                             usage="wordscramble")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def wordscramble(self, ctx: commands.Context):
        if self._channel_busy(ctx):
            return await ctx.reply("❌ A game is already running here!", mention_author=False, delete_after=5)

        word     = random.choice(self.SCRAMBLE_WORDS)
        letters  = list(word)
        # Ensure the scramble is actually different from the original
        for _ in range(20):
            random.shuffle(letters)
            if "".join(letters) != word:
                break
        scrambled = "".join(letters)

        self.games[ctx.channel.id] = True

        embed = _game_embed(
            f"## 🔀 Unscramble this word!\n\n"
            f"**`{scrambled.upper()}`**\n\n"
            f"Type the correct word in chat — you have **20 seconds**!\n"
            f"Type `hint` for a letter hint (-1 point).",
            "Word Scramble",
            icon_url=ctx.bot.user.avatar.url,
            footer=f"Requested by {ctx.author.display_name}",
        )
        msg = await ctx.reply(embed=embed, mention_author=False)

        hint_used = False
        scores: dict[discord.Member, int] = {}

        def check(m: discord.Message):
            return m.channel == ctx.channel and not m.author.bot

        deadline = asyncio.get_event_loop().time() + 20

        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            try:
                resp = await ctx.bot.wait_for("message", timeout=remaining, check=check)
            except asyncio.TimeoutError:
                break

            if resp.content.lower() == "hint" and not hint_used:
                hint_used = True
                hint_letter = word[0]
                await ctx.channel.send(
                    f"💡 Hint: The word starts with **`{hint_letter.upper()}`**",
                    delete_after=10,
                )
                continue

            if resp.content.strip().lower() == word:
                pts = 1 if not hint_used else 0
                winner = resp.author
                self._free(ctx.channel.id)
                await msg.edit(embed=_game_embed(
                    f"## 🎉 {winner.mention} got it!\n\n"
                    f"**`{scrambled.upper()}`** → **`{word.upper()}`**\n\n"
                    f"{'⭐ +1 point (no hint used)' if not hint_used else '✅ Correct (hint was used)'}",
                    "Word Scramble",
                    icon_url=winner.display_avatar.url,
                ))
                return

        self._free(ctx.channel.id)
        await msg.edit(embed=_game_embed(
            f"## ⏰ Time's up!\n\n"
            f"**`{scrambled.upper()}`** → **`{word.upper()}`**\n\n"
            f"Nobody got it in time!",
            "Word Scramble",
            icon_url=ctx.bot.user.avatar.url,
        ))

    #  TRIVIA

    TRIVIA = [
        ("What is the capital of Japan?",                   ["tokyo"], "🌏"),
        ("How many sides does a hexagon have?",             ["6", "six"], "🔷"),
        ("What gas do plants absorb from the atmosphere?",  ["co2", "carbon dioxide"], "🌿"),
        ("What is the fastest land animal?",                ["cheetah"], "🐆"),
        ("How many colors are in a rainbow?",               ["7", "seven"], "🌈"),
        ("What planet is known as the Red Planet?",         ["mars"], "🔴"),
        ("What is the chemical symbol for gold?",           ["au"], "🥇"),
        ("Who wrote Romeo and Juliet?",                     ["shakespeare", "william shakespeare"], "🎭"),
        ("What is the largest ocean on Earth?",             ["pacific", "pacific ocean"], "🌊"),
        ("How many bones are in the adult human body?",     ["206"], "🦴"),
        ("What is the square root of 144?",                 ["12", "twelve"], "🔢"),
        ("What is the smallest prime number?",              ["2", "two"], "🔢"),
        ("What language was Python named after?",           ["monty python", "monty python's flying circus"], "🐍"),
        ("What year did the Titanic sink?",                 ["1912"], "🚢"),
        ("How many strings does a standard guitar have?",   ["6", "six"], "🎸"),
    ]

    @commands.hybrid_command(name="trivia", description="Answer a trivia question first to win",
                             usage="trivia")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trivia(self, ctx: commands.Context):
        if self._channel_busy(ctx):
            return await ctx.reply("❌ A game is already running here!", mention_author=False, delete_after=5)

        question, answers, emoji = random.choice(self.TRIVIA)
        self.games[ctx.channel.id] = True

        embed = _game_embed(
            f"## {emoji} Trivia Time!\n\n"
            f"**{question}**\n\n"
            f"Type your answer in chat — ⏰ **20 seconds**!",
            "Trivia",
            icon_url=ctx.bot.user.avatar.url,
            footer="First correct answer wins!",
        )
        await ctx.reply(embed=embed, mention_author=False)

        def check(m: discord.Message):
            return m.channel == ctx.channel and not m.author.bot

        correct_answer = answers[0]

        try:
            while True:
                resp = await ctx.bot.wait_for("message", timeout=20.0, check=check)
                if resp.content.strip().lower() in [a.lower() for a in answers]:
                    await ctx.channel.send(embed=_game_embed(
                        f"## 🏆 {resp.author.mention} got it!\n\n"
                        f"**{question}**\n"
                        f"✅ Answer: **`{correct_answer.title()}`**",
                        "Trivia",
                        icon_url=resp.author.display_avatar.url,
                    ))
                    break
        except asyncio.TimeoutError:
            await ctx.channel.send(embed=_game_embed(
                f"## ⏰ Time's up!\n\n"
                f"**{question}**\n"
                f"The answer was **`{correct_answer.title()}`**",
                "Trivia",
                icon_url=ctx.bot.user.avatar.url,
            ))

        self._free(ctx.channel.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))