import random

import discord

from Game.Werewolf import player, role


class RoleInfoView(discord.ui.View):
    def __init__(self, players: list, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.players = players

    @discord.ui.button(emoji="ℹ️", style=discord.ButtonStyle.gray)
    async def InfoButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        player_role = [p.role for p in self.players if interaction.user.id == p.id][0]
        embed = discord.Embed(
            title=player_role.name,
            color=discord.Color.green(),
        )
        embed.add_field(
            name="陣営",
            value=player_role.team,
            inline=False,
        )
        embed.add_field(
            name="勝利条件",
            value=player_role.win_condition,
            inline=False,
        )
        embed.add_field(
            name="説明",
            value=player_role.description,
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class WerewolfManager:
    def __init__(self, game: dict, client: discord.Client):
        self.id = game["id"]
        self.client = client
        self.game = game
        self.roles = self.game["roles"]
        self.available_roles = []
        self.message_id = self.game["message_id"]
        self.channel_id = self.game["channel_id"]
        self.players = []
        self.alive_players = []
        self.turns = 0

    async def game_start(self):
        players_ids = [self.game["host"]] + list(self.game["participants"])
        self.players = []
        for id in players_ids:
            p = player.Player(id, self.client)
            await p.initialize()
            self.players.append(p)
        self.alive_players = self.players

        self.available_roles = [
            role for role, count in self.game["roles"].items() for _ in range(count)
        ]
        while len(self.available_roles) < len(self.game["players"]):
            self.available_roles.append(role.Villager())
        random.shuffle(self.available_roles)

        for i, role in enumerate(self.available_roles):
            self.players[i].assign_role(role)

        role_info_view = RoleInfoView(self.players)
        for p in self.players:
            await p.message(f"あなたの役職は{p.role.name}です", view=role_info_view)
