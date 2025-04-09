import asyncio
import random
from collections import Counter
from dataclasses import dataclass, field

import discord

import Modules.global_value as g
from Game.Werewolf import player, role
from Game.Werewolf.view import PlayerChoiceView, RoleInfoView
from Modules.logger import make_logger


class WerewolfManager:
    """
    ゲーム全体の管理クラス。
    プレイヤーの生成、役職の割り当て、各フェーズの開始などを管理する。

    parameters
    ----------
    id: int
        ゲームID
    """

    def __init__(self, id: int) -> None:
        # ゲームIDに基づいて該当のゲームインスタンスを取得
        self.id = id
        self.game = g.werewolf_games.get(id)
        if self.game is not None:
            self.client = self.game.client
            self.logger = make_logger("WerewolfManager", id)
            self.t = self.game.translator

    async def _create_player_instances(self) -> None:
        """
        ゲームに参加する各プレイヤーのPlayerクラスインスタンスを生成する。
        """
        if self.game is not None:
            players_ids = [self.game.host_id] + list(self.game.participant_ids)

            # 各プレイヤーのインスタンスを生成して初期化後、ゲーム内プレイヤーリストに追加する
            for id in players_ids:
                p = player.Player(id, self.id)
                await p.initialize()
                self.game.players.append(p)

            # 現在生存しているプレイヤーのリストを更新
            self.game.refresh_alive_players()
            self.game.last_alive_players = self.game.players

    def _assign_roles(self) -> None:
        """
        ゲームに参加するプレイヤーに対して、役職を割り当てる。
        まず用意された役職リストを展開し、足りなければ村人(Villager)を補充する。
        その後、シャッフルして順番に割り当てる。
        """
        # 各役職の数に応じてリストに展開
        if self.game is not None:
            self.game.assigned_roles = [
                r for r, count in self.game.roles.items() for _ in range(count)
            ]

            # プレイヤー数に足りなければ、村人役を追加する
            while len(self.game.assigned_roles) < len(self.game.players):
                self.game.assigned_roles.append(role.Villager())

            # 役職リストをシャッフルしてランダムな割り当てにする
            random.shuffle(self.game.assigned_roles)

            # もし余分な役職があればプレイヤー数に合わせてトリムする
            if len(self.game.assigned_roles) > len(self.game.players):
                self.game.assigned_roles = self.game.assigned_roles[
                    : len(self.game.players)
                ]

            # 各プレイヤーに役職を順次割り当て、ログにも記録する
            for i, r in enumerate(self.game.assigned_roles):
                self.game.players[i].assign_role(r)
                self.logger.info(f"{self.game.players[i].id} has been assigned {r.name}")

    async def _notify_roles(self) -> None:
        """
        各プレイヤーに自分の役職情報を通知する。
        通知にはRoleInfoViewを利用してインタラクティブなメッセージを送信する。
        """
        if self.game is not None:
            role_info_view = RoleInfoView(self.game.players, self.id)
            for p in self.game.players:
                await p.message(
                    f"あなたの役職は{self.t.getstring(p.role.name)}です",
                    view=role_info_view,
                )

    async def game_start(self) -> None:
        """
        ゲーム開始時の処理をまとめて実行する。
        プレイヤーのインスタンス生成、役職の割り当て、通知を行う。
        """
        self.logger.info("Game has started.")
        await self._create_player_instances()
        self._assign_roles()
        await self._notify_roles()

    async def night(self) -> None:
        """
        夜のフェーズを開始する。
        NightManagerクラスのmain関数を呼び出す。
        """
        await NightManager(self.id).main()

    async def day(self) -> None:
        """
        昼のフェーズを開始する。
        DayManagerクラスのmain関数を呼び出す。
        """
        await DayManager(self.id).main()

    async def win_check(self) -> None:
        """
        ゲーム終了条件を確認する。
        """
        if self.game is not None:
            await EndManager(self.id).win_check()
        
    async def execute_game_end(self) -> None:
        """
        ゲーム終了時の処理。
        """
        await EndManager(self.id).execute_game_end()


