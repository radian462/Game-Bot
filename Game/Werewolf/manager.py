import asyncio
from dataclasses import dataclass, field
import random
from collections import Counter

import discord

import Modules.global_value as g
from Game.Werewolf import player, role
from Game.Werewolf.view import PlayerChoiceView, RoleInfoView

g.games = {}


@dataclass
class Game:
    id: int = 0
    turns: int = 0

    players: list[player.Player] = field(default_factory=list)
    alive_players: list[player.Player] = field(default_factory=list)
    last_alive_players: list[player.Player] = field(default_factory=list)
    roles: dict[role.Role, int] = field(default_factory=dict)
    assigned_roles: list[role.Role] = field(default_factory=list)

    def refresh_alive_players(self):
        self.alive_players = [p for p in self.players if p.is_alive]


class WerewolfManager:
    def __init__(self, game: dict, client: discord.Client):
        self.id = game["id"]
        self.host = game["host"]
        self.participants = game["participants"]
        self.client = client
        self.message_id = game["message_id"]
        self.channel_id = game["channel_id"]
        self.channel = self.client.get_channel(self.channel_id)

        self.winner = []
        self.win_team = []

        self.lang = "ja"
        self.t = g.translators[self.id]
        self.logger = g.loggers[self.id]

        self.game = Game(id=game["id"], roles=game["roles"])
        g.games[game["id"]] = self.game

    async def _create_player_instances(self) -> None:
        players_ids = [self.host] + list(self.participants)

        for id in players_ids:
            p = player.Player(id, self.client)
            await p.initialize()
            self.game.players.append(p)

        self.game.refresh_alive_players()
        self.game.last_alive_players = self.game.players


    def _assign_roles(self) -> None:
        self.game.assigned_roles = [
            r for r, count in self.game.roles.items() for _ in range(count)
        ]

        while len(self.game.assigned_roles) < len(self.game.players):
            self.game.assigned_roles.append(role.Villager())

        random.shuffle(self.game.assigned_roles)

        for i, r in enumerate(self.game.assigned_roles):
            self.game.players[i].assign_role(r)
            self.logger.info(f"{self.game.players[i].id} has been assigned {r.name}")

    async def _notify_roles(self) -> None:
        role_info_view = RoleInfoView(self.game.players, self.id)
        for p in self.game.players:
            await p.message(
                f"あなたの役職は{self.t.getstring(p.role.name)}です",
                view=role_info_view,
            )

    async def game_start(self) -> None:
        self.logger.info("Game has started.")
        await self._create_player_instances()

        self._assign_roles()
        await self._notify_roles()

    # 以下夜の処理
    async def night(self) -> None:
        embed = discord.Embed(
            title="人狼ゲーム",
            description=f"夜になりました。プレイヤーは<@!{self.client.application_id}>のDMに移動してください。",
        )
        await self.channel.send(embed=embed)

        await self.night_ability_time()

        if self.game.turns != 0:
            await self.kill_votes()

        for p in self.game.last_alive_players:
            await p.message(f"<#{self.channel.id}>に戻ってください")

        self.game.turns += 1

    async def night_ability_time(self) -> None:
        tasks = []
        for p in self.game.alive_players:
            tasks.append(p.role.night_ability())

        await asyncio.gather(*tasks)

    async def kill_votes(self) -> None:
        async def wait_for_vote(player: player.Player) -> int:
            embed = discord.Embed(
                title="キル投票", description="襲撃対象を選んでください"
            )
            view = PlayerChoiceView(
                choices=alive_not_werewolf_players,
                process="Ability",
                allow_skip=False,
                game_id=self.id,
            )

            await player.message(embed=embed, view=view)
            await view.wait()

            return list(view.votes.values())[0]

        alive_werewolf_players = [p for p in self.game.alive_players if p.role.is_werewolf]
        alive_not_werewolf_players = [p for p in self.game.alive_players if not p.role.is_werewolf]

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

        target_players = [p for p in self.game.last_alive_players if p.id == chosen_mode][0]

        target_players.kill()

        for p in alive_werewolf_players:
            await p.message(f"<@!{target_players.id}>を襲撃します")

        self.game.refresh_alive_players()
        self.logger.info(f"Werewolfs {target_players.id} tried to kill a target.")

    # 以下昼の処理
    async def day(self):
        today_killed_players = [
            player
            for player in self.game.last_alive_players
            if player not in self.game.alive_players
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
            choices=self.game.alive_players,
            process="Execute",
            allow_skip=True,
            game_id=self.id,
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
            target_player = [p for p in self.game.alive_players if p.id == execute_target][0]
            target_player.execute()
            self.game.refresh_alive_players()
            await self.channel.send(f"<@!{target_player.id}> が処刑されました。")
            self.logger.info(f"{target_player.id} was executed.")

        self.last_alive_players = self.game.alive_players

    # 以下ゲーム終了処理
    def win_check(self) -> bool:
        if (
            len([p for p in self.game.alive_players if p.role.is_werewolf])
            >= len(self.game.alive_players) / 2
        ):
            self.winner = [p for p in self.game.players if p.role.team == "TeamWerewolf"]
            self.win_team = "TeamWerewolf"
            return True
        elif len([p for p in self.game.alive_players if p.role.is_werewolf]) == 0:
            self.winner = [p for p in self.game.players if p.role.team == "TeamVillager"]
            self.win_team = "TeamVillager"
            return True
        else:
            return False

    async def game_end(self) -> None:
        embed = discord.Embed(
            title="人狼ゲーム",
            description=f"{self.t.getstring(self.win_team)}勝利",
            color=0xFFD700,
        )
        embed.add_field(
            name="勝者",
            value="\n".join([f"<@!{player.id}>" for player in self.winner]),
            inline=False,
        )
        await self.channel.send(embed=embed)

        self.logger.info(f"Game has ended. Winners: {self.winner}")

        result_embed = discord.Embed(
            title="人狼ゲーム",
            color=0xFFD700,
        )
        result_embed.add_field(
            name="最終結果",
            value="\n".join(
                f"<@!{p.id}> {self.t.getstring(p.status)} - {self.t.getstring(p.role.name)}"
                for p in self.game.players
            ),
            inline=False,
        )
        await self.channel.send(embed=result_embed)
