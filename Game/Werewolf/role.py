import tomllib
from typing import Final

with open("Resources/role_description.toml", "rb") as f:
    ROLE_DESCRIPTIONS: Final = tomllib.load(f)


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

    def initialize_role(self):
        self.name = self.__class__.__name__
        self.team = ROLE_DESCRIPTIONS[self.name]["Team"]
        self.fortune_result = ROLE_DESCRIPTIONS[self.name]["FortuneResult"]
        self.win_condition = ROLE_DESCRIPTIONS[self.name]["WinCondition"]
        self.description = ROLE_DESCRIPTIONS[self.name]["Description"]

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


# 村人陣営
class Villager(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()


class Medium(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()


# 人狼陣営
class Hunter(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()


class Bakery(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()


# 人狼陣営
class Werewolf(Role):
    def __init__(self):
        super().__init__()
        self.is_werewolf = True

        self.initialize_role()


class BlackCat(Role):
    def __init__(self):
        super().__init__()
        self.is_villager = True

        self.initialize_role()


# 第三陣営
class Teruteru(Role):
    def __init__(self):
        super().__init__()
        self.is_neutral = True

        self.initialize_role()
