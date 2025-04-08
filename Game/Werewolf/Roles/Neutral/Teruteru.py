from ...manager import EndManager
from ...role import Role


class Teruteru(Role):
    def __init__(self):
        super().__init__()
        self.is_neutral = True

        self.initialize_role()

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
        await EndManager(game_id).main(
            team="TeamTeruteru",
            winners=[player],
        )
