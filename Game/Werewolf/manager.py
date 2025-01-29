import asyncio
import random
from collections import Counter
from typing import Literal

import discord
from discord.ui import Select, View

from Game.Werewolf import player, role
from Modules.logger import make_logger


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


class PlayerChoiceView(discord.ui.View):
    def __init__(
        self,
        choices: list[player.Player],
        process: Literal["Execute", "Ability"],
        allow_skip: bool = False,
    ) -> None:
        super().__init__()
        self.choices = choices
        self.votes = {}
        self.process = process
        self.options = [
            discord.SelectOption(label=choice.name, value=choice.id)
            for choice in self.choices
        ]

        if allow_skip:
            self.options.append(discord.SelectOption(label="スキップ", value="skip"))

        self.add_item(GenericSelect(self.options, self.choices, self.process))


class GenericSelect(Select):
    def __init__(
        self,
        options: list[discord.SelectOption],
        players: list[player.Player],
        process: Literal["Execute", "Ability"],
    ):
        super().__init__(placeholder="プレイヤーを選択してください...", options=options)
        self.players = players
        self.votes = {}
        self.process = process

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.process == "Execute":
            alive_player_ids = (p.id for p in self.players if p.is_alive)

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
                await interaction.message.edit(view=None)
                self.view.stop()

        elif self.process == "Ability":
            selected_user_id = int(self.values[0]) if self.values[0] != "skip" else None
            self.view.votes[interaction.user.id] = selected_user_id

            if selected_user_id is not None:
                await interaction.response.send_message(
                    f"<@!{selected_user_id}> に投票しました。", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "スキップしました。", ephemeral=True
                )

            await interaction.message.edit(view=None)
            self.view.stop()


