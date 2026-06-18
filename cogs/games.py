import discord
from discord.ext import commands
from discord import app_commands, ui
from utils.variables import *
import random
import asyncio
import time
import aiohttp
import html

HANGMAN_STAGES = [
    "```\n  +---+\n      |\n      |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  O   |\n      |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  O   |\n  |   |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  O   |\n /|   |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  O   |\n /|\\  |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  O   |\n /|\\  |\n /    |\n      |\n      |\n=========```",
    "```\n  +---+\n  O   |\n /|\\  |\n / \\  |\n      |\n      |\n=========```",
]

FALLBACK_WORDS = [
    "python", "discord", "server", "channel", "member", "message",
    "keyboard", "monitor", "network", "browser", "penguin", "volcano",
    "gravity", "quantum", "library", "timeout", "webhook", "command",
    "reaction", "mention", "profile", "sticker", "nitro", "bridge",
    "jacket", "planet", "rocket", "silver", "window", "garden",
]

FALLBACK_TRIVIA = [
    ("What is the capital of Japan?", ["tokyo"], "\U0001f30f"),
    ("How many sides does a hexagon have?", ["6", "six"], "\U0001f537"),
    ("What gas do plants absorb from the atmosphere?", ["co2", "carbon dioxide"], "\U0001f33f"),
    ("What is the fastest land animal?", ["cheetah"], "\U0001f406"),
    ("How many colors are in a rainbow?", ["7", "seven"], "\U0001f308"),
    ("What planet is known as the Red Planet?", ["mars"], "\U0001f534"),
    ("What is the chemical symbol for gold?", ["au"], "\U0001f947"),
    ("Who wrote Romeo and Juliet?", ["shakespeare", "william shakespeare"], "\U0001f3ad"),
    ("What is the largest ocean on Earth?", ["pacific", "pacific ocean"], "\U0001f30a"),
    ("How many bones are in the adult human body?", ["206"], "\U0001f9b4"),
    ("What is the square root of 144?", ["12", "twelve"], "\U0001f522"),
    ("What is the smallest prime number?", ["2", "two"], "\U0001f522"),
    ("What language was Python named after?", ["monty python", "monty python's flying circus"], "\U0001f40d"),
    ("What year did the Titanic sink?", ["1912"], "\U0001f6a2"),
    ("How many strings does a standard guitar have?", ["6", "six"], "\U0001f3b8"),
]

REACTION_EMOJIS = ["<a:stolen_emoji_blaze:1499732756265963602>", "<:haromi_:1290890168324063274>",
                  "<:Doggy:1346169435060306021>", "<:shareef:1499463506205081632>"]

def _layout(title: str, body: str, footer: str = None) -> ui.LayoutView:
    layout = ui.LayoutView()
    c = ui.Container()
    parts = []
    if title:
        parts.append(f"## {title}")
    if body:
        parts.append(body)
    c.add_item(ui.TextDisplay("\n\n".join(parts)))
    if footer:
        c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        c.add_item(ui.TextDisplay(footer))
    layout.add_item(c)
    return layout


