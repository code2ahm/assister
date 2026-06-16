import discord
from discord.ext import commands
from utils.loads import antid
from datetime import timedelta, timezone, datetime
import asyncio



def _is_enabled(guild_id: str, event: str) -> bool:
    return event in antid.get(guild_id, {}).get("enabled_events", [])


def _is_whitelisted(guild_id: str, user_id: int, event: str) -> bool:
    wl = antid.get(guild_id, {}).get("whitelist", {})
    return event in wl.get(str(user_id), [])


def _get_punishment(guild_id: str) -> str:
    return antid.get(guild_id, {}).get("punishment", "kick")


async def _get_audit_entry(
    guild: discord.Guild,
    action: discord.AuditLogAction,
    *,
    limit: int = 5,
    max_age_seconds: float = 8.0
) -> discord.AuditLogEntry | None:
    """Fetch the most recent audit log entry for a given action within max_age_seconds."""
    if not guild.me.guild_permissions.view_audit_log:
        return None
    now = datetime.now(timezone.utc)
    try:
        async for entry in guild.audit_logs(action=action, limit=limit):
            age = (now - entry.created_at).total_seconds()
            if age <= max_age_seconds:
                return entry
            break  # entries are chronological, no point checking older ones
    except discord.Forbidden:
        pass
    except Exception as e:
        print(f"[Antinuke] Audit log error ({action}): {e}")
    return None



