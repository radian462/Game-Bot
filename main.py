import os

import discord
from discord import app_commands

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print("ログインしました")


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
@app_commands.describe(limit="人数制限")
async def werewolf(interaction: discord.Interaction, limit: int = 10):
    await interaction.response.defer()
    embed = discord.Embed(
        title=f"人狼ゲーム(1/{limit})",
        description=f"募集者:<@!{interaction.user.id}>",
        color=discord.Color.green(),
    )
    await interaction.followup.send(embed=embed)


client.run(os.getenv("DISCORD_TOKEN"))
