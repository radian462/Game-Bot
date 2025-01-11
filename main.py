import os

import discord
from discord import app_commands

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print("ログインしました")


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
async def werewolf(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(title="人狼")
    await interaction.followup.send(embed=embed)


client.run(os.getenv("DISCORD_TOKEN"))
