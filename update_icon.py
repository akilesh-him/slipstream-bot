import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_IDS = [g.strip() for g in os.environ["GUILD_IDS"].split(",") if g.strip()]
TZ = os.getenv("TIMEZONE", "America/Chicago")

today = datetime.now(ZoneInfo(TZ)).strftime("%m-%d")

with open("holidays.json") as f:
    data = json.load(f)


def is_active(h):
    start, end = h["start"], h["end"]
    if start <= end:
        return start <= today <= end
    return today >= start or today <= end  # range crosses new year


match = next((h for h in data["holidays"] if is_active(h)), None)
icon_key = match["icon"] if match else data["default"]
print(f"Today is {today}: {match['name'] if match else 'no holiday'} -> {icon_key}")

body = json.dumps({"icon": "data:image/png;base64," + data["icons"][icon_key]}).encode()

failed = False
for gid in GUILD_IDS:
    req = urllib.request.Request(
        f"https://discord.com/api/v10/guilds/{gid}",
        data=body,
        method="PATCH",
        headers={
            "Authorization": f"Bot {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (slipstream-icons, 1.0)",
        },
    )
    try:
        urllib.request.urlopen(req)
        print(f"[{gid}] icon updated")
    except urllib.error.HTTPError as e:
        print(f"[{gid}] failed: {e.code} {e.read().decode()}")
        failed = True

sys.exit(1 if failed else 0)
