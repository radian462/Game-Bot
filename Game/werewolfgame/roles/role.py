from enum import Enum


class Team(Enum):
    VILLAGER = "VILLAGER"
    WEREWOLF = "WEREWOLF"
    NEUTRAL = "NEUTRAL"


class Role:
    def __init__(self):
        self.name = ""
        self.is_villager = False
        self.is_werewolf = False
        self.is_neutral = False

        self.team: Team | None = None

        self.is_kill_protected = False

    async def night_ability(self, game, player):
        # 夜行動の記述
        pass

    async def seer_ability(self, game, player):
        # 占われたときの記述
        pass

    async def killed_ability(self, game, player):
        # 殺害されたときの記述
        pass

    async def executed_ability(self, game, player):
        # 処刑されたときの記述
        pass
