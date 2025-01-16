import random

import discord

from Game.Werewolf import player, role


class RoleInfoView(discord.ui.View):
    def __init__(self, game: dict, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.game = game

    @discord.ui.button(emoji="ℹ️", style=discord.ButtonStyle.gray)
    async def InfoButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        player_list = self.game["players"]
        player_role = [p.role for p in player_list if interaction.user.id == p.id][0]
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
        
        role_info_view = RoleInfoView(self.game)
        for p in self.game["players"]:
            await p.message(f"あなたの役職は{p.role.name}です", self.client, view=role_info_view)
