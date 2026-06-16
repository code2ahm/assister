# Assister

> A powerful all-in-one Discord bot built with Python. Antinuke, automod, moderation, logging, autoroles, giveaways, and more all in one.

[![Invite](https://img.shields.io/badge/Invite-Assister-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1496794996228231229&permissions=8&integration_type=0&scope=bot)
[![Support](https://img.shields.io/badge/Support_Server-Join-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/invite/jaed6STG7e)
[![Docs](https://img.shields.io/badge/Docs-assisterbot.xyz-000000?style=for-the-badge&logo=gitbook&logoColor=white)](https://assisterbot.xyz/docs)

---

## Features

- **Antinuke** - raid protection, mass ban/kick/channel destruction prevention
- **Automod** - spam, links, invite, and swear filter running 24/7
- **Moderation** - ban, kick, mute, purge, nuke, and more
- **Auto Roles** - assign roles to humans and bots on join
- **Voice** - mute, deafen, move members, join-to-create channels
- **Giveaways** - start, end, reroll, manage
- **Reaction Role** - self-assign roles by reacting to panel messages
- **Utility** - serverinfo, snipe, polls, reminders, avatar, roleinfo
- **General** - search, translate, currency converter, timers, jokes
- **Extra** - autoresponder, autoreact, media-only channels, profile badges

---

## Requirements

- Python `3.10+`
- A Discord bot token
- The following packages (see `requirements.txt`):

```yaml
discord.py>=2.6
jishaku
aiohttp
humanfriendly
psutil
requests
beautifulsoup4
ddgs
googletrans==4.0.0rc1
PyNaCl
colorlog
davey
deep-translator
```

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/code2ahm/assister.git
cd assister

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your token and variables (see below)

# 4. Run
python main.py
```

---

## Configuration

### `utils/token.py`

Add your bot token here:

```python
TOKEN = "your-bot-token-here"
```

### `utils/variables.py`

Replace the following with your own values:

```python
colour   = 0xYOURCOLOR       # embed color (hex)
ahmw1    = "WEBHOOK_URL"     # command log webhook
ahmw2    = "WEBHOOK_URL"     # cooldown log webhook
tick     = "✅"               # or your custom emoji
cross    = "❌"
e_dot    = "•"
blnk     = "\u200b"
animated_cross = "<a:cross:ID>"  # animated emoji ID
```

### `utils/prefixes.py`

Default prefix logic lives here. The bot reads per-guild prefixes from `prefixes.json`. Default prefix is `.`

### Developer IDs

In `utils/checks.py`, add your Discord user ID to the developer list so you can use owner-only commands like `.reload` and `.cmdids`.

---

## Project Structure

```yaml
assister/
├── cogs/               # all command categories (autoloaded)
├── utils/
│   ├── token.py        # bot token
│   ├── variables.py    # colors, webhooks, emojis
│   ├── prefixes.py     # per-guild prefix handling
│   ├── checks.py       # permission checks, developer guard
│   ├── loads.py        # cog loader helpers
│   ├── blacklists.py   # blacklisted users/guilds
│   ├── paginator.py    # embed paginator
│   └── helplund.py     # help command data
├── main.py             # entry point
├── requirements.txt
└── *.json              # per-feature data files (automod, antinuke, etc.)
```

---

## Data Files

The bot stores feature configs as flat JSON files in the root directory. These are auto-created but you can pre-populate them:

| File               | Purpose                     |
| ------------------ | --------------------------- |
| `reactionrole.json` | Reaction role panel data        |
| `prefixes.json`    | Per-guild custom prefixes   |
| `antinuke.json`    | Antinuke settings per guild |
| `automod.json`     | Automod config              |
| `autorole.json`    | Auto role assignments       |
| `giveaways.json`   | Active giveaway data        |
| `welcome.json`     | Welcome message config      |
| `autoreact.json`   | Auto-react triggers         |
| `autorespond.json` | Auto-responder rules        |
| `noprefix.txt`     | Users with no-prefix access |
| `blacklists.txt`   | Blacklisted user/guild IDs  |

---

<div align="center">
<sub>built by <a href="https://github.com/code2ahm">Ahmar Yaseen</a> · <a href="https://assisterbot.xyz/docs">docs</a> · <a href="https://assisterbot.xyz/tos">tos</a> · <a href="https://assisterbot.xyz/pp">privacy</a> · MIT License</sub>
</div>
