from ..roles.villagers.villager import Villager
from ..player import Player

import random

class GameStartPhase:
    def __init__(self, game):
        self.game = game

    def run(self):
        pass

    def assign_roles(self):
        roles = self.select_assign_roles()
        player_ids = self.game.config.player_ids

        for player_id, role in zip(player_ids, roles):
            player = Player(id=player_id, game=self.game)
            self.game.players.append(player)

            player.assign_role(role)

    def select_assign_roles(self) -> list[Role]:
        roles = [r() for r, count in roles for _ in range(count)]
        player_ids = self.game.config.player_ids.copy()

        if len(roles) < len(player_ids):
            for _ in range(len(player_ids) - len(roles)):
                roles.append(Villager())

        random.shuffle(roles)
        return roles[: len(player_ids)]

        
