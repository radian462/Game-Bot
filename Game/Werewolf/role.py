class Role:
    def __init__(self):
        self.name = ""
        self.is_villager = False
        self.is_werewolf = False
        self.is_neutral = False

        self.team = ""
        self.win_condition = ""
        self.description = ""

        self.is_kill_protected = False

    async def night_ability(self, game_id: int, player):
        # 夜行動の記述
        pass

    async def seer_ability(self, game_id: int, player):
        # 占われたときの記述
        pass

    async def killed_ability(self, game_id: int, player):
        # 殺害されたときの記述
        pass

    async def executed_ability(self, game_id: int, player):
        # 処刑されたときの記述
        pass
