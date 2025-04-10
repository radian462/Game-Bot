from ...manager import EndManager
from ...role import Role


class Teruteru(Role):
    def __init__(self):
        super().__init__()
        self.is_neutral = True

        self.name = self.__class__.__name__
        self.team = "TeamTeruteru"
        self.fortune_result = "TeamNeutral"
        self.description = "TeruteruDescription"
        self.win_condition = "TeruteruWinCondition"

    async def executed_ability(self, game_id: int, player):
        """
        自分が処刑されたときに、勝利する。

        Parameters
        ----------
        game_id : int
            ゲームのID

        player : Player
            この役職のプレイヤー情報
        """
        await EndManager(game_id).game_end(
            team="TeamTeruteru",
            winners=[player],
        )
