import discord

import Game.Werewolf.role as role
import Modules.global_value as g
from Modules.logger import make_logger


class Player:
    def __init__(self, id, game_id):
        self.id = id
        self.game = g.werewolf_games.get(game_id)
        self.client = self.game.client
        self.member = None
        self.status = "Alive"
        self.is_alive = True
        self.role = None
        self.is_kill_protected = False

        self.logger = make_logger("Werewolf.Player", id)

    async def initialize(self):
        self.member = await self.client.fetch_user(self.id)
        self.name = self.member.name

    async def message(
        self, content: str | None = None, embed: discord.Embed | None = None, view=None
    ):
        return await self.member.send(content, embed=embed, view=view)

    def assign_role(self, role: role.Role):
        self.role = role

    def kill(self):
        if not self.is_kill_protected and not self.role.is_kill_protected:
            self.status = "Killed"
            self.is_alive = False

            self.logger.info(f"{self.id} was killed.")
        else:
            self.logger.info(f"{self.id} was blocked to kill.")

    def system_kill(self, status: str):
        self.status = status
        self.is_alive = False

        self.logger.info(f"{self.id} was killed by system.")

    async def execute(self, status: str = "Executed"):
        self.status = status
        self.is_alive = False

        self.logger.info(f"{self.id} was executed.")

        await self.role.executed_ability(game_id=self.game.id, player=self)
