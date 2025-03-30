import asyncio
import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import discord

import Modules.global_value as g
from Game.Werewolf import player, role
from Game.Werewolf.view import PlayerChoiceView, RoleInfoView
from Modules.logger import make_logger

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

    channel: Optional[discord.TextChannel] = None
    client: Optional[discord.Client] = None

    win_team: Optional[str] = None
    winner: list[player.Player] = field(default_factory=list)

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

        self.game = Game(
            id=game["id"], roles=game["roles"], channel=self.channel, client=client
        )
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

    async def night(self) -> None:
        await NightManager(self.id).main()

    async def day(self) -> None:
        await DayManager(self.id).main()

    def win_check(self) -> None:
        return EndManager(self.id).win_check()

    async def game_end(self) -> None:
        await EndManager(self.id).main()


class NightManager:
    def __init__(self, id: Optional[int] = None) -> None:
        self.id = id
        self.game = g.games.get(id)
        self.logger = make_logger("NightManager", id)

        self.alive_werewolf_players: list[player.Player] = []
        self.alive_not_werewolf_players: list[player.Player] = []

    async def main(self) -> None:
        await self._announce_night_start()
        await self.night_ability_time()
        await self.kill_time()

        self.game.refresh_alive_players()

        self.game.turns += 1
        await self._announce_night_end()

    async def _announce_night_start(self) -> None:
        embed = discord.Embed(
            title="人狼ゲーム",
            description=f"夜になりました。プレイヤーは<@!{self.game.client.application_id}>のDMに移動してください。",
        )
        await self.game.channel.send(embed=embed)

    async def _announce_night_end(self) -> None:
        for p in self.game.last_alive_players:
            await p.message(f"<#{self.game.channel.id}>に戻ってください")

    async def _announce_kill(self, target_player) -> None:
        for p in self.alive_werewolf_players:
            await p.message(f"<@!{target_player.id}>を襲撃します")

    async def night_ability_time(self) -> None:
        tasks = [
            p.role.night_ability(game_id=self.id, player=p)
            for p in self.game.alive_players
        ]

        await asyncio.gather(*tasks)

    async def kill_time(self) -> None:
        if self.game.turns != 0:
            results = await self.kill_votes()
            target_id = self._decide_kill_target(results)
            target_player = next(
                p for p in self.game.last_alive_players if p.id == target_id
            )
            await self._announce_kill(target_player)
            target_player.kill()
            self.logger.info(f"Werewolfs {target_player.id} tried to kill a target.")

    def _decide_kill_target(self, results: list[int]) -> player.Player:
        counter = Counter(results)
        max_count = max(counter.values(), default=0)
        modes = [key for key, count in counter.items() if count == max_count]

        return random.choice(modes)

    async def kill_votes(self) -> list[int]:
        async def wait_for_vote(player: player.Player) -> int:
            embed = discord.Embed(
                title="キル投票", description="襲撃対象を選んでください"
            )
            view = PlayerChoiceView(
                choices=self.alive_not_werewolf_players,
                process="Ability",
                allow_skip=False,
                game_id=self.id,
            )

            await player.message(embed=embed, view=view)
            await view.wait()

            return list(view.votes.values())[0]

        self.alive_werewolf_players = [
            p for p in self.game.alive_players if p.role.is_werewolf
        ]
        self.alive_not_werewolf_players = [
            p for p in self.game.alive_players if not p.role.is_werewolf
        ]

        tasks = []
        for p in self.alive_werewolf_players:
            tasks.append(wait_for_vote(p))

        results = await asyncio.gather(*tasks)
        return results


class DayManager:
    def __init__(self, id: Optional[int] = None) -> None:
        self.id = id
        self.game = g.games.get(id)
        self.logger = make_logger("DayManager", id)

        self.today_killed_players: list[player.Player] = []

    async def main(self):
        self.today_killed_players = [
            player
            for player in self.game.last_alive_players
            if player not in self.game.alive_players
        ]

        await self._announce_day_start()
        await self.execute_vote()

    async def _announce_day_start(self) -> None:
        embed = discord.Embed(
            title="人狼ゲーム",
            description="朝になりました。議論を行い、誰を追放するか決めてください。",
            color=0xFFFACD,
        )
        embed.add_field(
            name="本日の死亡者",
            value="\n".join(
                [f"<@!{player.id}>" for player in self.today_killed_players]
            )
            or "なし",
            inline=False,
        )
        await self.game.channel.send(embed=embed)

    def _decide_execute_target(self, results: list[int]) -> int | None:
        counter = Counter(results)

        if not counter:
            execute_target = None
        elif counter.get(None, 0) * 2 >= len(results):
            execute_target = None
        else:
            most_common = counter.most_common()
            max_count = most_common[0][1]
            result_candidates = [k for k, v in most_common if v == max_count]
            execute_target = (
                result_candidates[0] if len(result_candidates) == 1 else None
            )

        return execute_target

    async def execute_vote(self) -> None:
        embed = discord.Embed(title="処刑投票", description="処刑対象を選んでください")
        view = PlayerChoiceView(
            choices=self.game.alive_players,
            process="Execute",
            allow_skip=True,
            game_id=self.id,
        )

        await self.game.channel.send(embed=embed, view=view)
        await view.wait()

        filtered_votes = [v for v in view.votes.values()]
        execute_id = self._decide_execute_target(filtered_votes)

        if execute_id is None:
            await self.game.channel.send(f"誰も処刑されませんでした。")
            self.logger.info(f"Nobody was executed.")
        else:
            target_player = [p for p in self.game.alive_players if p.id == execute_id][
                0
            ]
            target_player.execute()
            self.game.refresh_alive_players()
            await self.game.channel.send(f"<@!{target_player.id}> が処刑されました。")
            self.logger.info(f"{target_player.id} was executed.")

        self.game.last_alive_players = self.game.alive_players


class EndManager:
    def __init__(self, id: Optional[int] = None) -> None:
        self.id = id
        self.game = g.games.get(id)
        self.logger = make_logger("EndManager", id)
        self.t = g.translators.get(id)

    async def main(self) -> None:
        await self._send_result()
        del g.games[self.id]

    def win_check(self) -> bool:
        """
        人狼人数が生存者の半数を上回った場合、人狼勝利
        人狼が一人もいなくなった場合、村人勝利
        それ以外の場合、ゲーム続行
        """
        if self._is_werewolf_win():
            self.game.win_team = "TeamWerewolf"
        elif self._is_villager_win():
            self.game.win_team = "TeamVillager"

        if self.game.win_team:
            self.game.winner = [
                p for p in self.game.players if p.role.team == self.game.win_team
            ]
            return True
        else:
            return False

    def _is_werewolf_win(self) -> bool:
        if (
            len([p for p in self.game.alive_players if p.role.is_werewolf])
            >= len(self.game.alive_players) / 2
        ):
            return True
        else:
            return False

    def _is_villager_win(self) -> bool:
        if len([p for p in self.game.alive_players if p.role.is_werewolf]) == 0:
            return True
        else:
            return False

    async def _send_result(self) -> None:
        embed = discord.Embed(
            title="人狼ゲーム",
            description=f"{self.t.getstring(self.game.win_team)}勝利",
            color=0xFFD700,
        )
        embed.add_field(
            name="勝者",
            value="\n".join([f"<@!{player.id}>" for player in self.game.winner]),
            inline=False,
        )
        await self.game.channel.send(embed=embed)

        self.logger.info(f"Game has ended. Winners: {self.game.winner}")

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
        await self.game.channel.send(embed=result_embed)
