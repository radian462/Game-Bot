import discord

from Game.Werewolf import manager


async def main(id: int):
    werewolf_manager = manager.WerewolfManager(id)
    game = werewolf_manager.game
    await werewolf_manager.game_start()

    while True:
        await werewolf_manager.night()

        await werewolf_manager.win_check()
        if game is not None and game.is_ended:
            break

        await werewolf_manager.day()

        await werewolf_manager.win_check()
        if game is not None and game.is_ended:
            break

    await werewolf_manager.execute_game_end()
