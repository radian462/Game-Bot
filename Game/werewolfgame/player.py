from enum import Enum

import discord
from roles.role import Role

from helpers.make_logger import make_logger
from .main import WerewolfGameManager


class Status(Enum):
    ALIVE = "Alive"
    KILLED = "Killed"
    EXECUTED = "Executed"
    CURSED = "Cursed"
    SYSTEMKILL = "SystemKill"


class Player:
    def __init__(self, game: WerewolfGameManager, id: int):
        self.id = id
        self.game = game
        self.client = game.client
        self.status: Status = Status.ALIVE
        self.role: Role | None = None
        self.is_kill_protected = False
        self.is_alive = True

        self.logger = make_logger("WerewolfGame.Player", id)

    async def initialize(self):
        self.member = await self.client.fetch_user(self.id)
        self.name = self.member.name

    async def message(
        self, content: str | None = None, embed: discord.Embed | None = None, view=None
    ):
        return await self.member.send(content, embed=embed, view=view)

    def assign_role(self, role: Role):
        self.role = role

    def kill(self):
        if not self.is_kill_protected and not self.role.is_kill_protected:
            self.status = Status.KILLED
            self.is_alive = False

            self.logger.info(f"{self.id} was killed.")
        else:
            self.logger.info(f"{self.id} was blocked to kill.")

    def system_kill(self, status: Status = Status.SYSTEMKILL):
        self.status = status
        self.is_alive = False

        self.logger.info(f"{self.id} was killed by system.")

    async def execute(self, status: Status = Status.EXECUTED):
        self.status = status
        self.is_alive = False

        self.logger.info(f"{self.id} was executed.")

        await self.role.executed_ability(game_id=self.game.id, player=self)
