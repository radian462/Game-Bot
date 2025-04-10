from ...role import Role


class Madmate(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.name = self.__class__.__name__
        self.team = "TeamWerewolf"
        self.fortune_result = "TeamVillager"
        self.description = "MadmateDescription"
        self.win_condition = "MadmateWinCondition"
