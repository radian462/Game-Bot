from ..role import Role, Team

class Villager(Role):
    def __init__(self):
        super().__init__()
        self.name = "Villager"
        self.is_villager = True
        self.team = Team.VILLAGER