class NightManager:
    """
    夜のフェーズを管理するクラス。
    夜間における各プレイヤーのアクションや襲撃処理などを行う。

    parameters
    ----------
    id: int | None
        ゲームID。Noneの場合は新規ゲームとして扱う。
    """

    def __init__(self, id: int) -> None:
        self.id = id
        self.game = g.werewolf_games.get(id)
        self.logger = make_logger("NightManager", id)

        # 生存している人狼側と人狼でないプレイヤーのリストを保持
        self.alive_werewolf_players: list[player.Player] = []
        self.alive_not_werewolf_players: list[player.Player] = []

    async def main(self) -> None:
        """
        夜の処理のメインルーチン。
        夜の開始通知、各プレイヤーの夜のアクション実行、襲撃処理、夜の終了通知を順次実施する。
        """
        await self._announce_night_start()
        await self.night_ability_time()
        await self.kill_time()

        if self.game is not None:
            # 襲撃処理後、現在の生存プレイヤーリストを更新
            self.game.refresh_alive_players()

            # ターン数をインクリメントし、夜終了の通知を送信
            self.game.turns += 1
            await self._announce_night_end()

    async def _announce_night_start(self) -> None:
        """
        夜の開始を全体に通知する。
        チャンネルに埋め込みメッセージを送信する。
        """
        if self.game is not None:
            embed = discord.Embed(
                title="人狼ゲーム",
                description=f"夜になりました。プレイヤーは<@!{self.game.client.application_id}>のDMに移動してください。",
            )
            await self.game.channel.send(embed=embed)

    async def _announce_night_end(self) -> None:
        """
        夜の終了後、プレイヤーにチャンネルに戻るよう促す通知を送る。
        """
        if self.game is not None:
            for p in self.game.last_alive_players:
                await p.message(f"<#{self.game.channel.id}>に戻ってください")

    async def _announce_kill(self, target_player) -> None:
        """
        襲撃対象のプレイヤーが決定した際に、人狼側に通知する。
        """
        for p in self.alive_werewolf_players:
            await p.message(f"<@!{target_player.id}>を襲撃します")

    async def night_ability_time(self) -> None:
        """
        夜間の各プレイヤーの特殊能力（役職固有のアクション）を実行する。
        """
        if self.game is not None:
            tasks = [
                p.role.night_ability(game_id=self.id, player=p)
                for p in self.game.alive_players
            ]
            await asyncio.gather(*tasks)

    async def kill_time(self) -> None:
        """
        人狼の襲撃処理を行う。
        前ターン以降の場合のみ、投票に基づいた襲撃対象を決定し、対象プレイヤーを襲撃する。
        """
        if self.game is not None:
            if self.game.turns != 0:
                results = await self.kill_votes()
                target_id = self._decide_kill_target(results)
                target_player = next(
                    p for p in self.game.last_alive_players if p.id == target_id
                )
                await self._announce_kill(target_player)
                target_player.kill()
                self.logger.info(f"Werewolfs {target_player.id} tried to kill a target.")

    def _decide_kill_target(self, results: list[int]) -> int | None:
        """
        複数の人狼からの投票結果から、襲撃対象を決定する。
        最も多く票を得たプレイヤー（複数候補の場合はランダムに選択）を返す。
        """
        counter = Counter(results)
        max_count = max(counter.values(), default=0)
        modes = [key for key, count in counter.items() if count == max_count]

        return random.choice(modes) if modes else None

    async def kill_votes(self) -> list[int]:
        """
        人狼側プレイヤーからの襲撃対象投票を実施する。
        各プレイヤーに対してDMで投票を促し、その結果をリストとして返す。
        """

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

            # プレイヤーへメッセージと投票用ビューを送信
            await player.message(embed=embed, view=view)
            await view.wait()

            # 投票結果を取得（今回は単一票を前提とする）
            return list(view.votes.values())[0]

        # 現在生存している人狼プレイヤーと、人狼でないプレイヤーをリストアップする
        if self.game is not None:
            self.alive_werewolf_players = [
                p for p in self.game.alive_players if p.role.is_werewolf
            ]
            self.alive_not_werewolf_players = [
                p for p in self.game.alive_players if not p.role.is_werewolf
            ]

        tasks = []
        # 各人狼プレイヤーに対して非同期に投票待ち処理を実行
        for p in self.alive_werewolf_players:
            tasks.append(wait_for_vote(p))

        results = await asyncio.gather(*tasks)
        return results


class DayManager:
    """
    昼のフェーズを管理するクラス。
    議論後の処刑投票、結果の発表、生存状態のリセットなどを行う。

    parameters
    ----------
    id: int | None
        ゲームID。Noneの場合は新規ゲームとして扱う。
    """

    def __init__(self, id: int) -> None:
        self.id = id
        self.game = g.werewolf_games.get(id)
        self.logger = make_logger("DayManager", id)

        # 当日の夜に死亡したプレイヤーのリスト
        self.today_killed_players: list[player.Player] = []

    async def main(self):
        """
        昼の処理のメインルーチン。
        前夜に死亡したプレイヤーの通知、処刑投票、保護状態のリセットを行う。
        """
        self.today_killed_players = [
            player
            for player in self.game.last_alive_players
            if player not in self.game.alive_players
        ]

        await self._announce_day_start()
        await self.execute_vote()
        self.reset_protected()

    def reset_protected(self) -> None:
        """
        各プレイヤーの「殺害保護」状態をリセットする。
        狩人等の能力で保護された状態を初期化するための処理。
        """
        if self.game is not None:
            for player in self.game.players:
                player.is_kill_protected = False

    async def _announce_day_start(self) -> None:
        """
        昼の開始を全体に通知する。
        埋め込みメッセージで、前夜の死亡者を一覧表示する。
        """
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
        if self.game is not None:
            await self.game.channel.send(embed=embed)

    def _decide_execute_target(self, results: list[int | None]) -> int | None:
        """
        処刑投票の結果から、実際に処刑する対象を決定する。
        過半数がスキップした場合は処刑を行わない。
        また、最も票を得たプレイヤーが複数いた場合も処刑しない。

        Parameters
        ----------
        results: list[int]
            投票結果のリスト。各プレイヤーのIDが格納されている。
        Returns
        -------
        int | None
            処刑対象のプレイヤーID。決定しなかった場合はNone。
        """
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
        """
        処刑投票を実施し、その結果に基づいて対象プレイヤーを処刑する。
        対象が決定しなかった場合は処刑をスキップする。
        """
        if self.game is not None:
            embed = discord.Embed(title="処刑投票", description="処刑対象を選んでください")
            view = PlayerChoiceView(
                choices=self.game.alive_players,
                process="Execute",
                allow_skip=True,
                game_id=self.id,
            )

            # チャンネルに投票用のメッセージとビューを送信
            await self.game.channel.send(embed=embed, view=view)
            await view.wait()

            filtered_votes = [v for v in view.votes.values()]
            execute_id = self._decide_execute_target(filtered_votes)

            if execute_id is None:
                await self.game.channel.send(f"誰も処刑されませんでした。")
                self.logger.info(f"Nobody was executed.")
            else:
                # 該当するプレイヤーを検索して処刑処理を実行
                target_player = [p for p in self.game.alive_players if p.id == execute_id][
                    0
                ]
                await self.game.channel.send(f"<@!{target_player.id}> が処刑されました。")

                await target_player.execute()
                self.game.refresh_alive_players()
                self.logger.info(f"{target_player.id} was executed.")

            # 前回の生存プレイヤーリストを更新
            self.game.last_alive_players = self.game.alive_players


