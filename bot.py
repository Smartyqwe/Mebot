# bot.py
# pip install discord.py python-aternos

import discord
from discord.ext import commands, tasks
from discord import app_commands
import python_aternos as aternos_lib
import asyncio
import os

# ── Config ────────────────────────────────────────────────────────────────
ATERNOS_USER   = os.environ["ATERNOS_USER"]      # your aternos username
ATERNOS_PASS   = os.environ["ATERNOS_PASS"]      # your aternos password
SERVER_INDEX   = 0                                # 0 = first server on your account
DISCORD_TOKEN  = os.environ["DISCORD_TOKEN"]
STATUS_CHANNEL = int(os.environ["STATUS_CHANNEL"])  # channel id to post status msgs

# ── Aternos client ────────────────────────────────────────────────────────
atclient = aternos_lib.Client.from_credentials(ATERNOS_USER, ATERNOS_PASS)
mc_server = atclient.list_servers()[SERVER_INDEX]

# ── Discord setup ─────────────────────────────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ── Slash command: /start ─────────────────────────────────────────────────
@tree.command(name="start", description="Start the Minecraft server if it's offline")
async def start_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)

    status = mc_server.status  # 'online' | 'offline' | 'starting' | 'stopping'

    if status == "online":
        await interaction.followup.send("✅ Server is already online! Join at `{}`".format(mc_server.address))
        return

    if status == "starting":
        await interaction.followup.send("⏳ Server is already starting up, hang tight...")
        return

    if status == "stopping":
        await interaction.followup.send("⚠️ Server is stopping right now, try again in a minute.")
        return

    # status == "offline" — boot it
    await interaction.followup.send("🥔 Booting the server, give it 60–90 seconds...")
    mc_server.start()

    # Poll until online, then confirm
    for _ in range(24):           # max ~2 min of waiting
        await asyncio.sleep(5)
        mc_server.fetch()         # refresh status from aternos
        if mc_server.status == "online":
            channel = bot.get_channel(STATUS_CHANNEL)
            await channel.send(
                f"✅ **Server is online!** Join at `{mc_server.address}`\n"
                f"Players online: {mc_server.players_on}/{mc_server.slots}"
            )
            return

    await interaction.followup.send("⚠️ Server took too long to start — check the Aternos panel.")


# ── Slash command: /status ────────────────────────────────────────────────
@tree.command(name="status", description="Check the current server status")
async def status_cmd(interaction: discord.Interaction):
    mc_server.fetch()
    status = mc_server.status
    emoji  = {"online": "✅", "offline": "🔴", "starting": "⏳", "stopping": "🛑"}.get(status, "❓")
    await interaction.response.send_message(
        f"{emoji} Server is **{status}**\n"
        f"Address: `{mc_server.address}`\n"
        f"Players: {mc_server.players_on}/{mc_server.slots}"
    )


# ── On ready: sync slash commands ─────────────────────────────────────────
@bot.event
async def on_ready():
    await tree.sync()
    print(f"[+] Logged in as {bot.user} — slash commands synced")


bot.run(DISCORD_TOKEN)