import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import os
from veto import Veto
from utils import display_list

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

guild_id = 1392628719935291442
description = '''Bot for Esports NL'''

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', description=description, intents=intents)
# Bot state
bot.active_veto = None

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    # Register commands
    guild_id = 1392628719935291442
    guild = discord.Object(id=guild_id)
    synced = await bot.tree.sync(guild=guild)
    print(f"Synced {len(synced)} command(s) to guild {guild_id}")

@bot.event
async def on_message(message):
    # Handles map veto (messages starting with -)
    if message.content.startswith("-") and bot.active_veto is not None:
        try:
            map_to_ban = message.content[1:]
            bot.active_veto.ban(map_to_ban)

            if bot.active_veto.completed:
                maps_text = display_list(bot.active_veto.maps_remaining)
                bot.active_veto = None
                await message.channel.send("Banned map " + map_to_ban.capitalize() +
                                           "\nMap(s) for the match: " + maps_text)
            else:
                await message.channel.send("Banned map " + map_to_ban.capitalize() +
                                           "\nMaps remaining: " + display_list(bot.active_veto.maps_remaining))
        except ValueError:
            await message.channel.send("Map not in map list")


@bot.tree.command(name="mappool", description="Lists the current map pool", guild=discord.Object(id=guild_id))
async def map_pool(interaction: discord.Interaction):
    with open("config.json", "r") as f:
        data = json.load(f)
    await interaction.response.send_message("**Current map pool:** " + display_list(data["maps"]))

@bot.tree.command(name="startveto", description="Starts a veto for the specified number of maps (default 1)", guild=discord.Object(id=guild_id))
async def start_veto(interaction: discord.Interaction, num_maps: int = 1):
    with open("config.json", "r") as f:
        data = json.load(f)
    maps = data["maps"]
    if bot.active_veto is not None:
        await interaction.response.send_message("There is already an active veto")
    bot.active_veto = Veto(maps, num_maps)
    await interaction.response.send_message("**Starting Veto With:** " + display_list(maps) +
                                            "\n Type -<map> to ban a map.")

bot.run(token)