class EndManager:
    """
    ゲーム終了時の処理や勝利条件のチェックを行うクラス。
    勝利条件の判定、結果の送信、ゲームインスタンスの削除などを管理する。

    parameters
    ----------
    id: int | None
        ゲームID。Noneの場合は新規ゲームとして扱う。
    """

    def __init__(self, id: int) -> None:
        self.id = id
        self.game = g.werewolf_games.get(id)
        self.logger = make_logger("EndManager", id)
        if self.game is not None:
            self.t = self.game.translator

    async def execute_game_end(self) -> None:
        """
        ゲーム終了時に勝利結果を送信し、ゲームインスタンスを削除する。
        """
        await self._send_result()
        if self.game is not None:
            self.game.delete()

    async def win_check(self) -> None:
        """
        ゲームの勝利条件を判定する。
        人狼の人数が生存者の半数以上なら人狼勝利、
        人狼がいなければ村人勝利、
        さらに妖狐(Fox)が生存している場合は狐勝利に上書きする。
        """

        if self.game is not None:
            if self._is_werewolf_win():
                self.game.win_team = "TeamWerewolf"
            elif self._is_villager_win():
                self.game.win_team = "TeamVillager"

            if self.game.win_team in ["TeamWerewolf", "TeamVillager"]:
                if self._is_fox_win():
                    self.game.win_team = "TeamFox"

            if self.game.win_team:
                # 勝利陣営に所属するプレイヤーを勝者リストとして保持
                self.game.winner = [
                    p for p in self.game.players if p.role.team == self.game.win_team
                ]
                self.game.is_ended = True

    def _is_werewolf_win(self) -> bool:
        """
        人狼の数が生存プレイヤーの半数以上であれば勝利と判定する。
        returns
        -------
        bool
            人狼勝利の場合はTrue、そうでない場合はFalse。
        """
        if self.game is not None:
            if (
                len([p for p in self.game.alive_players if p.role.is_werewolf])
                >= len(self.game.alive_players) / 2
            ):
                return True
        return False

    def _is_villager_win(self) -> bool:
        """
        生存しているプレイヤーに人狼がいなければ、村人の勝利と判定する。
        returns
        -------
        bool
            村人勝利の場合はTrue、そうでない場合はFalse。
        """
        if self.game is not None:
            if len([p for p in self.game.alive_players if p.role.is_werewolf]) == 0:
                return True
        return False

    def _is_fox_win(self) -> bool:
        """
        妖狐（Fox）が生存していれば狐勝利と判定する。
        returns
        -------
        bool
            狐勝利の場合はTrue、そうでない場合はFalse。
        """
        if self.game is not None:
            if [p for p in self.game.alive_players if p.role.name == "Fox"]:
                return True
        return False

    async def _send_result(self) -> None:
        """
        ゲームの最終結果を全体チャンネルに通知する。
        勝利陣営と勝者リスト、各プレイヤーの最終ステータス・役職情報を送信する。
        """
        if self.game is not None:
            embed = discord.Embed(
                title="人狼ゲーム",
                description=f"{self.t.getstring(self.game.win_team or "")}勝利",
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

    async def game_end(self, team: str, winners: list[player.Player]) -> None:
        """
        ゲームを終了させる。

        Parameters
        ----------
        team: str
            勝利した陣営の名称
        winners: list[player.Player]
            勝利したプレイヤーのリスト
        """
        if self.game is not None:
            self.game.is_ended = True
            self.game.win_team = team
            self.game.winner = winners
