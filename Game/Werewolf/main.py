import discord

from Game.Werewolf import manager


async def main(game: dict):
    werewolf_manager = manager.WerewolfManager(game)
    await werewolf_manager.game_start()

    while True:
        await werewolf_manager.night()

        if await werewolf_manager.win_check():
            break

        await werewolf_manager.day()

        if await werewolf_manager.win_check():
            break
