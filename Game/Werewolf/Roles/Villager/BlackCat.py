import random

import Modules.global_value as g

from ...role import Role


class BlackCat(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.name = self.__class__.__name__
        self.team = "TeamWerewolf"
        self.fortune_result = "TeamVillager"
        self.description = "BlackCatDescription"
        self.win_condition = "MadmateWinCondition"

    async def executed_ability(self, game_id: int, player):
        """
        自分が処刑されたときに、他の生存しているプレイヤーを道連れにする。

        Parameters
        ----------
        game_id : int
            ゲームのID

        player : Player
            この役職のプレイヤー情報
        """

        game = g.werewolf_games.get(game_id)

        if game is not None:
            filtered_players = [p for p in game.alive_players if p.id != player.id]

            revenge_target = random.choice(filtered_players)
            await revenge_target.execute("Revenged")
            game.refresh_alive_players()