class AntinukeEvents(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._channel_update_cooldown: set[tuple] = set()
        self._recently_punished: set[tuple] = set()  # (guild_id, user_id)



    async def punish(self, member: discord.Member, punishment: str, reason: str):
        """Apply punishment to a member, skipping if recently punished."""
        key = (str(member.guild.id), member.id)

        if key in self._recently_punished:
            print(f"[Antinuke] Already punished {member} ({member.id}) recently — skipping duplicate")
            return

        if member.guild.owner_id == member.id:
            print(f"[Antinuke] Skipping punishment (server owner): {member} ({member.id})")
            return

        self._recently_punished.add(key)
        asyncio.get_event_loop().call_later(10, self._recently_punished.discard, key)

        try:
            if punishment == "kick":
                await member.kick(reason=reason)
            elif punishment == "ban":
                await member.ban(reason=reason, delete_message_days=0)
            elif punishment == "mute":
                await member.timeout(timedelta(hours=24), reason=reason)
            else:
                print(f"[Antinuke] Unknown punishment '{punishment}' — skipping")
        except discord.Forbidden:
            print(f"[Antinuke] Missing permissions to punish {member} ({member.id})")
        except discord.NotFound:
            print(f"[Antinuke] Member not found: {member} ({member.id})")
        except Exception as e:
            print(f"[Antinuke] punish error: {e}")



    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        guild_id = str(message.guild.id)
        author   = message.author

        if author.id == message.guild.owner_id:
            return
        if not _is_enabled(guild_id, 'anti_ping'):
            return

        # Only trigger on @everyone or @here — not regular role mentions
        if not message.mention_everyone:
            return

        if _is_whitelisted(guild_id, author.id, 'anti_ping'):
            return

        print(f"[Antinuke] anti_ping triggered by {author} ({author.id}) in {guild_id}")

        try:
            await message.delete()
        except discord.Forbidden:
            print(f"[Antinuke] anti_ping: missing permission to delete message")
        except Exception as e:
            print(f"[Antinuke] anti_ping: error deleting message: {e}")

        member = message.guild.get_member(author.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Mass ping (@everyone/@here) | User not whitelisted")



    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            return

        guild_id = str(member.guild.id)

        if not _is_enabled(guild_id, 'anti_bot'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(member.guild, discord.AuditLogAction.bot_add, limit=5)
        if entry is None:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == member.guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_bot'):
            return

        print(f"[Antinuke] anti_bot triggered: bot={member} added by {pakad} ({pakad.id}) in {guild_id}")

        try:
            await member.kick(reason="Anti-nuke: Bot added by unwhitelisted user")
        except discord.Forbidden:
            print(f"[Antinuke] anti_bot: missing permission to kick bot {member}")
        except Exception as e:
            print(f"[Antinuke] anti_bot: error kicking bot: {e}")

        guild_member = member.guild.get_member(pakad.id)
        if guild_member:
            await self.punish(guild_member, _get_punishment(guild_id),
                              "Anti-nuke: Added a bot | User not whitelisted")



    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        guild_id = str(channel.guild.id)

        if not _is_enabled(guild_id, 'anti_channel_create'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(channel.guild, discord.AuditLogAction.channel_create)
        if entry is None:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == channel.guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_channel_create'):
            return

        print(f"[Antinuke] anti_channel_create triggered by {pakad} ({pakad.id}) — channel: {channel.name}")

        try:
            await channel.delete(reason="Anti-nuke: Channel created by unwhitelisted user")
        except discord.Forbidden:
            print(f"[Antinuke] anti_channel_create: missing permission to delete channel")
        except Exception as e:
            print(f"[Antinuke] anti_channel_create: error deleting channel: {e}")

        member = channel.guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Created a channel | User not whitelisted")



    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild_id = str(channel.guild.id)

        if not _is_enabled(guild_id, 'anti_channel_delete'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(channel.guild, discord.AuditLogAction.channel_delete)
        if entry is None:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == channel.guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_channel_delete'):
            return

        print(f"[Antinuke] anti_channel_delete triggered by {pakad} ({pakad.id}) — channel: {channel.name}")

        try:
            restored = await channel.clone(reason="Anti-nuke: Restoring deleted channel")
            try:
                await restored.edit(position=channel.position)
            except Exception:
                pass
            print(f"[Antinuke] anti_channel_delete: restored '{channel.name}'")
        except discord.Forbidden:
            print(f"[Antinuke] anti_channel_delete: missing permission to clone channel")
        except Exception as e:
            print(f"[Antinuke] anti_channel_delete: error restoring channel: {e}")

        member = channel.guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Deleted a channel | User not whitelisted")



    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        guild_id = str(before.guild.id)

        if not _is_enabled(guild_id, 'anti_channel_update'):
            return

        cooldown_key = (guild_id, str(before.id))
        if cooldown_key in self._channel_update_cooldown:
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(before.guild, discord.AuditLogAction.channel_update)
        if entry is None:
            return

        # Make sure this entry is for the channel that actually changed
        if entry.target and entry.target.id != before.id:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == before.guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_channel_update'):
            return

        print(f"[Antinuke] anti_channel_update triggered by {pakad} ({pakad.id}) — channel: {before.name}")

        self._channel_update_cooldown.add(cooldown_key)
        try:
            edit_kwargs = {}

            if before.name != after.name:
                edit_kwargs["name"] = before.name

            if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
                if before.topic != after.topic:
                    edit_kwargs["topic"] = before.topic
                if before.slowmode_delay != after.slowmode_delay:
                    edit_kwargs["slowmode_delay"] = before.slowmode_delay
                if before.nsfw != after.nsfw:
                    edit_kwargs["nsfw"] = before.nsfw

            if isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
                if before.bitrate != after.bitrate:
                    edit_kwargs["bitrate"] = before.bitrate
                if before.user_limit != after.user_limit:
                    edit_kwargs["user_limit"] = before.user_limit

            if before.overwrites != after.overwrites:
                edit_kwargs["overwrites"] = before.overwrites

            if edit_kwargs:
                await after.edit(reason="Anti-nuke: Reverting channel update", **edit_kwargs)
                print(f"[Antinuke] anti_channel_update: reverted '{before.name}'")

        except discord.Forbidden:
            print(f"[Antinuke] anti_channel_update: missing permission to revert channel")
        except Exception as e:
            print(f"[Antinuke] anti_channel_update: error reverting channel: {e}")
        finally:
            await asyncio.sleep(3)
            self._channel_update_cooldown.discard(cooldown_key)

        member = before.guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Updated a channel | User not whitelisted")



    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        guild_id = str(role.guild.id)

        if not _is_enabled(guild_id, 'anti_role_create'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(role.guild, discord.AuditLogAction.role_create)
        if entry is None:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == role.guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_role_create'):
            return

        print(f"[Antinuke] anti_role_create triggered by {pakad} ({pakad.id}) — role: {role.name}")

        try:
            await role.delete(reason="Anti-nuke: Role created by unwhitelisted user")
        except discord.Forbidden:
            print(f"[Antinuke] anti_role_create: missing permission to delete role")
        except Exception as e:
            print(f"[Antinuke] anti_role_create: error deleting role: {e}")

        member = role.guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Created a role | User not whitelisted")



    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild_id = str(role.guild.id)

        if not _is_enabled(guild_id, 'anti_role_delete'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(role.guild, discord.AuditLogAction.role_delete)
        if entry is None:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == role.guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_role_delete'):
            return

        print(f"[Antinuke] anti_role_delete triggered by {pakad} ({pakad.id}) — role: {role.name}")

        try:
            restored = await role.guild.create_role(
                name=role.name,
                color=role.color,
                permissions=role.permissions,
                hoist=role.hoist,
                mentionable=role.mentionable,
                reason="Anti-nuke: Restoring deleted role"
            )
            print(f"[Antinuke] anti_role_delete: restored role '{restored.name}'")
        except discord.Forbidden:
            print(f"[Antinuke] anti_role_delete: missing permission to create role")
        except Exception as e:
            print(f"[Antinuke] anti_role_delete: error restoring role: {e}")

        member = role.guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Deleted a role | User not whitelisted")



    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        guild_id = str(before.guild.id)

        if not _is_enabled(guild_id, 'anti_role_update'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(before.guild, discord.AuditLogAction.role_update)
        if entry is None:
            return

        if entry.target and entry.target.id != before.id:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == before.guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_role_update'):
            return

        print(f"[Antinuke] anti_role_update triggered by {pakad} ({pakad.id}) — role: {before.name}")

        try:
            await after.edit(
                name=before.name,
                color=before.color,
                permissions=before.permissions,
                hoist=before.hoist,
                mentionable=before.mentionable,
                reason="Anti-nuke: Reverting role update"
            )
            print(f"[Antinuke] anti_role_update: reverted '{before.name}'")
        except discord.Forbidden:
            print(f"[Antinuke] anti_role_update: missing permission to edit role")
        except Exception as e:
            print(f"[Antinuke] anti_role_update: error reverting role: {e}")

        member = before.guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Updated a role | User not whitelisted")



    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        guild_id = str(after.id)

        if not _is_enabled(guild_id, 'anti_server'):
            return

        await asyncio.sleep(1.0)

        # Use `after` for audit log — `before` is a snapshot and may not have live perms
        entry = await _get_audit_entry(after, discord.AuditLogAction.guild_update)
        if entry is None:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == after.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_server'):
            return

        print(f"[Antinuke] anti_server triggered by {pakad} ({pakad.id}) in {guild_id}")

        try:
            edit_kwargs = {}

            if before.name != after.name:
                edit_kwargs["name"] = before.name

            if before.icon != after.icon:
                try:
                    icon_bytes = await before.icon.read() if before.icon else None
                    edit_kwargs["icon"] = icon_bytes
                except Exception as e:
                    print(f"[Antinuke] anti_server: could not read original icon: {e}")

            if before.verification_level != after.verification_level:
                edit_kwargs["verification_level"] = before.verification_level

            if before.default_notifications != after.default_notifications:
                edit_kwargs["default_notifications"] = before.default_notifications

            if before.explicit_content_filter != after.explicit_content_filter:
                edit_kwargs["explicit_content_filter"] = before.explicit_content_filter

            if before.afk_channel != after.afk_channel:
                edit_kwargs["afk_channel"] = before.afk_channel

            if before.afk_timeout != after.afk_timeout:
                edit_kwargs["afk_timeout"] = before.afk_timeout

            if before.system_channel != after.system_channel:
                edit_kwargs["system_channel"] = before.system_channel

            if edit_kwargs:
                await after.edit(reason="Anti-nuke: Reverting server update", **edit_kwargs)
                print(f"[Antinuke] anti_server: reverted server settings")

        except discord.Forbidden:
            print(f"[Antinuke] anti_server: missing permission to edit guild")
        except Exception as e:
            print(f"[Antinuke] anti_server: error reverting guild: {e}")

        member = after.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Server settings updated | User not whitelisted")



    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        guild    = channel.guild
        guild_id = str(guild.id)

        if not _is_enabled(guild_id, 'anti_webhook'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(guild, discord.AuditLogAction.webhook_create)
        if entry is None:
            return  # No recent webhook creation — could be edit/delete, ignore

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_webhook'):
            return

        print(f"[Antinuke] anti_webhook triggered by {pakad} ({pakad.id}) in {guild_id}")

        try:
            webhooks = await channel.webhooks()
            deleted  = 0
            for webhook in webhooks:
                if webhook.user and webhook.user.id == pakad.id:
                    await webhook.delete(reason="Anti-nuke: Webhook created by unwhitelisted user")
                    deleted += 1
            print(f"[Antinuke] anti_webhook: deleted {deleted} webhook(s) by {pakad}")
        except discord.Forbidden:
            print(f"[Antinuke] anti_webhook: missing permission to manage webhooks")
        except Exception as e:
            print(f"[Antinuke] anti_webhook: error deleting webhooks: {e}")

        member = guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Created a webhook | User not whitelisted")



    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        guild_id = str(guild.id)

        if not _is_enabled(guild_id, 'anti_ban'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(guild, discord.AuditLogAction.ban)
        if entry is None:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_ban'):
            return

        print(f"[Antinuke] anti_ban triggered: {user} banned by {pakad} ({pakad.id}) in {guild_id}")

        try:
            await guild.unban(user, reason="Anti-nuke: Reversing ban by unwhitelisted user")
            print(f"[Antinuke] anti_ban: unbanned {user}")
        except discord.Forbidden:
            print(f"[Antinuke] anti_ban: missing permission to unban {user}")
        except discord.NotFound:
            print(f"[Antinuke] anti_ban: {user} not found in ban list")
        except Exception as e:
            print(f"[Antinuke] anti_ban: error unbanning: {e}")

        member = guild.get_member(pakad.id)
        if member:
            await self.punish(member, _get_punishment(guild_id),
                              "Anti-nuke: Banned a member | User not whitelisted")



    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild    = member.guild
        guild_id = str(guild.id)

        if not _is_enabled(guild_id, 'anti_kick'):
            return

        await asyncio.sleep(1.0)

        entry = await _get_audit_entry(guild, discord.AuditLogAction.kick)
        if entry is None:
            return  # Not a kick — natural leave, ignore

        # Make sure this kick entry matches the member who left
        if entry.target and entry.target.id != member.id:
            return

        pakad = entry.user
        if pakad.id == self.bot.user.id or pakad.id == guild.owner_id:
            return
        if _is_whitelisted(guild_id, pakad.id, 'anti_kick'):
            return

        print(f"[Antinuke] anti_kick triggered: {member} kicked by {pakad} ({pakad.id}) in {guild_id}")

        punisher = guild.get_member(pakad.id)
        if punisher:
            await self.punish(punisher, _get_punishment(guild_id),
                              "Anti-nuke: Kicked a member | User not whitelisted")


async def setup(bot: commands.Bot):
    await bot.add_cog(AntinukeEvents(bot))