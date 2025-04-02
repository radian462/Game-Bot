import logging
import os
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Final, Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

import Modules.global_value as g
from Modules.logger import make_logger
from Modules.translator import Translator
from Modules.Views.JoinView import JoinView
from Game.Werewolf import player, role

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

logger = make_logger("System")
g.werewolf_games = {}

NOT_HOST_MSG: Final = "あなたは募集者ではありません"
NOT_PLAYER_MSG: Final = "あなたは参加していません"
ALREADY_PLAYER_MSG: Final = "すでに参加しています"
LIMIT_PLAYER_MSG: Final = "人数制限に達しました"
HOST_JOIN_MSG: Final = "募集者は参加できません"
HOST_LEAVE_MSG: Final = "募集者は退出できません"
GAME_NOT_EXIST_MSG: Final = "ゲームが存在しません"

ERROR_TEMPLATE: Final = "エラーが発生しました\n"


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


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
@app_commands.describe(limit="人数制限")
@discord.app_commands.choices(
    limit=[discord.app_commands.Choice(name=i, value=i) for i in range(3, 16)]
)
@discord.app_commands.guild_only()
async def werewolf(interaction: discord.Interaction, limit: int = 10):
    logger.info(f"{interaction.user.id} created a game.")
    try:
        id = int(uuid.uuid4().int)

        view = JoinView(id=id, timeout=None)
        await interaction.response.send_message(view=view)
        message = await interaction.original_response()

        game = WerewolfGame(
            id=id,
            host_id=interaction.user.id,
            limit=limit,
            message=message,
            channel=interaction.channel,
            client=client,
            joinview=view,
            logger=make_logger("Game", id),
            translator=Translator("ja"),
        )
        g.werewolf_games[id] = game
        await update_recruiting_embed(id)
    except Exception as e:
        traceback.print_exc()
        await interaction.response.send_message(ERROR_TEMPLATE + str(e))


async def update_recruiting_embed(id: int, interaction: Optional[discord.Interaction] = None, show_view: bool = True) -> discord.Embed:
    game = g.werewolf_games[id]
    t = game.translator

    embed = discord.Embed(
        title=f"人狼ゲーム({len(game.participant_ids) + 1}/{game.limit}人)",
        description=f"募集者:<@!{game.host_id}>",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="参加者",
        value="\n".join([f"<@!{player}>" for player in game.participant_ids]) or "なし",
        inline=False,
    )
    embed.add_field(
        name="役職",
        value="\n".join(
            [
                f"{t.getstring(role.name)} {count}人"
                for role, count in game.roles.items()
                if count > 0
            ]
        )
        or "なし",
        inline=False,
    )

    view = game.joinview if show_view == True else None

    if interaction:
        await interaction.response.edit_message(embed=embed, view=view)
    else:
        channel = client.get_channel(game.channel.id)
        message = await channel.fetch_message(game.message.id)
        await message.edit(embed=embed, view=view)


load_dotenv()
client.run(os.getenv("DISCORD_TOKEN"))
