from ...role import Role


# 人狼陣営
class Werewolf(Role):
    def __init__(self):
        super().__init__()
        self.is_werewolf = True

        self.name = self.__class__.__name__
        self.team = "TeamWerewolf"
        self.fortune_result = "TeamWerewolf"
        self.description = "WerewolfDescription"
        self.win_condition = "WerewolfWinCondition"
