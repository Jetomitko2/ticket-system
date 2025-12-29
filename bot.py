import os
import json
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
from html import escape
from datetime import datetime

# ======================================================
# ENV
# ======================================================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CREATE_CHANNEL_ID = int(os.getenv("CREATE_CHANNEL_ID"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
ARCHIVE_CATEGORY_ID = int(os.getenv("ARCHIVE_CATEGORY_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))

DATA_FILE = "tickets.json"
EXPORT_DIR = "exports/html"
os.makedirs(EXPORT_DIR, exist_ok=True)

# ======================================================
# STORAGE
# ======================================================
def load_data():
    default = {
        "last_ticket_id": 0,
        "panel_message_id": None,
        "tickets": {}
    }
    if not os.path.exists(DATA_FILE):
        return default
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return default
    for k, v in default.items():
        if k not in data:
            data[k] = v
    return data

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ======================================================
# INTENTS
# ======================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================================
# HTML EXPORT HELPERS
# ======================================================
def sanitize_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", value)[:120]

def is_image(att: discord.Attachment) -> bool:
    if att.content_type and att.content_type.startswith("image/"):
        return True
    ext = os.path.splitext(att.filename or "")[1].lower()
    return ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

async def export_channel_to_html(channel: discord.TextChannel):
    messages = []
    async for m in channel.history(limit=None, oldest_first=True):
        messages.append(m)

    parts = []
    for m in messages:
        author = escape(m.author.display_name)
        avatar = m.author.display_avatar.url
        content = escape(m.clean_content or "").replace("\n", "<br>")
        ts = m.created_at.strftime("%Y-%m-%d %H:%M:%S")

        att_html = ""
        for att in m.attachments:
            if is_image(att):
                att_html += f'<div class="att image"><img src="{att.url}"></div>'
            else:
                att_html += f'<div class="att file">📎 <a href="{att.url}">{escape(att.filename)}</a></div>'

        parts.append(f"""
        <div class="message">
            <img class="avatar" src="{avatar}">
            <div class="bubble">
                <div class="header">
                    <span class="author">{author}</span>
                    <span class="time">{ts}</span>
                </div>
                <div class="content">{content}</div>
                <div class="attachments">{att_html}</div>
            </div>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(channel.name)}</title>
<style>
body {{
    background:#0b0e14;
    color:#e6e6e6;
    font-family:Segoe UI,Arial,sans-serif;
    margin:0;
}}
.container {{ max-width:900px;margin:auto;padding:20px; }}
.message {{ display:flex;gap:12px;padding:12px;border-bottom:1px solid #1f2937; }}
.avatar {{ width:42px;height:42px;border-radius:50%; }}
.bubble {{ background:#111827;border-radius:10px;padding:10px 12px;flex:1; }}
.header {{ display:flex;gap:10px;font-size:14px; }}
.author {{ font-weight:600; }}
.time {{ color:#9ca3af;font-size:12px; }}
.content {{ margin-top:6px;line-height:1.4; }}
.attachments {{ margin-top:8px;display:grid;gap:8px; }}
.att.image img {{ max-width:320px;border-radius:8px; }}
.att.file a {{ color:#60a5fa;text-decoration:none; }}
</style>
</head>
<body>
<div class="container">
<h2>{escape(channel.guild.name)} — #{escape(channel.name)}</h2>
{''.join(parts)}
</div>
</body>
</html>
"""

    filename = f"{sanitize_filename(channel.guild.name)}_{sanitize_filename(channel.name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(html)
    return path

# ======================================================
# READY
# ======================================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.add_view(CreateTicketView())
    bot.add_view(CloseTicketView())
    await bot.tree.sync()
    await ensure_ticket_panel()

# ======================================================
# PANEL
# ======================================================
async def ensure_ticket_panel():
    channel = bot.get_channel(CREATE_CHANNEL_ID)
    if not channel:
        return

    pid = data["panel_message_id"]
    if pid:
        try:
            msg = await channel.fetch_message(pid)
            await msg.edit(view=CreateTicketView())
            return
        except discord.NotFound:
            data["panel_message_id"] = None
            save_data()

    embed = discord.Embed(
        title="🎫 Support Tickets",
        description="Click **Create Ticket** to open a support ticket.\nAll communication happens via **DMs**.",
        color=0x5865F2
    )
    msg = await channel.send(embed=embed, view=CreateTicketView())
    data["panel_message_id"] = msg.id
    save_data()

# ======================================================
# CREATE TICKET VIEW
# ======================================================
class CreateTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        emoji="🎫",
        style=discord.ButtonStyle.green,
        custom_id="ticket:create"
    )
    async def create_ticket(self, interaction: discord.Interaction, _):
        uid = str(interaction.user.id)

        if uid in data["tickets"]:
            await interaction.response.send_message(
                "❌ You already have an open ticket.",
                ephemeral=True
            )
            return

        data["last_ticket_id"] += 1
        tid = data["last_ticket_id"]

        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        username = sanitize_filename(interaction.user.name.lower())
        channel_name = f"{username}-{tid}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites
        )

        data["tickets"][uid] = {
            "ticket_id": tid,
            "channel_id": channel.id
        }
        save_data()

        await channel.send(
            embed=discord.Embed(
                title=f"🎫 Ticket #{tid}",
                description="This ticket is handled via **DMs**.",
                color=0x2ECC71
            ),
            view=CloseTicketView()
        )

        await interaction.user.send(
            embed=discord.Embed(
                title=f"🎫 Ticket #{tid} Opened",
                description="Reply here to contact support.",
                color=0x2ECC71
            ),
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            "✅ Ticket created. Check your DMs.",
            ephemeral=True
        )

# ======================================================
# CLOSE VIEW
# ======================================================
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.red,
        custom_id="ticket:close"
    )
    async def close_ticket(self, interaction: discord.Interaction, _):
        if isinstance(interaction.channel, discord.DMChannel):
            ticket = data["tickets"].get(str(interaction.user.id))
            if not ticket:
                await interaction.response.send_message(
                    "❌ No active ticket.",
                    ephemeral=True
                )
                return
            channel = bot.get_channel(ticket["channel_id"])
        else:
            channel = interaction.channel

        await close_ticket_logic(channel)
        await interaction.response.send_message("🔒 Ticket closed.", ephemeral=True)

