#  █████╗ ██╗    ███╗   ███╗ █████╗ ██████╗ ███████╗
# ██╔══██╗██║    ████╗ ████║██╔══██╗██╔══██╗██╔════╝
# ███████║██║    ██╔████╔██║███████║██║  ██║█████╗
# ██╔══██║██║    ██║╚██╔╝██║██╔══██║██║  ██║██╔══╝
# ██║  ██║██║    ██║ ╚═╝ ██║██║  ██║██████╔╝███████╗
# ╚═╝  ╚═╝╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝
# This code is written by ai - unresolved bugs

import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from utils.variables import *
from utils.checks import *
import json
import os
import random
from datetime import datetime, timezone

GIVEAWAYS_FILE = "giveaways.json"
MAX_GIVEAWAYS = 5


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def load_giveaways() -> dict:
    if os.path.exists(GIVEAWAYS_FILE):
        try:
            with open(GIVEAWAYS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_giveaways(data: dict):
    with open(GIVEAWAYS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def parse_duration(duration: str) -> int | None:
    import re
    pattern = re.fullmatch(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", duration.strip())
    if not pattern or not any(pattern.groups()):
        return None
    days    = int(pattern.group(1) or 0)
    hours   = int(pattern.group(2) or 0)
    minutes = int(pattern.group(3) or 0)
    seconds = int(pattern.group(4) or 0)
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else None


def giveaway_embed(prize: str, winners: int, host: discord.Member | discord.User, ends_at: int, ended: bool = False) -> discord.Embed:
    if ended:
        embed = discord.Embed(
            title=f"🎉 {prize}",
            description=(
                f"{e_dot} This giveaway has ended.\n"
                f"{e_dot} Winners announced below."
            ),
            color=colour,
        )
    else:
        embed = discord.Embed(
            title=f"🎉 {prize}",
            description=(
                f"{e_dot} React with 🎉 to enter!\n"
                f"{e_dot} Ends: <t:{ends_at}:R> (<t:{ends_at}:F>)\n"
                f"{e_dot} Winners: **{winners}**\n"
                f"{e_dot} Hosted by: {host.mention}"
            ),
            color=colour,
        )
    embed.set_footer(text=f"{'Ended' if ended else 'Ends'} at")
    embed.timestamp = datetime.fromtimestamp(ends_at, tz=timezone.utc)
    return embed


# ──────────────────────────────────────────────
#  COG
# ──────────────────────────────────────────────

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._tasks: dict[str, asyncio.Task] = {}
        self._ready = False  # guard so on_ready only schedules once

    async def cog_load(self):
        # Don't schedule here — bot isn't ready yet, channels can't be resolved.
        # Scheduling happens in on_ready instead.
        pass

    async def cog_unload(self):
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()

    @commands.Cog.listener()
    async def on_ready(self):
        if self._ready:
            return
        self._ready = True

        await self.bot.wait_until_ready()

        data = load_giveaways()
        changed = False
        scheduled = 0

        for msg_id, gw in list(data.items()):
            if gw.get("ended"):
                continue

            # If ends_at already passed and it somehow wasn't marked ended,
            # it means the bot ended it but a crash prevented saving — mark it now
            # and DO NOT reschedule. This prevents ghost re-announcements.
            remaining = gw["ends_at"] - datetime.now(timezone.utc).timestamp()

            # Already have a live task for this — skip (mid-session cog reload)
            if msg_id in self._tasks and not self._tasks[msg_id].done():
                continue

            if remaining <= 0:
                # Check if the giveaway message already has the ended embed
                # by trying to detect if it was already processed.
                # We can't know for sure without fetching — so we check winner_ids:
                # if winner_ids is non-empty OR entries existed, it was processed.
                # Safest: just re-run _end_giveaway with delay=0 only if NOT already ended.
                # Since ended=False here, it genuinely needs ending.
                self._tasks[msg_id] = asyncio.ensure_future(
                    self._end_giveaway(msg_id, delay=0)
                )
                scheduled += 1
            else:
                self._tasks[msg_id] = asyncio.ensure_future(
                    self._end_giveaway(msg_id, delay=remaining)
                )
                scheduled += 1

        if changed:
            save_giveaways(data)

        if scheduled:
            print(f"[Giveaways] Scheduled {scheduled} giveaway(s) after ready.")
                
    # ── REACTION LISTENERS ─────────────────────

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "🎉":
            return
        if payload.user_id == self.bot.user.id:
            return

        msg_id = str(payload.message_id)
        data = load_giveaways()
        gw = data.get(msg_id)
        if not gw or gw.get("ended"):
            return

        if payload.user_id not in gw["entries"]:
            gw["entries"].append(payload.user_id)
            save_giveaways(data)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "🎉":
            return
        if payload.user_id == self.bot.user.id:
            return

        msg_id = str(payload.message_id)
        data = load_giveaways()
        gw = data.get(msg_id)
        if not gw or gw.get("ended"):
            return

        if payload.user_id in gw["entries"]:
            gw["entries"].remove(payload.user_id)
            save_giveaways(data)

    # ── END LOGIC ──────────────────────────────

    async def _end_giveaway(self, msg_id: str, delay: float):
        try:
            if delay > 0:
                await asyncio.sleep(delay)

            # Re-read fresh from disk in case entries updated during sleep
            data = load_giveaways()
            gw = data.get(msg_id)
            if not gw or gw.get("ended"):
                return

            channel = self.bot.get_channel(gw["channel_id"])
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(gw["channel_id"])
                except Exception:
                    data[msg_id]["ended"] = True
                    save_giveaways(data)
                    return

            try:
                message = await channel.fetch_message(int(msg_id))
            except Exception:
                data[msg_id]["ended"] = True
                save_giveaways(data)
                return

            entries = gw.get("entries", [])

            host = channel.guild.get_member(gw["host_id"]) or await self.bot.fetch_user(gw["host_id"])

            ended_embed = giveaway_embed(
                prize=gw["prize"],
                winners=gw["winners_count"],
                host=host,
                ends_at=gw["ends_at"],
                ended=True,
            )
            await message.edit(embed=ended_embed)

            winner_ids = random.sample(entries, min(gw["winners_count"], len(entries))) if entries else []

            if winner_ids:
                winner_members = []
                for uid in winner_ids:
                    member = channel.guild.get_member(uid)
                    if member is None:
                        try:
                            member = await channel.guild.fetch_member(uid)
                        except Exception:
                            member = await self.bot.fetch_user(uid)
                    winner_members.append(member)

                winner_mentions = ", ".join(w.mention for w in winner_members)
                result_embed = discord.Embed(color=colour)
                result_embed.set_author(
                    name="🎉 Giveaway Ended!",
                    icon_url=channel.guild.icon.url if channel.guild.icon else None,
                )
                result_embed.description = (
                    f"{e_dot} **Prize:** {gw['prize']}\n"
                    f"{e_dot} **Winner(s):** {winner_mentions}\n"
                    f"{e_dot} Congratulations! 🎊"
                )
                result_embed.set_footer(text=f"Giveaway ID: {msg_id}")
                await channel.send(
                    content=winner_mentions,
                    embed=result_embed,
                    reference=message,
                )
            else:
                no_win_embed = discord.Embed(
                    description=f"{cross} Not enough entries to pick a winner for **{gw['prize']}**.",
                    color=colour,
                )
                await channel.send(embed=no_win_embed, reference=message)

            data[msg_id]["ended"] = True
            data[msg_id]["winner_ids"] = winner_ids
            save_giveaways(data)

        except asyncio.CancelledError:
            pass  # Task was cancelled cleanly (cog unload / manual end)
        except Exception as e:
            print(f"[Giveaways] Error ending giveaway {msg_id}: {e}")
        finally:
            self._tasks.pop(msg_id, None)

    # ── GIVEAWAY GROUP ─────────────────────────

    @commands.hybrid_group(name="giveaway", aliases=["gw"], description="Giveaway commands.", usage="giveaway", category="Giveaways")
    @bled()
    async def giveaway(self, ctx: commands.Context):
        cmd = self.bot.get_command("help")
        if cmd:
            await ctx.invoke(cmd, query="giveaway")

    # ── START ──────────────────────────────────

    @giveaway.command(name="start", description="Starts a new giveaway in the current channel.", usage="giveaway start <duration> <winners> <prize>", category="Giveaways")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(
        duration="Duration of the giveaway (e.g. 1d2h30m10s)",
        winners="Number of winners",
        prize="The prize for the giveaway",
    )
    async def giveaway_start(self, ctx: commands.Context, duration: str, winners: int, *, prize: str):
        data = load_giveaways()

        active = [
            gw for gw in data.values()
            if not gw.get("ended") and gw["guild_id"] == ctx.guild.id
        ]
        if len(active) >= MAX_GIVEAWAYS:
            embed = discord.Embed(
                description=f"{cross} This server already has **{MAX_GIVEAWAYS}** active giveaways. End one before starting another.",
                color=colour,
            )
            return await ctx.reply(embed=embed, mention_author=False)

        if winners < 1:
            embed = discord.Embed(description=f"{cross} Number of winners must be at least **1**.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        total_seconds = parse_duration(duration)
        if total_seconds is None:
            embed = discord.Embed(
                description=f"{cross} Invalid duration. Use a format like `1d`, `2h30m`, `45s`, etc.",
                color=colour,
            )
            return await ctx.reply(embed=embed, mention_author=False)

        ends_at = int(datetime.now(timezone.utc).timestamp()) + total_seconds

        embed = giveaway_embed(
            prize=prize,
            winners=winners,
            host=ctx.author,
            ends_at=ends_at,
        )

        gw_msg = await ctx.channel.send(embed=embed)
        await gw_msg.add_reaction("🎉")

        msg_id = str(gw_msg.id)
        data[msg_id] = {
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "host_id": ctx.author.id,
            "prize": prize,
            "winners_count": winners,
            "ends_at": ends_at,
            "ended": False,
            "entries": [],
            "winner_ids": [],
        }
        save_giveaways(data)

        self._tasks[msg_id] = asyncio.ensure_future(
            self._end_giveaway(msg_id, delay=total_seconds)
        )

        confirm = discord.Embed(
            description=f"{tick} Giveaway started for **{prize}**! Ends <t:{ends_at}:R>.",
            color=colour,
        )
        await ctx.reply(embed=confirm, mention_author=False, delete_after=8)

    @giveaway_start.error
    async def giveaway_start_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You need **Manage Server** to start giveaways.", mention_author=False, ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⏳ Cooldown! Try again in `{error.retry_after:.1f}s`.", mention_author=False, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f"{cross} Usage: `giveaway start <duration> <winners> <prize>`", mention_author=False)

    # ── END ────────────────────────────────────

    @giveaway.command(name="end", description="Ends an active giveaway early.", usage="giveaway end <message_id>", category="Giveaways")
    @bled()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(message_id="The message ID of the giveaway to end.")
    async def giveaway_end(self, ctx: commands.Context, message_id: str):
        data = load_giveaways()
        gw = data.get(message_id)

        if not gw or gw["guild_id"] != ctx.guild.id:
            embed = discord.Embed(description=f"{cross} No active giveaway found with that message ID.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        if gw.get("ended"):
            embed = discord.Embed(description=f"{cross} That giveaway has already ended.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        task = self._tasks.pop(message_id, None)
        if task:
            task.cancel()

        self._tasks[message_id] = asyncio.ensure_future(
            self._end_giveaway(message_id, delay=0)
        )

        embed = discord.Embed(
            description=f"{tick} Giveaway `{message_id}` is being ended now.",
            color=colour,
        )
        await ctx.reply(embed=embed, mention_author=False, delete_after=8)

    @giveaway_end.error
    async def giveaway_end_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You need **Manage Server** to end giveaways.", mention_author=False, ephemeral=True)

    # ── REROLL ─────────────────────────────────

    @giveaway.command(name="reroll", description="Rerolls the winner for a finished giveaway.", usage="giveaway reroll <message_id>", category="Giveaways")
    @bled()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(message_id="The message ID of the finished giveaway to reroll.")
    async def giveaway_reroll(self, ctx: commands.Context, message_id: str):
        data = load_giveaways()
        gw = data.get(message_id)

        if not gw or gw["guild_id"] != ctx.guild.id:
            embed = discord.Embed(description=f"{cross} No giveaway found with that message ID.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        if not gw.get("ended"):
            embed = discord.Embed(description=f"{cross} That giveaway hasn't ended yet. Use `giveaway end` first.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        entries = gw.get("entries", [])
        if not entries:
            embed = discord.Embed(
                description=f"{cross} No entries found to reroll for **{gw['prize']}**.",
                color=colour,
            )
            return await ctx.reply(embed=embed, mention_author=False)

        winner_ids = random.sample(entries, min(gw["winners_count"], len(entries)))

        winner_members = []
        for uid in winner_ids:
            member = ctx.guild.get_member(uid)
            if member is None:
                try:
                    member = await ctx.guild.fetch_member(uid)
                except Exception:
                    member = await self.bot.fetch_user(uid)
            winner_members.append(member)

        winner_mentions = ", ".join(w.mention for w in winner_members)

        channel = self.bot.get_channel(gw["channel_id"])
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(gw["channel_id"])
            except Exception:
                channel = ctx.channel

        ref_message = None
        try:
            ref_message = await channel.fetch_message(int(message_id))
        except Exception:
            pass

        result_embed = discord.Embed(color=colour)
        result_embed.set_author(
            name="🎲 Giveaway Rerolled!",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
        )
        result_embed.description = (
            f"{e_dot} **Prize:** {gw['prize']}\n"
            f"{e_dot} **New Winner(s):** {winner_mentions}\n"
            f"{e_dot} Congratulations! 🎊"
        )
        result_embed.set_footer(
            text=f"Rerolled by {ctx.author}  •  Giveaway ID: {message_id}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.reply(embed=result_embed, mention_author=False)
        send_kwargs = {"content": winner_mentions, "embed": result_embed}
        if ref_message:
            send_kwargs["reference"] = ref_message
        await channel.send(**send_kwargs)

        data[message_id]["winner_ids"] = winner_ids
        save_giveaways(data)

    @giveaway_reroll.error
    async def giveaway_reroll_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You need **Manage Server** to reroll giveaways.", mention_author=False, ephemeral=True)

    # ── LIST ───────────────────────────────────

    @giveaway.command(name="list", description="Lists all active giveaways in the server.", usage="giveaway list", category="Giveaways")
    @bled()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def giveaway_list(self, ctx: commands.Context):
        data = load_giveaways()
        active = {
            mid: gw for mid, gw in data.items()
            if not gw.get("ended") and gw["guild_id"] == ctx.guild.id
        }

        if not active:
            embed = discord.Embed(
                description=f"{cross} There are no active giveaways in this server.",
                color=colour,
            )
            return await ctx.reply(embed=embed, mention_author=False)

        embed = discord.Embed(color=colour)
        embed.set_author(
            name=f"Active Giveaways — {ctx.guild.name}",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
        )

        items = list(active.items())
        for i, (mid, gw) in enumerate(items, 1):
            channel = self.bot.get_channel(gw["channel_id"])
            channel_mention = channel.mention if channel else f"`#{gw['channel_id']}`"
            entries = len(gw.get("entries", []))
            embed.add_field(
                name="",
                value=(
                    f"{e_dot} **{gw['prize']}**\n"
                    f"**Channel:** {channel_mention}\n"
                    f"**Winners:** {gw['winners_count']}  •  **Entries:** {entries}\n"
                    f"**Ends:** <t:{gw['ends_at']}:R>\n"
                    f"**ID:** `{mid}`"
                ),
                inline=False,
            )
            if i != len(items):
                embed.add_field(name="\u200b", value="\u200b", inline=False)

        embed.set_footer(
            text=f"Requested by {ctx.author}  •  {len(active)}/{MAX_GIVEAWAYS} slots used",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.reply(embed=embed, mention_author=False)

    # ── DELETE ─────────────────────────────────

    @giveaway.command(name="delete", description="Deletes a giveaway without picking a winner.", usage="giveaway delete <message_id>", category="Giveaways")
    @bled()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(message_id="The message ID of the giveaway to delete.")
    async def giveaway_delete(self, ctx: commands.Context, message_id: str):
        data = load_giveaways()
        gw = data.get(message_id)

        if not gw or gw["guild_id"] != ctx.guild.id:
            embed = discord.Embed(description=f"{cross} No giveaway found with that message ID.", color=colour)
            return await ctx.reply(embed=embed, mention_author=False)

        task = self._tasks.pop(message_id, None)
        if task:
            task.cancel()

        channel = self.bot.get_channel(gw["channel_id"])
        if channel:
            try:
                message = await channel.fetch_message(int(message_id))
                await message.delete()
            except Exception:
                pass

        prize = gw["prize"]
        del data[message_id]
        save_giveaways(data)

        embed = discord.Embed(
            description=f"{tick} Giveaway for **{prize}** has been deleted. No winner was picked.",
            color=colour,
        )
        await ctx.reply(embed=embed, mention_author=False, delete_after=8)

    @giveaway_delete.error
    async def giveaway_delete_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ You need **Manage Server** to delete giveaways.", mention_author=False, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Giveaways(bot))
