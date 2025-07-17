import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import json
import os

from veto import Veto, VetoAction
from utils import display_list, parse_users, get_veto_for_channel

load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
startgg_token = os.getenv("STARTGG_TOKEN")

guild_id = 1392628719935291442
description = '''Bot for Esports NL'''

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', description=description, intents=intents)
# Bot state
bot.active_vetoes = []


@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    # Register commands
    guild = discord.Object(id=guild_id)
    synced = await bot.tree.sync(guild=guild)
    print(f"Synced {len(synced)} command(s) to guild {guild_id}")


@bot.event
async def on_message(message):
    # Handles map veto (messages starting with - or +)
    veto = get_veto_for_channel(bot.active_vetoes, message.channel.id)
    if veto is not None:
        action_made = False
        map_choice = ""
        veto_action = veto.get_veto_action()
        if (message.content.startswith("-") and veto is not None
                and veto.get_veto_action() == VetoAction.Ban):
            try:
                map_choice = message.content[1:]
                if veto.can_user_ban(int(message.author.id)):
                    veto.ban(map_choice, int(message.author.id))
                    action_made = True
            except ValueError as e:
                await message.channel.send(str(e))

        elif (message.content.startswith("+") and veto is not None
                and veto.get_veto_action() == VetoAction.Pick):
            try:
                map_choice = message.content[1:]
                if veto.can_user_ban(int(message.author.id)):
                    veto.pick(map_choice, int(message.author.id))
                    action_made = True
            except ValueError as e:
                await message.channel.send(str(e))

        if veto.completed and action_made:
            action_text = "Banned" if veto_action == VetoAction.Ban else "Picked"
            maps_text = display_list(veto.picked_maps)
            bot.active_vetoes.remove(veto)
            await message.channel.send(f"{action_text} map " + map_choice.capitalize() +
                                       "\nMap(s) for the match: " + maps_text)
        elif action_made:
            action_text = "Banned" if veto_action == VetoAction.Ban else "Picked"
            next_action_text = "banning" if veto.get_veto_action() == VetoAction.Ban else "picking"
            mentions = " ".join(f"<@{user_id}>" for user_id in veto.active_team)
            await message.channel.send(f"{action_text} map {map_choice.capitalize()}" +
                                       f"\nTeam {next_action_text}: {mentions}" +
                                       f"\nMaps remaining: {display_list(veto.maps_remaining)}")


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
    veto = get_veto_for_channel(bot.active_vetoes, interaction.channel.id)
    if veto is not None:
        await interaction.response.send_message("There is already an active veto.", ephemeral=True)
    veto = Veto(int(interaction.channel.id), maps, parse_users(team1), parse_users(team2), num_maps)
    bot.active_vetoes.append(veto)
    mentions_active = " ".join(f"<@{user_id}>" for user_id in veto.active_team)
    mentions_t1 = " ".join(f"<@{user_id}>" for user_id in veto.team1)
    mentions_t2 = " ".join(f"<@{user_id}>" for user_id in veto.team2)
    await interaction.response.send_message(f"**Starting Veto With:** {display_list(maps)}" +
                                            f"\nTeams: {mentions_t1} vs. {mentions_t2}" +
                                            f"\n Team banning: {mentions_active}" +
                                            "\n Type -<map> to ban a map, and +<map> to pick a map.")


@bot.tree.command(name="cancelveto", description="Cancels the active veto", guild=discord.Object(id=guild_id))
@app_commands.checks.has_any_role("Admin", "Tournament Organizer")
async def cancel_veto(interaction: discord.Interaction):
    veto = get_veto_for_channel(bot.active_vetoes, interaction.channel.id)
    if veto is not None:
        bot.active_vetoes.remove(veto)
        await interaction.response.send_message("Cancelled active veto")
    else:
        await interaction.response.send_message("No active veto.")

bot.run(discord_token)