def _resp(text: str) -> ui.LayoutView:
    layout = ui.LayoutView()
    c = ui.Container()
    c.add_item(ui.TextDisplay(text))
    layout.add_item(c)
    return layout


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games: dict[str, object] = {}
        self._session: aiohttp.ClientSession = None

    async def cog_load(self):
        self._session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self._session:
            await self._session.close()

    def _key(self, ctx: commands.Context, game: str) -> str:
        return f"{ctx.channel.id}:{game}"

    def _channel_busy(self, ctx: commands.Context, game: str) -> bool:
        return self._key(ctx, game) in self.games

    def _free(self, ctx: commands.Context, game: str):
        self.games.pop(self._key(ctx, game), None)

    async def _fetch_word(self) -> str:
        try:
            async with self._session.get(
                "https://random-word-api.herokuapp.com/word?number=1", timeout=5
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if data and len(data[0]) >= 4:
                        return data[0].lower()
        except Exception:
            pass
        return random.choice(FALLBACK_WORDS)

    async def _fetch_definition(self, word: str) -> str:
        try:
            async with self._session.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=5
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if data and "meanings" in data[0]:
                        for m in data[0]["meanings"]:
                            if "definitions" in m and m["definitions"]:
                                return m["definitions"][0]["definition"]
        except Exception:
            pass
        return None

    async def _fetch_trivia(self, difficulty: str = None) -> dict:
        url = "https://opentdb.com/api.php?amount=1"
        if difficulty and difficulty in ("easy", "medium", "hard"):
            url += f"&difficulty={difficulty}"
        try:
            async with self._session.get(url, timeout=8) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("response_code") == 0 and data["results"]:
                        return data["results"][0]
        except Exception:
            pass
        return None

    @commands.hybrid_command(name="tictactoe", aliases=["ttt"],
                             description="Play Tic-Tac-Toe with someone",
                             usage="ttt <user>")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(opponent="Who do you want to play against?")
    async def tictactoe(self, ctx: commands.Context, opponent: discord.Member):
        if self._channel_busy(ctx, "ttt"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)
        if opponent.bot or opponent == ctx.author:
            return await ctx.reply(view=_resp(f"{cross} Invalid opponent."), mention_author=False, delete_after=5)

        outer = self
        board = [["" for _ in range(3)] for _ in range(3)]
        marks = {ctx.author: "\u274c", opponent: "\u26aa"}
        players = [ctx.author, opponent]
        turn = 0

        WINNING_LINES = [
            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],
        ]

        def check_winner():
            for line in WINNING_LINES:
                vals = [board[r][c] for r, c in line]
                if vals[0] and vals.count(vals[0]) == 3:
                    return vals[0], line
            return None, None

        def check_draw():
            return all(board[r][c] for r in range(3) for c in range(3))

        class TTTView(ui.LayoutView):
            def __init__(self):
                super().__init__(timeout=120)
                self._render()

            def _render(self, win_line=None, game_over=False):
                self.clear_items()
                c = ui.Container()

                if game_over:
                    c.add_item(ui.TextDisplay(
                        f"{e_dot} {players[0].mention} {marks[players[0]]}  vs  {marks[players[1]]} {players[1].mention}"
                    ))
                else:
                    c.add_item(ui.TextDisplay(
                        f"### {marks[players[turn]]} {players[turn].mention}'s turn\n\n"
                        f"{e_dot} {players[0].display_name} {marks[players[0]]}  vs  {marks[players[1]]} {players[1].display_name}"
                    ))
                self.add_item(c)

                if not game_over:
                    for i in range(3):
                        row = ui.ActionRow()
                        for j in range(3):
                            label = "\u200b"
                            style = discord.ButtonStyle.secondary
                            disabled = False
                            if board[i][j]:
                                label = board[i][j]
                                style = discord.ButtonStyle.success if board[i][j] == "\u274c" else discord.ButtonStyle.primary
                                disabled = True
                            if win_line and (i, j) in win_line:
                                style = discord.ButtonStyle.success
                                disabled = True
                            btn = ui.Button(label=label, style=style, disabled=disabled)

                            async def cb(interaction: discord.Interaction, r=i, c=j):
                                nonlocal turn
                                if interaction.user != players[turn]:
                                    return await interaction.response.send_message(f"{cross} Not your turn!", ephemeral=True)
                                mark = marks[interaction.user]
                                board[r][c] = mark

                                wm, wl = check_winner()
                                if wm:
                                    winner = players[turn]
                                    self._render(win_line=wl, game_over=True)
                                    c2 = ui.Container()
                                    c2.add_item(ui.TextDisplay(
                                        f"## \U0001f3c6 {winner.mention} wins!\n\n"
                                        f"{e_dot} {players[0].mention} {marks[players[0]]}\n"
                                        f"{e_dot} {players[1].mention} {marks[players[1]]}"
                                    ))
                                    self.add_item(c2)
                                    outer._free(ctx, "ttt")
                                    return await interaction.response.edit_message(view=self)

                                if check_draw():
                                    self._render(game_over=True)
                                    c2 = ui.Container()
                                    c2.add_item(ui.TextDisplay("## \U0001f91d It's a draw!"))
                                    self.add_item(c2)
                                    outer._free(ctx, "ttt")
                                    return await interaction.response.edit_message(view=self)

                                turn = 1 - turn
                                self._render()
                                await interaction.response.edit_message(view=self)

                            btn.callback = cb
                            row.add_item(btn)
                        self.add_item(row)

                    stop_row = ui.ActionRow()
                    stop_btn = ui.Button(label="Stop Game", style=discord.ButtonStyle.danger, emoji="\u26d4")
                    async def stop_cb(interaction: discord.Interaction):
                        if interaction.user not in players:
                            return await interaction.response.send_message(f"{cross} Only players can stop.", ephemeral=True)
                        self._render(game_over=True)
                        c2 = ui.Container()
                        c2.add_item(ui.TextDisplay(f"## \U0001f6d1 Stopped by {interaction.user.mention}"))
                        self.add_item(c2)
                        outer._free(ctx, "ttt")
                        await interaction.response.edit_message(view=self)
                    stop_btn.callback = stop_cb
                    stop_row.add_item(stop_btn)
                    self.add_item(stop_row)

            async def on_timeout(self):
                self.clear_items()
                c = ui.Container()
                c.add_item(ui.TextDisplay(f"## \u23f0 Timed out! {players[turn].mention} took too long."))
                self.add_item(c)
                try:
                    await msg.edit(view=self)
                except Exception:
                    pass
                outer._free(ctx, "ttt")

        view = TTTView()
        self.games[self._key(ctx, "ttt")] = view
        msg = await ctx.reply(view=view, mention_author=False)

    @commands.hybrid_command(name="rockpaperscissors", aliases=["rps"],
                             description="Play Rock-Paper-Scissors with someone",
                             usage="rps <user>")
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(opponent="Who do you want to play against?")
    async def rockpaperscissors(self, ctx: commands.Context, opponent: discord.Member):
        if self._channel_busy(ctx, "rps"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)
        if opponent.bot or opponent == ctx.author:
            return await ctx.reply(view=_resp(f"{cross} Invalid opponent."), mention_author=False, delete_after=5)

        players = [ctx.author, opponent]
        outer = self
        BEATS = {"\U0001f5fb": "\u2702\ufe0f", "\U0001f4c4": "\U0001f5fb", "\u2702\ufe0f": "\U0001f4c4"}
        LABELS = {"\U0001f5fb": "\U0001f5fb Rock", "\U0001f4c4": "\U0001f4c4 Paper", "\u2702\ufe0f": "\u2702\ufe0f Scissors"}

        async def run_game(reply_target, edit_msg=None):
            choices: dict[discord.Member, str] = {}
            self.games[self._key(ctx, "rps")] = choices

            class RPSView(ui.LayoutView):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.message = None
                    self._render()

                def _render(self, result_text=None, winner=None):
                    self.clear_items()
                    c = ui.Container()
                    if result_text:
                        c.add_item(ui.TextDisplay(result_text))
                    else:
                        c.add_item(ui.TextDisplay(
                            f"### {players[0].mention} vs {players[1].mention}\n\n"
                            f"Pick your move below \u2014 your choice is hidden until both pick!"
                        ))
                    self.add_item(c)

                    if not result_text:
                        for emoji in ["\U0001f5fb", "\U0001f4c4", "\u2702\ufe0f"]:
                            row = ui.ActionRow()
                            btn = ui.Button(label=LABELS[emoji], style=discord.ButtonStyle.primary)
                            async def cb(interaction: discord.Interaction, e=emoji):
                                if interaction.user not in players:
                                    return await interaction.response.send_message(f"{cross} You're not in this game.", ephemeral=True)
                                if interaction.user in choices:
                                    return await interaction.response.send_message(f"{tick} You already picked!", ephemeral=True)
                                choices[interaction.user] = e
                                remaining = [p for p in players if p not in choices]
                                await interaction.response.send_message(
                                    f"{tick} Locked in: **{LABELS[e]}**"
                                    + (f"\n\u231b Waiting for {remaining[0].mention}\u2026" if remaining else ""),
                                    ephemeral=True,
                                )
                                if len(choices) == 2:
                                    p1, p2 = players
                                    c1, c2 = choices[p1], choices[p2]
                                    if c1 == c2:
                                        result = "## \U0001f91d It's a draw!"
                                        w = None
                                    elif BEATS[c1] == c2:
                                        result = f"## \U0001f3c6 {p1.mention} wins!"
                                        w = p1
                                    else:
                                        result = f"## \U0001f3c6 {p2.mention} wins!"
                                        w = p2

                                    body = (
                                        f"{result}\n\n"
                                        f"{e_dot} {LABELS[c1]} \u2192 {p1.mention}\n"
                                        f"{e_dot} {LABELS[c2]} \u2192 {p2.mention}"
                                    )
                                    self._render(result_text=body, winner=w)

                                    rematch_row = ui.ActionRow()
                                    rematch_btn = ui.Button(label="Rematch", style=discord.ButtonStyle.success, emoji="\U0001f504")
                                    async def rematch_cb(interaction: discord.Interaction):
                                        if interaction.user not in players:
                                            return await interaction.response.send_message(f"{cross} Only players can rematch.", ephemeral=True)
                                        await interaction.response.defer()
                                        for it in self.children:
                                            if isinstance(it, ui.Container):
                                                it.clear_items()
                                            elif isinstance(it, ui.ActionRow):
                                                for b in it.children:
                                                    b.disabled = True
                                        await self.message.edit(view=self)
                                        await run_game(reply_target=None, edit_msg=self.message)
                                    rematch_btn.callback = rematch_cb
                                    rematch_row.add_item(rematch_btn)
                                    self.add_item(rematch_row)
                                    outer._free(ctx, "rps")
                                    await self.message.edit(view=self)
                            btn.callback = cb
                            row.add_item(btn)
                            self.add_item(row)

                    stop_row = ui.ActionRow()
                    stop_btn = ui.Button(label="Stop", style=discord.ButtonStyle.danger, emoji="\u26d4")
                    async def stop_cb(interaction: discord.Interaction):
                        if interaction.user not in players:
                            return await interaction.response.send_message(f"{cross} Only players can stop.", ephemeral=True)
                        self.clear_items()
                        c2 = ui.Container()
                        c2.add_item(ui.TextDisplay(f"## \U0001f6d1 Stopped by {interaction.user.mention}"))
                        self.add_item(c2)
                        outer._free(ctx, "rps")
                        await interaction.response.edit_message(view=self)
                    stop_btn.callback = stop_cb
                    stop_row.add_item(stop_btn)
                    if not result_text:
                        self.add_item(stop_row)

                async def on_timeout(self):
                    self.clear_items()
                    missing = [p.display_name for p in players if p not in choices]
                    c = ui.Container()
                    c.add_item(ui.TextDisplay(
                        f"\u23f0 Timed out \u2014 **{', '.join(missing)}** didn't pick in time."
                    ))
                    self.add_item(c)
                    try:
                        await self.message.edit(view=self)
                    except Exception:
                        pass
                    outer._free(ctx, "rps")

            view = RPSView()
            if edit_msg:
                m = await edit_msg.reply(view=view, mention_author=False)
            elif reply_target:
                m = await reply_target.reply(view=view, mention_author=False)
            else:
                m = await ctx.channel.send(view=view)
            view.message = m

        await run_game(reply_target=ctx.message)

    @commands.hybrid_command(name="reaction", description="Quick emoji reaction game \u2014 fastest fingers win!",
                             usage="reaction [rounds]")
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(rounds="Number of rounds to play (1\u20135, default 1)")
    async def reaction(self, ctx: commands.Context, rounds: int = 1):
        if self._channel_busy(ctx, "reaction"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)

        rounds = max(1, min(rounds, 5))
        self.games[self._key(ctx, "reaction")] = True

        scores: dict[int, dict] = {}

        msg = await ctx.reply(view=_resp(
            f"### \u26a1 Quick Reaction \u2014 {rounds} round{'s' if rounds > 1 else ''}\n\n"
            f"React to the correct emoji as fast as possible!"
        ), mention_author=False)

        for rnd in range(1, rounds + 1):
            target = random.choice(REACTION_EMOJIS)
            shown = random.sample(REACTION_EMOJIS, k=min(4, len(REACTION_EMOJIS)))
            if target not in shown:
                shown[0] = target
            random.shuffle(shown)

            await msg.edit(view=_resp(
                f"**Round {rnd}/{rounds}**\n\nAdding reactions\u2026 get ready!"
            ))

            for e in shown:
                try:
                    await msg.add_reaction(e)
                except Exception:
                    pass

            for t in [3, 2, 1]:
                await asyncio.sleep(1)
                await msg.edit(view=_resp(
                    f"**Round {rnd}/{rounds}** \u2014 React in `{t}`\u2026"
                ))

            await msg.edit(view=_resp(
                f"**Round {rnd}/{rounds}** \u2014 {target}"
            ))
            start = time.time()
            deadline = start + 6
            round_responses = {}

            def make_check():
                seen = set()
                def _check(reaction, user):
                    if (reaction.message.id == msg.id
                        and str(reaction.emoji) == target
                        and not user.bot
                        and user.id not in seen):
                        seen.add(user.id)
                        return True
                    return False
                return _check

            chk = make_check()
            while time.time() < deadline:
                rem = deadline - time.time()
                if rem <= 0:
                    break
                try:
                    rxn, user = await ctx.bot.wait_for("reaction_add", timeout=min(0.3, rem), check=chk)
                    round_responses[user.id] = {"user": user, "time": time.time() - start}
                except asyncio.TimeoutError:
                    continue

            if round_responses:
                lines = []
                sorted_users = sorted(round_responses.items(), key=lambda x: x[1]["time"])
                for rank, (uid, info) in enumerate(sorted_users, 1):
                    pts = max(1, 4 - rank)
                    scores[uid] = scores.get(uid, {"user": info["user"], "total_pts": 0, "total_time": 0, "rounds": 0})
                    scores[uid]["total_pts"] += pts
                    scores[uid]["total_time"] += info["time"]
                    scores[uid]["rounds"] += 1
                    badge = "\U0001f947" if rank == 1 else "\U0001f948" if rank == 2 else "\U0001f949" if rank == 3 else "\u25ab\ufe0f"
                    lines.append(f"{badge} {info['user'].mention} \u2014 **{info['time']:.2f}s** (+{pts}pt)")
                body = f"**Round {rnd}/{rounds}** \u2014 {target}\n\n" + "\n".join(lines)
            else:
                body = f"**Round {rnd}/{rounds}** \u2014 {target}\n\n\u23f0 Nobody reacted in time!"

            await msg.edit(view=_resp(body))

            try:
                await msg.clear_reactions()
            except Exception:
                pass

            if rnd < rounds:
                await asyncio.sleep(2)

        self._free(ctx, "reaction")

        if scores:
            sorted_scores = sorted(scores.values(), key=lambda x: (-x["total_pts"], x["total_time"]))
            board_lines = []
            for rank, s in enumerate(sorted_scores, 1):
                badge = "\U0001f947" if rank == 1 else "\U0001f948" if rank == 2 else "\U0001f949" if rank == 3 else "\u25ab\ufe0f"
                avg = s["total_time"] / s["rounds"]
                board_lines.append(f"{badge} {s['user'].mention} \u2014 **{s['total_pts']}pts** (avg {avg:.2f}s)")
            await msg.edit(view=_resp(
                f"## \U0001f3c1 Game Over!\n\n**Leaderboard:**\n" + "\n".join(board_lines)
            ))
        else:
            await msg.edit(view=_resp("## \U0001f3c1 Game Over!\nNobody scored a single point. \U0001f480"))

    @commands.hybrid_command(name="hangman", description="Play Hangman in the channel",
                             usage="hangman")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def hangman(self, ctx: commands.Context):
        if self._channel_busy(ctx, "hangman"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)

        word = await self._fetch_word()
        outer = self
        self.games[self._key(ctx, "hangman")] = True
        max_wrong = len(HANGMAN_STAGES) - 1

        class HangmanView(ui.LayoutView):
            def __init__(self):
                super().__init__(timeout=180)
                self.guessed = set()
                self.wrong = []
                self.hint_used = False
                self.hint_def = None
                self._render()

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user != ctx.author:
                    await interaction.response.send_message(f"{cross} This is {ctx.author.mention}'s hangman game!", ephemeral=True)
                    return False
                return True

            def _render(self):
                self.clear_items()
                stage = len(self.wrong)
                won = all(c in self.guessed for c in word)
                lost = stage >= max_wrong
                progress = " ".join(c if c in self.guessed else "\\_" for c in word)
                wrong_str = " ".join(f"`{c}`" for c in self.wrong) or "None yet"
                c = ui.Container()

                if won:
                    c.add_item(ui.TextDisplay(
                        f"## \U0001f389 You got it!\n\n"
                        f"The word was **`{word}`**\n\n"
                        f"Wrong guesses: {wrong_str}"
                    ))
                elif lost:
                    c.add_item(ui.TextDisplay(
                        f"## \U0001f480 Game over!\n\n"
                        f"The word was **`{word}`**\n\n"
                        f"{HANGMAN_STAGES[stage]}"
                    ))
                else:
                    c.add_item(ui.TextDisplay(
                        f"{HANGMAN_STAGES[stage]}\n"
                        f"**Word:** {progress}\n\n"
                        f"{e_dot} Wrong ({stage}/{max_wrong}): {wrong_str}"
                    ))
                self.add_item(c)

                if not won and not lost:
                    alphabet = "abcdefghijklmnopqrstuvwxyz"
                    for row_i in range(5):
                        row = ui.ActionRow()
                        for col in range(5):
                            idx = row_i * 5 + col
                            if idx >= 26:
                                break
                            letter = alphabet[idx]
                            disabled = letter in self.guessed or letter in self.wrong
                            style = (discord.ButtonStyle.success if letter in self.guessed else
                                     discord.ButtonStyle.danger if letter in self.wrong else
                                     discord.ButtonStyle.secondary)
                            btn = ui.Button(label=letter.upper(), style=style, disabled=disabled)

                            async def cb(interaction: discord.Interaction, l=letter):
                                if l in self.guessed or l in self.wrong:
                                    return await interaction.response.send_message("Already guessed!", ephemeral=True)
                                if l in word:
                                    self.guessed.add(l)
                                else:
                                    self.wrong.append(l)
                                if all(c in self.guessed for c in word) or len(self.wrong) >= max_wrong:
                                    outer._free(ctx, "hangman")
                                self._render()
                                await interaction.response.edit_message(view=self)

                            btn.callback = cb
                            row.add_item(btn)
                        if row.children:
                            self.add_item(row)

                    hint_row = ui.ActionRow()
                    hint_btn = ui.Button(label="Hint", style=discord.ButtonStyle.secondary, emoji="\U0001f4a1", disabled=self.hint_used)
                    async def hint_cb(interaction: discord.Interaction):
                        if self.hint_used:
                            return await interaction.response.send_message("Hint already used!", ephemeral=True)
                        self.hint_used = True
                        unguessed = [c for c in word if c not in self.guessed]
                        if unguessed:
                            target = unguessed[0]
                            self.guessed.add(target)
                        if self.hint_def is None:
                            self.hint_def = await outer._fetch_definition(word)
                        msg_text = f"\U0001f4a1 Revealed letter: **{target.upper()}**"
                        if self.hint_def:
                            msg_text += f"\n*{self.hint_def}*"
                        if all(c in self.guessed for c in word):
                            outer._free(ctx, "hangman")
                        self._render()
                        await interaction.response.edit_message(view=self)
                        await ctx.channel.send(msg_text, delete_after=10)
                    hint_btn.callback = hint_cb
                    hint_row.add_item(hint_btn)
                    self.add_item(hint_row)

            async def on_timeout(self):
                self.clear_items()
                c = ui.Container()
                c.add_item(ui.TextDisplay(f"\u23f0 Game timed out! The word was **`{word}`**."))
                self.add_item(c)
                outer._free(ctx, "hangman")
                try:
                    await msg.edit(view=self)
                except Exception:
                    pass

        view = HangmanView()
        msg = await ctx.reply(view=view, mention_author=False)

    @commands.hybrid_command(name="higherorlower", aliases=["hol", "guess"],
                             description="Guess the secret number \u2014 higher or lower?",
                             usage="higherorlower [max]")
    @commands.cooldown(1, 8, commands.BucketType.user)
    @app_commands.describe(maximum="Upper bound for the number (default 100)")
    async def higherorlower(self, ctx: commands.Context, maximum: int = 100):
        if self._channel_busy(ctx, "hol"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)

        maximum = max(10, min(maximum, 1000))
        secret = random.randint(1, maximum)
        attempts = 0
        outer = self
        self.games[self._key(ctx, "hol")] = True

        await ctx.reply(view=_layout(
            "Higher or Lower",
            f"I'm thinking of a number between **1** and **{maximum}**.\n\n"
            f"Type your guess in chat \u2014 you have **60 seconds** per guess.\n"
            f"Type `stop` to quit."
        ), mention_author=False)

        def check(m: discord.Message):
            return m.channel == ctx.channel and m.author == ctx.author

        while True:
            try:
                msg = await ctx.bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send(view=_layout(
                    "Time's Up!",
                    f"\u23f0 You took too long! The number was **`{secret}`**."
                ))
                break

            if msg.content.lower() == "stop":
                await ctx.channel.send(view=_layout(
                    "Stopped",
                    f"\U0001f6d1 Game stopped. The number was **`{secret}`**."
                ))
                break

            try:
                guess = int(msg.content.strip())
            except ValueError:
                await ctx.channel.send(f"{cross} That's not a valid number \u2014 try again.", delete_after=4)
                continue

            attempts += 1

            if guess == secret:
                await ctx.channel.send(view=_layout(
                    "You Got It!",
                    f"\U0001f389 {ctx.author.mention} got it!\n\n"
                    f"The number was **`{secret}`** \u2014 found in **{attempts}** guess{'es' if attempts > 1 else ''}!"
                ))
                break
            elif guess < secret:
                hint = "\U0001f4c8 **Higher!**"
            else:
                hint = "\U0001f4c9 **Lower!**"

            await ctx.channel.send(view=_layout(
                "Higher or Lower",
                f"{hint}\nYour guess: `{guess}` | Attempts: `{attempts}`"
            ), delete_after=10)

        self._free(ctx, "hol")

    @commands.hybrid_command(name="wordscramble", aliases=["scramble"],
                             description="Unscramble the word before time runs out",
                             usage="wordscramble")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def wordscramble(self, ctx: commands.Context):
        if self._channel_busy(ctx, "scramble"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)

        word = await self._fetch_word()
        letters = list(word)
        for _ in range(20):
            random.shuffle(letters)
            if "".join(letters) != word:
                break
        scrambled = "".join(letters)

        self.games[self._key(ctx, "scramble")] = True

        hint_cost = 0
        definition = None
        hint_revealed = set()
        max_hints = 2
        base_points = 3

        def build_layout(msg_text=None):
            remaining = max_hints - len(hint_revealed)
            parts = [f"### \U0001f500 Unscramble this word!\n\n**`{scrambled.upper()}`**\n\n"]
            if msg_text:
                parts.append(msg_text + "\n\n")
            parts.append(f"Length: `{len(word)}` | Hints left: `{remaining}` | Points: **{base_points - hint_cost}**")
            if hint_revealed:
                parts.append("")
                if "first" in hint_revealed:
                    parts.append(f"First letter: **{word[0].upper()}**")
                if "definition" in hint_revealed and definition:
                    parts.append(f"Definition hint: *{definition}*")
            parts.append(f"\n\nType the answer in chat \u2014 or type `hint` for a hint ({base_points - hint_cost - 1}pt).")
            return _layout("Word Scramble", "\n".join(parts))

        msg = await ctx.reply(view=build_layout(), mention_author=False)

        def check(m: discord.Message):
            return m.channel == ctx.channel and not m.author.bot

        deadline = asyncio.get_event_loop().time() + 25

        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            try:
                resp = await ctx.bot.wait_for("message", timeout=remaining, check=check)
            except asyncio.TimeoutError:
                break

            content = resp.content.strip().lower()

            if content == "hint":
                if len(hint_revealed) >= max_hints:
                    await ctx.channel.send(f"{caution} No hints left!", delete_after=5)
                    continue
                if "first" not in hint_revealed:
                    hint_revealed.add("first")
                    hint_cost += 1
                    await ctx.channel.send(
                        f"\U0001f4a1 Hint: The word starts with **`{word[0].upper()}`** (\u22121 pt)",
                        delete_after=8
                    )
                elif "definition" not in hint_revealed:
                    if not definition:
                        definition = await self._fetch_definition(word)
                    hint_revealed.add("definition")
                    hint_cost += 1
                    if definition:
                        await ctx.channel.send(
                            f"\U0001f4a1 Definition: *{definition}* (\u22121 pt)",
                            delete_after=12
                        )
                    else:
                        await ctx.channel.send(
                            f"\U0001f4a1 The word has **{len(word)}** letters and starts with **{word[0].upper()}** (\u22121 pt)",
                            delete_after=8
                        )
                await msg.edit(view=build_layout())
                continue

            if content == word:
                pts = max(0, base_points - hint_cost)
                winner = resp.author
                self._free(ctx, "scramble")
                body = (
                    f"\U0001f389 {winner.mention} got it!\n\n"
                    f"**`{scrambled.upper()}`** \u2192 **`{word.upper()}`**\n\n"
                    f"**+{pts}pt** {'(no hints)' if pts == base_points else f'(hints used: {hint_cost})'}"
                )
                await msg.edit(view=_layout("Word Scramble", body))
                return

        self._free(ctx, "scramble")
        await msg.edit(view=_layout(
            "Time's Up!",
            f"\u23f0 Nobody got it in time!\n\n"
            f"**`{scrambled.upper()}`** \u2192 **`{word.upper()}`**"
        ))

    @commands.hybrid_command(name="trivia", description="Answer a trivia question \u2014 first correct wins!",
                             usage="trivia [difficulty]")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(difficulty="Question difficulty: easy, medium, or hard")
    async def trivia(self, ctx: commands.Context, difficulty: str = None):
        if self._channel_busy(ctx, "trivia"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)

        if difficulty and difficulty.lower() not in ("easy", "medium", "hard"):
            difficulty = None
        self.games[self._key(ctx, "trivia")] = True
        api_q = await self._fetch_trivia(difficulty)
        timeout = 20

        if api_q:
            question = html.unescape(api_q["question"])
            correct = html.unescape(api_q["correct_answer"])
            incorrect = [html.unescape(i) for i in api_q["incorrect_answers"]]
            qtype = api_q["type"]
            answers = [correct] + incorrect
            random.shuffle(answers)
            outer = self
            answered = [False]

            class TriviaView(ui.LayoutView):
                def __init__(self):
                    super().__init__(timeout=timeout + 5)
                    self._render()

                def _render(self, finished=False, winner_data=None):
                    self.clear_items()
                    c = ui.Container()
                    if finished and winner_data:
                        c.add_item(ui.TextDisplay(winner_data))
                    elif finished:
                        c.add_item(ui.TextDisplay(
                            f"\u23f0 Time's up!\n\n**{question}**\nThe answer was **`{correct}`**"
                        ))
                    else:
                        c.add_item(ui.TextDisplay(
                            f"### \U0001f3af Trivia\n\n**{question}**\n\nPick an answer below \u2014 \u23f0 {timeout}s!"
                        ))
                    self.add_item(c)

                    if not finished:
                        for i, ans in enumerate(answers):
                            row = ui.ActionRow()
                            labels = ["A", "B", "C", "D"]
                            btn = ui.Button(label=f"{labels[i]}. {ans}", style=discord.ButtonStyle.primary)
                            async def cb(interaction: discord.Interaction, a=ans):
                                if answered[0]:
                                    return await interaction.response.send_message(f"{cross} Already answered!", ephemeral=True)
                                answered[0] = True
                                if a.lower() == correct.lower():
                                    self._render(finished=True, winner_data=
                                        f"\U0001f3c6 {interaction.user.mention} got it!\n\n"
                                        f"**{question}**\n{tick} Answer: **`{correct}`**"
                                    )
                                    outer._free(ctx, "trivia")
                                else:
                                    self._render(finished=True, winner_data=
                                        f"\u274c {interaction.user.mention} answered **{a}** \u2014 wrong!\n\n"
                                        f"**{question}**\n{tick} Answer: **`{correct}`**"
                                    )
                                    outer._free(ctx, "trivia")
                                await interaction.response.edit_message(view=self)
                            btn.callback = cb
                            row.add_item(btn)
                            self.add_item(row)

                async def on_timeout(self):
                    if not answered[0]:
                        self._render(finished=True)
                        answered[0] = True
                        outer._free(ctx, "trivia")
                        try:
                            await msg.edit(view=self)
                        except Exception:
                            pass

            view = TriviaView()
            msg = await ctx.reply(view=view, mention_author=False)

        else:
            question, answers, emoji = random.choice(FALLBACK_TRIVIA)
            await ctx.reply(view=_layout(
                "Trivia Time!",
                f"{emoji} **{question}**\n\nType your answer in chat \u2014 \u23f0 **{timeout}s**!"
            ), mention_author=False)

            def check(m: discord.Message):
                return m.channel == ctx.channel and not m.author.bot

            correct_answer = answers[0]
            try:
                while True:
                    resp = await ctx.bot.wait_for("message", timeout=timeout, check=check)
                    if resp.content.strip().lower() in [a.lower() for a in answers]:
                        await ctx.channel.send(view=_layout(
                            "Correct!",
                            f"\U0001f3c6 {resp.author.mention} got it!\n\n"
                            f"**{question}**\n{tick} Answer: **`{correct_answer.title()}`**"
                        ))
                        break
            except asyncio.TimeoutError:
                await ctx.channel.send(view=_layout(
                    "Time's Up!",
                    f"\u23f0 Nobody got it!\n\n"
                    f"**{question}**\n{tick} Answer: **`{correct_answer.title()}`**"
                ))

            self._free(ctx, "trivia")

    @commands.hybrid_command(name="connect4", aliases=["c4"],
                             description="Play Connect 4 with someone \u2014 get 4 in a row!",
                             usage="connect4 <user>")
    @commands.cooldown(1, 15, commands.BucketType.user)
    @app_commands.describe(opponent="Who do you want to play against?")
    async def connect4(self, ctx: commands.Context, opponent: discord.Member):
        if self._channel_busy(ctx, "c4"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)
        if opponent.bot or opponent == ctx.author:
            return await ctx.reply(view=_resp(f"{cross} Invalid opponent."), mention_author=False, delete_after=5)

        ROWS, COLS = 6, 7
        grid = [["" for _ in range(COLS)] for _ in range(ROWS)]
        players = [ctx.author, opponent]
        marks = ["\U0001f535", "\U0001f534"]
        turn = 0
        outer = self
        self.games[self._key(ctx, "c4")] = True

        def render_grid():
            lines = []
            for r in range(ROWS):
                line = "".join(grid[r][c] if grid[r][c] else "\u26ab" for c in range(COLS))
                lines.append(line)
            lines.append("".join(str(i + 1) for i in range(COLS)))
            return "```\n" + "\n".join(lines) + "```"

        def drop(col):
            for r in range(ROWS - 1, -1, -1):
                if not grid[r][col]:
                    grid[r][col] = marks[turn]
                    return r
            return -1

        def check_winner():
            dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
            for r in range(ROWS):
                for c in range(COLS):
                    if not grid[r][c]:
                        continue
                    for dr, dc in dirs:
                        cells = []
                        for step in range(4):
                            nr, nc = r + dr * step, c + dc * step
                            if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] == grid[r][c]:
                                cells.append((nr, nc))
                            else:
                                break
                        if len(cells) == 4:
                            return grid[r][c], cells
            return None, None

        def check_draw():
            return all(grid[0][c] for c in range(COLS))

        class C4View(ui.LayoutView):
            def __init__(self):
                super().__init__(timeout=120)
                self._render()

            def _render(self, finished=False, winner=None, win_cells=None):
                self.clear_items()
                c = ui.Container()

                if finished:
                    if winner:
                        c.add_item(ui.TextDisplay(
                            f"## \U0001f3c6 {winner.mention} wins!\n\n{render_grid()}"
                        ))
                    else:
                        c.add_item(ui.TextDisplay(
                            f"## \U0001f91d It's a draw!\n\n{render_grid()}"
                        ))
                else:
                    c.add_item(ui.TextDisplay(
                        f"### Connect 4\n\n{marks[turn]} {players[turn].mention}'s turn\n\n{render_grid()}"
                    ))
                self.add_item(c)

                if not finished:
                    button_rows = []
                    current = ui.ActionRow()
                    for col in range(COLS):
                        full = bool(grid[0][col])
                        btn = ui.Button(label=str(col + 1), style=discord.ButtonStyle.secondary, disabled=full)

                        async def cb(interaction: discord.Interaction, cl=col):
                            nonlocal turn
                            if interaction.user != players[turn]:
                                return await interaction.response.send_message(f"{cross} Not your turn!", ephemeral=True)
                            row = drop(cl)
                            if row == -1:
                                return await interaction.response.send_message(f"{cross} Column full!", ephemeral=True)

                            mark, wc = check_winner()
                            if mark:
                                self._render(finished=True, winner=players[turn], win_cells=wc)
                                outer._free(ctx, "c4")
                                return await interaction.response.edit_message(view=self)

                            if check_draw():
                                self._render(finished=True)
                                outer._free(ctx, "c4")
                                return await interaction.response.edit_message(view=self)

                            turn = 1 - turn
                            self._render()
                            await interaction.response.edit_message(view=self)

                        btn.callback = cb
                        if len(current.children) >= 4:
                            button_rows.append(current)
                            current = ui.ActionRow()
                        current.add_item(btn)
                    if current.children:
                        button_rows.append(current)
                    for r in button_rows:
                        self.add_item(r)

                    stop_row = ui.ActionRow()
                    stop_btn = ui.Button(label="Stop", style=discord.ButtonStyle.danger, emoji="\u26d4")
                    async def stop_cb(interaction: discord.Interaction):
                        if interaction.user not in players:
                            return await interaction.response.send_message(f"{cross} Only players can stop.", ephemeral=True)
                        self._render(finished=True, winner=players[1 - turn])
                        outer._free(ctx, "c4")
                        await interaction.response.edit_message(view=self)
                    stop_btn.callback = stop_cb
                    stop_row.add_item(stop_btn)
                    self.add_item(stop_row)

            async def on_timeout(self):
                self.clear_items()
                c = ui.Container()
                c.add_item(ui.TextDisplay(f"\u23f0 Game timed out! {players[turn].mention} took too long."))
                self.add_item(c)
                outer._free(ctx, "c4")
                try:
                    await msg.edit(view=self)
                except Exception:
                    pass

        view = C4View()
        msg = await ctx.reply(view=view, mention_author=False)

    @commands.hybrid_command(name="quickmath", aliases=["math"],
                             description="Solve math problems as fast as you can!",
                             usage="quickmath")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def quickmath(self, ctx: commands.Context):
        if self._channel_busy(ctx, "math"):
            return await ctx.reply(view=_resp(f"{cross} A game is already running here!"), mention_author=False, delete_after=5)

        self.games[self._key(ctx, "math")] = True
        outer = self
        max_rounds = 10

        class MathGameView(ui.LayoutView):
            def __init__(self):
                super().__init__(timeout=15)
                self.round = 0
                self.done = False
                self.round_answers: set[int] = set()
                self.participants: dict[int, dict] = {}
                self.a = self.b = self.op = self.ans = 0
                self.choices = []
                self._next_round()

            def _gen_problem(self):
                ops = ["+", "-", "\u00d7"]
                op = random.choice(ops)
                if op == "+":
                    a, b = random.randint(10, 99), random.randint(10, 99)
                    ans = a + b
                elif op == "-":
                    a = random.randint(20, 99)
                    b = random.randint(10, a - 1)
                    ans = a - b
                else:
                    a = random.randint(2, 12)
                    b = random.randint(2, 12)
                    ans = a * b
                choices = [ans]
                while len(choices) < 4:
                    offset = random.randint(-9, 9)
                    alt = ans + offset
                    if alt >= 0 and alt != ans and alt not in choices:
                        choices.append(alt)
                random.shuffle(choices)
                return a, b, op, ans, choices

            def _next_round(self):
                self.round += 1
                if self.round > max_rounds:
                    self.done = True
                    self._render_game_over()
                    return
                self.round_answers.clear()
                self.a, self.b, self.op, self.ans, self.choices = self._gen_problem()
                self._render()

            def _render(self, finished=False):
                self.clear_items()
                c = ui.Container()
                if finished:
                    c.add_item(ui.TextDisplay(
                        f"\u23f0 Time's up!\n\n**{self.a} {self.op} {self.b} = ?**\n"
                        f"{tick} Answer: **{self.ans}**"
                    ))
                else:
                    c.add_item(ui.TextDisplay(
                        f"### \U0001f522 Quick Math\n\n**{self.a} {self.op} {self.b} = ?**\n\n"
                        f"Participants: **{len(self.participants)}** | Round: **{self.round}/{max_rounds}**"
                    ))
                self.add_item(c)
                if not finished:
                    for val in self.choices:
                        row = ui.ActionRow()
                        btn = ui.Button(label=str(val), style=discord.ButtonStyle.primary)
                        async def cb(interaction: discord.Interaction, v=val):
                            if self.done:
                                return
                            uid = interaction.user.id
                            if uid in self.round_answers:
                                return await interaction.response.send_message(f"{cross} Already answered this round!", ephemeral=True)
                            self.round_answers.add(uid)
                            if uid not in self.participants:
                                self.participants[uid] = {"user": interaction.user, "correct": 0, "wrong": 0, "total": 0}
                            self.participants[uid]["total"] += 1
                            if v == self.ans:
                                self.participants[uid]["correct"] += 1
                                await interaction.response.send_message(f"{tick} **Correct!** \u2014 {self.a} {self.op} {self.b} = **{self.ans}**", ephemeral=True)
                            else:
                                self.participants[uid]["wrong"] += 1
                                await interaction.response.send_message(f"\u274c **Wrong!** \u2014 {self.a} {self.op} {self.b} = **{self.ans}**", ephemeral=True)
                        btn.callback = cb
                        row.add_item(btn)
                        self.add_item(row)
                    stop_row = ui.ActionRow()
                    stop_btn = ui.Button(label="End Game", style=discord.ButtonStyle.danger, emoji="\u26d4")
                    async def stop_cb(interaction: discord.Interaction):
                        self.done = True
                        self._render_game_over()
                        await interaction.response.edit_message(view=self)
                    stop_btn.callback = stop_cb
                    stop_row.add_item(stop_btn)
                    self.add_item(stop_row)

            def _render_game_over(self):
                self.clear_items()
                outer._free(ctx, "math")
                if not self.participants:
                    c = ui.Container()
                    c.add_item(ui.TextDisplay("## Game Over!\n\nNobody participated."))
                    self.add_item(c)
                    return
                sorted_parts = sorted(self.participants.values(), key=lambda x: (-x["correct"], x["wrong"]))
                lines = ["### \U0001f3c1 Quick Math Results\n"]
                for i, p in enumerate(sorted_parts, 1):
                    badge = "\U0001f947" if i == 1 else "\U0001f948" if i == 2 else "\U0001f949" if i == 3 else "\u25ab\ufe0f"
                    pct = int(p["correct"] / max(p["total"], 1) * 100)
                    lines.append(f"{badge} {p['user'].mention} \u2014 **{p['correct']}**/**{p['total']}** correct ({pct}%)")
                c = ui.Container()
                c.add_item(ui.TextDisplay("\n".join(lines)))
                self.add_item(c)

            async def on_timeout(self):
                if not self.done:
                    self._render(finished=True)
                    try:
                        await msg.edit(view=self)
                    except Exception:
                        pass
                    await asyncio.sleep(2)
                    self._next_round()
                    if not self.done:
                        try:
                            await msg.edit(view=self)
                        except Exception:
                            pass

        view = MathGameView()
        msg = await ctx.reply(view=view, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
