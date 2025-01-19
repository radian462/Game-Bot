import discord

import Game.Werewolf.role as role


class Player:
    def __init__(self, id, client):
        self.id = id
        self.client = client
        self.member = None
        self.status = "Alive"
        self.is_alive = True
        self.role = None
        self.is_kill_protected = False

    async def initialize(self):
        self.member = await self.client.fetch_user(self.id)
        self.name = self.member.name

    async def message(self, content: str, view=None):
        await self.member.send(content, view=view)

    def assign_role(self, role: role.Role):
        self.role = role

    def kill(self):
        if not self.is_kill_protected:
            self.status = "Killed"
            self.is_alive = False
