import discord
from discord import app_commands
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
                                               f"\nTeam banning: {mentions}" +
                                               f"\nMaps remaining: {display_list(bot.active_veto.maps_remaining)}")
        except ValueError as e:
            await message.channel.send(str(e))

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingAnyRole):
        if interaction.response.is_done():
            await interaction.followup.send("You don’t have the required role to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message("You don’t have the required role to use this command.", ephemeral=True)
    else:
        print(f"Unhandled error: {error}")

@bot.tree.command(name="maplist", description="Lists the current map pool", guild=discord.Object(id=guild_id))
async def list_map_pool(interaction: discord.Interaction):
    with open("config.json", "r") as f:
        data = json.load(f)
    await interaction.response.send_message("**Current map pool:** " + display_list(data["maps"]))


@bot.tree.command(name="mapreplace", description="Replace a map in the pool", guild=discord.Object(id=guild_id))
@app_commands.checks.has_any_role("Admin", "Tournament Organizer")
async def replace_map(interaction: discord.Interaction, map_to_replace:str, new_map:str):
    with open("config.json", "r") as f:
        data = json.load(f)
    maps = data.get("maps", [])
    # Case-insensitive check
    try:
        index = next(i for i, m in enumerate(maps) if m.lower() == map_to_replace.lower())
    except StopIteration:
        await interaction.response.send_message(f"Map `{map_to_replace}` not found in the current pool.", ephemeral=True)
        return
    old_map = maps[index]
    maps[index] = new_map
    data["maps"] = maps
    with open("config.json", "w") as f:
        json.dump(data, f, indent=4)

    await interaction.response.send_message(
        f"Replaced map `{old_map.capitalize()}` with `{new_map.capitalize()}`.\n**New map pool:** {display_list(maps)}"
    )

@bot.tree.command(name="startveto", description="Starts a veto for the specified number of maps (default 1)", guild=discord.Object(id=guild_id))
@app_commands.checks.has_any_role("Admin", "Tournament Organizer")
async def start_veto(interaction: discord.Interaction, team1: str, team2: str, num_maps: int = 1):
    if num_maps != 1 and num_maps != 3 and num_maps != 5:
        await interaction.response.send_message("Invalid veto. Supply 1, 3 or 5 maps.", ephemeral=True)
    with open("config.json", "r") as f:
        data = json.load(f)
    maps = data["maps"]
    if bot.active_veto is not None:
        await interaction.response.send_message("There is already an active veto.", ephemeral=True)
    bot.active_veto = Veto(maps, parse_users(team1), parse_users(team2), num_maps)
    mentions_active = " ".join(f"<@{user_id}>" for user_id in bot.active_veto.active_team)
    mentions_t1 = " ".join(f"<@{user_id}>" for user_id in bot.active_veto.team1)
    mentions_t2 = " ".join(f"<@{user_id}>" for user_id in bot.active_veto.team2)
    await interaction.response.send_message(f"**Starting Veto With:** {display_list(maps)}" +
                                            f"\nTeams: {mentions_t1} vs. {mentions_t2}" +
                                            f"\n Team banning: {mentions_active}" +
                                            "\n Type -<map> to ban a map.")

@bot.tree.command(name="cancelveto", description="Cancels the active veto", guild=discord.Object(id=guild_id))
@app_commands.checks.has_any_role("Admin", "Tournament Organizer")
async def cancel_veto(interaction: discord.Interaction):
    if bot.active_veto is not None:
        bot.active_veto = None
        await interaction.response.send_message("Cancelled active veto")
    else:
        await interaction.response.send_message("No active veto.")

bot.run(discord_token)