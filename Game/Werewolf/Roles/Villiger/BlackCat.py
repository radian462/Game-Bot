import random

import Modules.global_value as g

from ...role import Role


class BlackCat(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()

    async def executed_ability(self, game_id: int, player):
        game = g.werewolf_games.get(game_id)
        filtered_players = [p for p in game.alive_players if p.id != player.id]

        revenge_target = random.choice(filtered_players)
        await revenge_target.execute("Revenged")
        game.refresh_alive_players()
