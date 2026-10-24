import json
import os
import random
from pathlib import Path

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
MODE = os.getenv("MODE", "cycle")  # "cycle" = in order, "random" = shuffle
RESET_WHEN_EVENT_ENDS = os.getenv("RESET_WHEN_EVENT_ENDS", "true").lower() == "true"

ICON_DIR = Path("icons")
DEFAULT_ICON = ICON_DIR / "default.png"  # shown when no event is running
STATE_FILE = Path("state.json")

intents = discord.Intents.default()  # includes guild_scheduled_events
client = discord.Client(intents=intents)


def event_icons() -> list[Path]:
    files = sorted(p for p in ICON_DIR.glob("*.png") if p.name != "default.png")
    return files


def load_index() -> int:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text()).get("index", 0)
    return 0


def save_index(i: int) -> None:
    STATE_FILE.write_text(json.dumps({"index": i}))


def pick_icon() -> Path | None:
    icons = event_icons()
    if not icons:
        return None
    if MODE == "random":
        return random.choice(icons)
    i = load_index() % len(icons)
    save_index(i + 1)
    return icons[i]


async def set_icon(guild: discord.Guild, path: Path, reason: str) -> None:
    try:
        await guild.edit(icon=path.read_bytes(), reason=reason)
        print(f"Icon set to {path.name} ({reason})")
    except discord.Forbidden:
        print("Missing permission: the bot needs Manage Server.")
    except discord.HTTPException as e:
        print(f"Discord rejected the icon change: {e}")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_scheduled_event_update(before, after):
    if after.guild.id != GUILD_ID or before.status == after.status:
        return

    if after.status == discord.EventStatus.active:
        icon = pick_icon()
        if icon:
            await set_icon(after.guild, icon, f"Event started: {after.name}")

    elif after.status in (discord.EventStatus.completed, discord.EventStatus.cancelled):
        if RESET_WHEN_EVENT_ENDS and DEFAULT_ICON.exists():
            await set_icon(after.guild, DEFAULT_ICON, f"Event ended: {after.name}")


client.run(TOKEN)
