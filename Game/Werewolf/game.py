import logging
from dataclasses import dataclass, field
from typing import Optional

import discord

import Modules.global_value as g
from Game.Werewolf import player, role
from Modules.translator import Translator
from Modules.Views.JoinView import JoinView


@dataclass
class WerewolfGame:
    # 以下ゲーム募集情報
    id: int
    host_id: int
    limit: int
    message: discord.Message
    channel: discord.TextChannel
    client: discord.Client
    joinview: JoinView
    logger: logging.LoggerAdapter
    translator: Translator

    is_started: bool = False

    # 以下ゲーム進行情報
    participant_ids: set[int] = field(default_factory=set)

    turns: int = 0

    players: list[player.Player] = field(default_factory=list)
    alive_players: list[player.Player] = field(default_factory=list)
    last_alive_players: list[player.Player] = field(default_factory=list)
    roles: dict[role.Role, int] = field(default_factory=dict)
    assigned_roles: list[role.Role] = field(default_factory=list)

    win_team: Optional[str] = None
    winner: list[player.Player] = field(default_factory=list)

    def refresh_alive_players(self):
        self.alive_players = [p for p in self.players if p.is_alive]

    async def update_recruiting_embed(
        self, interaction: Optional[discord.Interaction] = None, show_view: bool = True
    ) -> discord.Embed:
        t = self.translator

        embed = discord.Embed(
            title=f"人狼ゲーム({len(self.participant_ids) + 1}/{self.limit}人)",
            description=f"募集者:<@!{self.host_id}>",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="参加者",
            value="\n".join([f"<@!{player}>" for player in self.participant_ids])
            or "なし",
            inline=False,
        )
        embed.add_field(
            name="役職",
            value="\n".join(
                [
                    f"{t.getstring(role.name)} {count}人"
                    for role, count in self.roles.items()
                    if count > 0
                ]
            )
            or "なし",
            inline=False,
        )

        view = self.joinview if show_view == True else None

        if interaction:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            channel = self.client.get_channel(self.channel.id)
            message = await channel.fetch_message(self.message.id)
            await message.edit(embed=embed, view=view)

    def delete(self):
        del g.werewolf_games[self.id]
        self.logger.info(f"Game {self.id} deleted.")
