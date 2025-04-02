import logging
from dataclasses import dataclass, field
from typing import Optional

import discord

import Modules.global_value as g
from Game.Werewolf import player, role
from Modules.translator import Translator
from Modules.Views.JoinView import JoinView

g.werewolf_games = {}

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
