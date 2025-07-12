import discord
from discord.ext import commands
from dotenv import load_dotenv

import json
import os

from veto import Veto
from utils import display_list, parse_users

load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
startgg_token = os.getenv("STARTGG_TOKEN")

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
    guild = discord.Object(id=guild_id)
    synced = await bot.tree.sync(guild=guild)
    print(f"Synced {len(synced)} command(s) to guild {guild_id}")

@bot.event
async def on_message(message):
    # Handles map veto (messages starting with -)
    if message.content.startswith("-") and bot.active_veto is not None:
        try:
            map_to_ban = message.content[1:]
            if bot.active_veto.can_user_ban(int(message.author.id)):
                bot.active_veto.ban(map_to_ban, int(message.author.id))

                if bot.active_veto.completed:
                    maps_text = display_list(bot.active_veto.maps_remaining)
                    bot.active_veto = None
                    await message.channel.send("Banned map " + map_to_ban.capitalize() +
                                               "\nMap(s) for the match: " + maps_text)
                else:
                    mentions = " ".join(f"<@{user_id}>" for user_id in bot.active_veto.active_team)
                    await message.channel.send(f"Banned map {map_to_ban.capitalize()}"+
                                               f"\nTeam banning: {mentions}"
                                               f"\nMaps remaining: {display_list(bot.active_veto.maps_remaining)}")
        except ValueError as e:
            await message.channel.send(str(e))


@bot.tree.command(name="mappool", description="Lists the current map pool", guild=discord.Object(id=guild_id))
async def map_pool(interaction: discord.Interaction):
    with open("config.json", "r") as f:
        data = json.load(f)
    await interaction.response.send_message("**Current map pool:** " + display_list(data["maps"]))

@bot.tree.command(name="startveto", description="Starts a veto for the specified number of maps (default 1)", guild=discord.Object(id=guild_id))
async def start_veto(interaction: discord.Interaction, team1: str, team2: str, num_maps: int = 1):
    if num_maps != 1 and num_maps != 3 and num_maps != 5:
        await interaction.response.send_message("Invalid veto. Supply 1, 3 or 5 maps.")
    with open("config.json", "r") as f:
        data = json.load(f)
    maps = data["maps"]
    if bot.active_veto is not None:
        await interaction.response.send_message("There is already an active veto.")
    bot.active_veto = Veto(maps, parse_users(team1), parse_users(team2), num_maps)
    mentions = " ".join(f"<@{user_id}>" for user_id in bot.active_veto.active_team)
    await interaction.response.send_message(f"**Starting Veto With:** {display_list(maps)}" +
                                            f"\n Team banning: {mentions}" +
                                            "\n Type -<map> to ban a map.")

bot.run(discord_token)