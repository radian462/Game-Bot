import discord

import Game.Werewolf.role as role
from Modules.logger import make_logger


class Player:
    def __init__(self, id, client):
        self.id = id
        self.client = client
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
        if not self.is_kill_protected:
            self.status = "Killed"
            self.is_alive = False

            self.logger.info(f"{self.id} was killed.")
        else:
            self.logger.info(f"{self.id} was blocked to kill.")

    def execute(self):
        self.status = "Executed"
        self.is_alive = False

        self.logger.info(f"{self.id} was executed.")
