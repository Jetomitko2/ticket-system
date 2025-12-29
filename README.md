# Discord DM Ticket Bot

A production-ready **Discord ticket bot** that operates entirely through **Direct Messages**, while keeping ticket channels private on the server for support staff only.

The bot supports **persistent buttons**, **file and image attachments**, **HTML transcripts**, and continues working correctly even after restarts.

---

## Overview

This bot provides a clean and private support system for Discord servers.  
Users never see ticket channels on the server – all communication happens via **DMs**, while the support team works inside private channels.

It is suitable for:
- Hosting providers
- Support servers
- Communities that want a clean ticket system without server clutter

---

## Features

- Ticket creation using a **Create Ticket** button
- All ticket communication via **Direct Messages**
- Server-side ticket channels visible only to:
  - Support role
  - Bot
- Ticket channel naming format:


<username>-<ticket-id>

- Tickets can be closed:
- from Direct Messages
- from the server ticket channel
- Automatic **HTML transcript generation** when a ticket is closed
- Transcripts are sent:
- to the ticket channel
- to the user via DM
- Full support for:
- Images
- Files
- Attachments (included in HTML transcripts)
- Persistent buttons (no “Interaction Failed” after restart)
- Tickets are archived instead of deleted
- All data is stored locally in `tickets.json`

---

## How It Works

1. The bot sends a **ticket panel** to a selected channel
2. A user clicks **Create Ticket**
3. The bot:
 - Creates a private ticket channel on the server
 - Sends a DM to the user
4. Messages are mirrored:
 - User DM → ticket channel
 - Support reply → user DM
5. When the ticket is closed:
 - The channel is moved to an archive category
 - An HTML transcript is generated
 - The transcript is sent to both the server and the user

---

## Project Structure

```text
.
├── bot.py
├── tickets.json
├── env.txt
├── requirements.txt
└── exports/
  └── html/
```

Requirements

Python 3.10 or newer

A Discord bot application

A Discord server with proper permissions

A hosting solution for 24/7 uptime (recommended)

Installation
Step 1 – Download the Project

Clone or download this repository from GitHub to your computer or server.

Step 2 – Rename the Environment File

Rename the file:

env.txt → .env


This step is required.
The bot will not start without the .env file.

Step 3 – Configure the .env File

Open .env and fill in your values:
```
BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN

CREATE_CHANNEL_ID=CHANNEL_ID_FOR_TICKET_PANEL
TICKET_CATEGORY_ID=CATEGORY_ID_FOR_ACTIVE_TICKETS
ARCHIVE_CATEGORY_ID=CATEGORY_ID_FOR_ARCHIVED_TICKETS
SUPPORT_ROLE_ID=SUPPORT_ROLE_ID
```
How to Get Discord IDs (Channels, Categories, Roles)

Open Discord

Go to User Settings

Open Advanced

Enable Developer Mode

After that:

Right-click a channel, category, or role

Click Copy ID

Paste the ID into the .env file

Creating a Discord Bot

Go to https://discord.com/developers/applications

Click New Application

Give the application a name

Open the Bot section

Click Add Bot

Copy the Bot Token and paste it into .env

Required Bot Permissions

The bot requires the following permissions:

Read Messages

Send Messages

Manage Channels

Manage Roles

Embed Links

Attach Files

Read Message History

Running the Bot Locally

Install dependencies:

pip install -r requirements.txt


Start the bot:

python bot.py

Hosting the Bot (Recommended)

For 24/7 uptime, a Python bot hosting service is recommended.

You can host this bot on:
https://hothost.org/

Steps:

Upload all project files

Set the startup file to bot.py

Install dependencies

Start the server

Data Storage

Active tickets and settings are stored in tickets.json

The file is managed automatically by the bot

Do not edit it manually while the bot is running

Notes

The bot is designed for single-server use

Restart-safe (persistent buttons and tickets)

HTML transcripts are saved locally and sent automatically

License

You are free to use, modify, and host this project for personal or commercial purposes.
