from ...role import Role


class Madmate(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()
