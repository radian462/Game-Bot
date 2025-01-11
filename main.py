import os

import discord

from keep_alive import keep_alive


client = discord.Client(intents=discord.Intents.default())


@client.event
async def on_ready():
    print("ログインしました")


client.run(os.getenv("DISCORD_TOKEN"))
