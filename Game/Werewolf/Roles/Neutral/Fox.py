import discord

import Modules.global_value as g

from ...player import Player
from ...role import Role


class Fox(Role):
    def __init__(self):
        super().__init__()
        self.is_neutral = True

        self.initialize_role()

        self.is_kill_protected = True

    async def seer_ability(self, game_id: int, player: Player):
        """
        占い師に占われたときこのプレイヤーを呪殺する。

        Parameters
        ----------
        game_id : int
            ゲームのID
        player : Player
            この役職のプレイヤー情報
        """
        player.system_kill("Cursed")