class WerewolfManager:
    def __init__(self, game: dict, client: discord.Client):
        self.id = game["id"]
        self.client = client
        self.game = game
        self.roles = self.game["roles"]
        self.available_roles = []
        self.message_id = self.game["message_id"]
        self.channel_id = self.game["channel_id"]
        self.channel = self.client.get_channel(self.channel_id)
        self.players = []
        self.alive_players = []
        self.winner = []
        self.win_team = []
        self.turns = 0

        self.logger = make_logger("Werewolf", self.id)

    def refresh_alive_players(self):
        self.alive_players = [p for p in self.players if p.is_alive]

    async def game_start(self) -> None:
        self.logger.info("Game has started.")
        
        players_ids = [self.game["host"]] + list(self.game["participants"])
        self.players = []
        for id in players_ids:
            p = player.Player(id, self.client)
            await p.initialize()
            self.players.append(p)
        self.alive_players = self.players
        self.last_alive_players = self.players

        self.available_roles = [
            r for r, count in self.game["roles"].items() for _ in range(count)
        ]

        while len(self.available_roles) < len(self.players):
            self.available_roles.append(role.Villager())

        random.shuffle(self.available_roles)

        for i, r in enumerate(self.available_roles):
            self.players[i].assign_role(r)
            self.logger.info(f"{self.players[i].id} has been assigned {r.name}")

        role_info_view = RoleInfoView(self.players)
        for p in self.players:
            await p.message(f"あなたの役職は{p.role.name}です", view=role_info_view)

    # 以下夜の処理
    async def night(self) -> None:
        embed = discord.Embed(
            title="人狼ゲーム",
            description=f"夜になりました。プレイヤーは<@!{self.client.application_id}>のDMに移動してください。",
        )
        await self.channel.send(embed=embed)

        await self.night_ability_time()

        if self.turns != 0:
            await self.kill_votes()

        for p in self.last_alive_players:
            await p.message(f"<#{self.channel.id}>に戻ってください")

        self.turns += 1

    async def night_ability_time(self) -> None:
        tasks = []
        for p in self.alive_players:
            tasks.append(p.role.night_ability())

        await asyncio.gather(*tasks)

    async def kill_votes(self) -> None:
        async def wait_for_vote(player: player.Player) -> int:
            embed = discord.Embed(
                title="キル投票", description="襲撃対象を選んでください"
            )
            view = PlayerChoiceView(
                choices=self.alive_players, process="Ability", allow_skip=False
            )

            message = await player.message(embed=embed, view=view)
            await view.wait()

            return list(view.votes.values())[0]

        alive_werewolf_players = [p for p in self.alive_players if p.role.is_werewolf]

        tasks = []
        for p in alive_werewolf_players:
            tasks.append(wait_for_vote(p))

        results = await asyncio.gather(*tasks)

        counter = Counter(results)
        modes = [
            key for key, count in counter.items() if count == max(counter.values())
        ]

        if modes:
            chosen_mode = random.choice(modes)

        target_players = [p for p in self.last_alive_players if p.id == chosen_mode][0]
        target_players.kill()

        for p in alive_werewolf_players:
            await p.message(f"<@!{target_players.id}>を襲撃します")

        self.refresh_alive_players()
        self.logger.info(f"Werewolfs {target_players.id} tried to kill a target.")

    # 以下昼の処理
    async def day(self):
        today_killed_players = [
            player
            for player in self.last_alive_players
            if player not in self.alive_players
        ]

        embed = discord.Embed(
            title="人狼ゲーム",
            description="朝になりました。議論を行い、誰を追放するか決めてください。",
            color=0xFFFACD,
        )
        embed.add_field(
            name="本日の死亡者",
            value="\n".join([f"<@!{player.id}>" for player in today_killed_players])
            or "なし",
            inline=False,
        )
        await self.channel.send(embed=embed)

        await self.execute_vote()

    async def execute_vote(self) -> None:
        embed = discord.Embed(title="処刑投票", description="処刑対象を選んでください")
        view = PlayerChoiceView(
            choices=self.alive_players, process="Execute", allow_skip=True
        )

        message = await self.channel.send(embed=embed, view=view)
        await view.wait()

        filtered_votes = [v for v in view.votes.values()]
        counter = Counter(filtered_votes)

        if not counter:
            execute_target = None
        elif counter.get(None, 0) * 2 >= len(view.votes):
            execute_target = None
        else:
            most_common = counter.most_common()
            max_count = most_common[0][1]
            result_candidates = [k for k, v in most_common if v == max_count]
            execute_target = (
                result_candidates[0] if len(result_candidates) == 1 else None
            )

        if execute_target is None:
            await self.channel.send(f"誰も処刑されませんでした。")
            self.logger.info(f"Nobody was executed.")
        else:
            target_player = [p for p in self.alive_players if p.id == execute_target][0]
            target_player.execute()
            self.refresh_alive_players()
            await self.channel.send(f"<@!{target_player.id}> が処刑されました。")
            self.logger.info(f"{target_player.id} was executed.")

        self.last_alive_players = self.alive_players

    # 以下ゲーム終了処理
    def win_check(self) -> bool:
        if (
            len([p for p in self.alive_players if p.role.is_werewolf])
            >= len(self.alive_players) / 2
        ):
            self.winner = [p for p in self.players if p.role.team == "人狼"]
            self.win_team = "人狼"
            return True
        elif len([p for p in self.alive_players if p.role.is_werewolf]) == 0:
            self.winner = [p for p in self.players if p.role.team == "村人"]
            self.win_team = "村人"
            return True
        else:
            return False

    async def game_end(self) -> None:
        embed = discord.Embed(
            title="人狼ゲーム",
            description=f"{self.win_team}勝利",
            color=0xFFD700,
        )
        embed.add_field(
            name="勝者",
            value="\n".join([f"<@!{player.id}>" for player in self.winner]),
            inline=False,
        )
        await self.channel.send(embed=embed)

        self.logger.info(f"Game has ended. Winners: {self.winner}")