# ======================================================
# CLOSE LOGIC
# ======================================================
async def close_ticket_logic(channel: discord.TextChannel):
    for uid, t in list(data["tickets"].items()):
        if t["channel_id"] == channel.id:
            html_path = await export_channel_to_html(channel)

            archive = channel.guild.get_channel(ARCHIVE_CATEGORY_ID)
            if archive:
                await channel.edit(category=archive)

            await channel.send(file=discord.File(html_path))

            user = await bot.fetch_user(int(uid))
            await user.send(
                "🔒 Your ticket has been closed. Here is the transcript:",
                file=discord.File(html_path)
            )

            del data["tickets"][uid]
            save_data()
            return

# ======================================================
# MESSAGE MIRROR + ATTACHMENTS
# ======================================================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    files = [await a.to_file() for a in message.attachments]

    # USER → SUPPORT
    if isinstance(message.channel, discord.DMChannel):
        ticket = data["tickets"].get(str(message.author.id))
        if not ticket:
            return

        channel = bot.get_channel(ticket["channel_id"])
        embed = discord.Embed(
            description=message.content or "",
            color=0x2B2D31
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )
        await channel.send(embed=embed, files=files)
        return

    # SUPPORT → USER
    for uid, t in data["tickets"].items():
        if message.channel.id == t["channel_id"]:
            user = await bot.fetch_user(int(uid))
            embed = discord.Embed(
                description=message.content or "",
                color=0x5865F2
            )
            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )
            await user.send(embed=embed, files=files)

    await bot.process_commands(message)

# ======================================================
# RUN
# ======================================================
bot.run(TOKEN)
