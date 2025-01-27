import discord

from Game.Werewolf import manager


async def main(game: dict, client: discord.Client):
    werewolf_manager = manager.WerewolfManager(game, client)
    await werewolf_manager.game_start()

    while True:
        await werewolf_manager.night()

        if werewolf_manager.win_check():
            break

        await werewolf_manager.day()

        if werewolf_manager.win_check():
            break

    await werewolf_manager.game_end()
    del werewolf_manager
