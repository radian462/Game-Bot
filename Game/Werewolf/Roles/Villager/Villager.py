from ...role import Role


class Villager(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.name = self.__class__.__name__
        self.team = "TeamVillager"
        self.fortune_result = "TeamVillager"
        self.description = "VillagerDescription"
        self.win_condition = "VillagerWinCondition"
