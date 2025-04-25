import Modules.global_value as g

from ...role import Role


class Medium(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.name = self.__class__.__name__
        self.team = "TeamVillager"
        self.fortune_result = "TeamVillager"
        self.description = "MediumDescription"
        self.win_condition = "VillagerWinCondition"

    async def night_ability(self, game_id: int, player):
        """
        前回処刑されたプレイヤーの陣営を確認する。

        Parameters
        ----------
        game_id : int
            ゲームのID
        player : Player
            この役職のプレイヤー情報
        """

        game = g.werewolf_games.get(game_id)

        if game is not None:
            t = game.translator
            target = game.last_executed_player

            if target is not None:
                await player.message(
                    f"{target.name}は{t.getstring(target.role.fortune_result)}でした。"
                )
