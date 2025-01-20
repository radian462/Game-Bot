import asyncio
import random
from collections import Counter

import discord
from discord.ui import Select, View

from Game.Werewolf import player, role
from make_logger import make_logger


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
    def __init__(self, choices: list[player.Player]) -> None:
        super().__init__()
        self.choices = choices
        self.result = None
        self.options = [
            discord.SelectOption(label=choice.name, value=choice.id)
            for choice in self.choices
        ]
        self.add_item(PlayerSelect(self.options))


class PlayerSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="プレイヤーを選択してください...", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        selected_user_id = int(self.values[0])
        self.view.result = selected_user_id

        selected_user_name = [
            op.label for op in self.options if selected_user_id == op.value
        ][0]

        await interaction.response.send_message(
            f"{selected_user_name} に投票しました。", ephemeral=True
        )
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
        self.players = []
        self.alive_players = []
        self.turns = 0

        self.logger = make_logger(str(self.id))

    async def game_start(self) -> None:
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

    async def night(self) -> None:
        embed = discord.Embed(title="人狼ゲーム", description="夜になりました。")
        channel = self.client.get_channel(self.channel_id)
        await channel.send(embed=embed)

        await self.night_ability_time()
        await self.kill_votes()

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
            view = PlayerChoiceView(self.alive_players)

            message = await player.message(embed=embed, view=view)
            await view.wait()

            return view.result

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

        target_players = [p for p in self.alive_players if p.id == chosen_mode][0]
        target_players.kill()

        for p in alive_werewolf_players:
            await p.message(f"{target_players.name}を襲撃します")

        self.logger.info(f"Werewolfs {target_players.id} tried to kill a target.")
