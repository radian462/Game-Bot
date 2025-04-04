import discord

import Modules.global_value as g

from ...player import Player
from ...role import Role
from ...view import PlayerChoiceView


class Hunter(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()

    async def night_ability(self, game_id: int, player: Player):
        game = g.werewolf_games.get(game_id)
        self.t = game.translator

        embed = discord.Embed(title="護衛", description="護衛対象を選んでください")
        view = PlayerChoiceView(
            choices=game.last_alive_players,
            process="Ability",
            allow_skip=False,
            game_id=game_id,
        )
        await player.message(embed=embed, view=view)
        await view.wait()

        target_id = list(view.votes.values())[0]
        target = next((p for p in game.players if p.id == target_id), None)

        target.is_kill_protected = True

        await player.message(f"{target.name}を守ります。")
