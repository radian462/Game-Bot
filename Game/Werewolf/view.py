from typing import Literal

import discord
from discord.ui import Select, View

import Modules.global_value as g
from Game.Werewolf import player, role
from Modules.translator import Translator


class RoleInfoView(discord.ui.View):
    def __init__(self, players: list, game_id: int, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.players = players
        self.game = g.werewolf_games[game_id]
        self.logger = self.game.logger
        self.t = self.game.translator

    @discord.ui.button(emoji="ℹ️", style=discord.ButtonStyle.gray)
    async def InfoButton(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        player_role = [p.role for p in self.players if interaction.user.id == p.id][0]

        embed = discord.Embed(
            title=self.t.getstring(player_role.name),
            color=discord.Color.green(),
        )
        embed.add_field(
            name="陣営",
            value=self.t.getstring(player_role.team),
            inline=False,
        )
        embed.add_field(
            name="勝利条件",
            value=self.t.getstring(player_role.win_condition),
            inline=False,
        )
        embed.add_field(
            name="説明",
            value=self.t.getstring(player_role.description),
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class PlayerChoiceView(discord.ui.View):
    def __init__(
        self,
        choices: list[player.Player],
        process: Literal["Execute", "Ability"],
        game_id: int,
        allow_skip: bool = False,
    ) -> None:
        super().__init__()
        self.choices = choices
        self.votes: dict[int, int | None] = {}
        self.process = process
        self.options = [
            discord.SelectOption(label=choice.name, value=choice.id)
            for choice in self.choices
        ]

        self.game = g.werewolf_games[game_id]
        self.logger = self.game.logger
        self.t = self.game.translator

        if allow_skip:
            self.options.append(discord.SelectOption(label="スキップ", value="skip"))

        self.add_item(
            GenericSelect(self.options, self.choices, self.process, self.game.id)
        )


class GenericSelect(Select):
    def __init__(
        self,
        options: list[discord.SelectOption],
        players: list[player.Player],
        process: Literal["Execute", "Ability"],
        game_id: int,
    ):
        super().__init__(placeholder="プレイヤーを選択してください...", options=options)
        self.players = players
        self.votes: dict[int, int] = {}
        self.process = process
        self.game = g.werewolf_games[game_id]
        self.logger = self.game.logger
        self.t = self.game.translator
        self.view: PlayerChoiceView | None = None

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.values:
            self.logger.info(f"{interaction.user.id} selected {self.values[0]}")

            if self.process == "Execute":
                alive_player_ids = (p.id for p in self.players if p.is_alive)

                if self.view is None:
                    self.logger.error("self.view is None")
                    await interaction.response.send_message(
                        "内部エラーが発生しました。", ephemeral=True
                    )
                    return

                if interaction.user.id in self.view.votes:
                    await interaction.response.send_message(
                        "既に投票済みです", ephemeral=True
                    )
                    return
                if interaction.user.id not in alive_player_ids:
                    await interaction.response.send_message(
                        "生存しているプレイヤーだけが投票できます", ephemeral=True
                    )
                    return

                selected_user_id: int | None

                if self.values[0] == "skip":
                    selected_user_id = None
                    await interaction.response.send_message(
                        "スキップしました。", ephemeral=True
                    )
                else:
                    selected_user_id = int(self.values[0])
                    await interaction.response.send_message(
                        f"<@!{selected_user_id}> に投票しました。", ephemeral=True
                    )

                self.view.votes[interaction.user.id] = selected_user_id

                if len(self.view.votes) == len(self.players):
                    if interaction.message is not None:  # None チェックを追加
                        await interaction.message.edit(view=None)
                    self.view.stop()

            elif self.process == "Ability":
                if self.view is None:
                    self.logger.error("self.view is None")
                    await interaction.response.send_message(
                        "内部エラーが発生しました。", ephemeral=True
                    )
                    return

                selected_user_id: int | None = (
                    int(self.values[0]) if self.values[0] != "skip" else None
                )
                self.view.votes[interaction.user.id] = selected_user_id

                if selected_user_id is not None:
                    await interaction.response.send_message(
                        f"<@!{selected_user_id}> に投票しました。", ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "スキップしました。", ephemeral=True
                    )

                if interaction.message is not None:
                    await interaction.message.edit(view=None)
                self.view.stop()
        else:
            self.logger.warning(f"Not selected by {interaction.user.id}")
