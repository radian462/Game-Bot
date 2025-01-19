import discord

from Game.Werewolf import manager


async def main(game: dict, client: discord.Client):
    werewolf_manager = manager.WerewolfManager(game, client)
    await werewolf_manager.game_start()

    await werewolf_manager.night()
