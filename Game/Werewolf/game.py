import logging
from dataclasses import dataclass, field

import discord

import Modules.global_value as g
from Game.Werewolf import main, player, role
from Modules.translator import Translator
from Modules.Views.JoinView import JoinView


@dataclass
class WerewolfGame:
    """
    ゲームの情報を保持するクラス。

    Attributes
    ----------
    id : int
        ゲームのID
    host_id : int
        ホストのID
    limit : int
        参加人数の上限
    message : discord.Message
        募集メッセージ
    channel : discord.TextChannel
        募集メッセージのチャンネル
    client : discord.Client
        Discordクライアント
    joinview : JoinView
        募集用のボタン
    logger : logging.LoggerAdapter
        ロガー
    translator : Translator
        翻訳クラス
    is_started : bool
        ゲームが開始されたかどうか
    participant_ids : set[int]
        参加者のIDのセット
    turns : int
        ターン数
    players : list[player.Player]
        プレイヤーのリスト
    alive_players : list[player.Player]
        生存しているプレイヤーのリスト
    """

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
    is_ended: bool = False

    # 以下ゲーム進行情報
    participant_ids: set[int] = field(default_factory=set)

    turns: int = 0
    last_night_turn_time: float = 0.0

    players: list[player.Player] = field(default_factory=list)
    alive_players: list[player.Player] = field(default_factory=list)
    last_alive_players: list[player.Player] = field(default_factory=list)
    roles: dict[role.Role, int] = field(default_factory=dict)
    assigned_roles: list[role.Role] = field(default_factory=list)
    last_executed_player: player.Player | None = None

    win_team: str | None = None
    winner: list[player.Player] = field(default_factory=list)

    def refresh_alive_players(self):
        """
        生存しているプレイヤーを更新する。
        """

        self.alive_players = [p for p in self.players if p.is_alive]

    async def update_recruiting_embed(
        self, interaction: discord.Interaction | None = None, show_view: bool = True
    ) -> None:
        """
        募集用のEmbedを更新する。

        Parameters
        ----------
        interaction : discord.Interaction | None
            インタラクションオブジェクト
        show_view : bool
            募集用のボタンを表示するかどうか
        """

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

        view = self.joinview if show_view else None

        if interaction:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            channel = self.client.get_channel(self.channel.id)
            if isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(self.message.id)
                await message.edit(embed=embed, view=view)
            else:
                self.logger.warning(
                    "channel is not a TextChannel. Cannot fetch message."
                )

    def delete(self):
        """
        ゲームを削除する。
        """

        del g.werewolf_games[self.id]
        self.logger.info(f"Game {self.id} deleted.")

    async def start(self):
        """
        ゲームを開始する。
        """

        self.is_started = True
        await main.main(self.id)
        self.logger.info(f"Game {self.id} started.")
