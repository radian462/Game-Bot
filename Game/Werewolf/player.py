import discord

import Game.Werewolf.role as role


class Player:
    def __init__(self, id: int | str):
        self.id = id
        self.status = "Alive"
        self.is_alive = True
        self.role = None
        self.is_kill_protected = False

    async def message(self, content: str, client, view=None):
        member = await client.fetch_user(self.id)
        await member.send(content,view=view)

    def assign_role(self, role: role.Role):
        self.role = role

    def kill(self):
        if not self.is_kill_protected:
            self.status = "Killed"
            self.is_alive = False
