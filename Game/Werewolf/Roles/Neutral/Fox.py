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
        player.system_kill("Cursed")
