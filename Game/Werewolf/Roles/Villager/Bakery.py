from ...role import Role


class Bakery(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.name = self.__class__.__name__
        self.team = "TeamVillager"
        self.fortune_result = "TeamVillager"
        self.description = "BakeryDescription"
        self.win_condition = "VillagerWinCondition"
