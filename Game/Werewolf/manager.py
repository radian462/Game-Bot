import random

import discord

from Game.Werewolf import player, role


class WerewolfManager:
    def __init__(self, game: dict, client: discord.Client):
        self.game = game
        self.id = game["id"]
        self.client = client

    async def game_start(self):
        players_ids = [self.game["host"]] + list(self.game["participants"])
        self.game["players"] = [player.Player(id) for id in players_ids]

        roles_list = [
            role for role, count in self.game["roles"].items() for _ in range(count)
        ]
        while len(roles_list) < len(self.game["players"]):
            roles_list.append(role.Villager())
        random.shuffle(roles_list)

        for i, role in enumerate(roles_list):
            self.game["players"][i].assign_role(role)

        for p in self.game["players"]:
            await p.message(f"あなたの役職は{p.role.name}です", self.client)
