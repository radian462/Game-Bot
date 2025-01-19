import tomllib
from typing import final

with open("Game/Werewolf/resources/role_description.toml", "rb") as f:
    ROLE_DESCRIPTIONS: final = tomllib.load(f)


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
        self.team = ROLE_DESCRIPTIONS[self.name]["Team"]
        self.win_condition = ROLE_DESCRIPTIONS[self.name]["WinCondition"]
        self.description = ROLE_DESCRIPTIONS[self.name]["Description"]


# 村人陣営
class Villager(Role):
    def __init__(self):
        super().__init__()
        self.name = "村人"
        self.is_villager = True

        self.initialize_role()


class Seer(Role):
    def __init__(self):
        super().__init__()
        self.name = "占い師"
        self.is_villager = True

        self.initialize_role()


class Medium(Role):
    def __init__(self):
        super().__init__()
        self.name = "霊媒師"
        self.is_villager = True

        self.initialize_role()


# 人狼陣営
class Hunter(Role):
    def __init__(self):
        super().__init__()
        self.name = "狩人"
        self.is_villager = True

        self.initialize_role()


class Bakery(Role):
    def __init__(self):
        super().__init__()
        self.name = "パン屋"
        self.is_villager = True

        self.initialize_role()


# 人狼陣営
class Werewolf(Role):
    def __init__(self):
        super().__init__()
        self.name = "人狼"
        self.is_werewolf = True

        self.initialize_role()


class Madmate(Role):
    def __init__(self):
        super().__init__()
        self.name = "狂人"
        self.is_villager = True

        self.initialize_role()


class BlackCat(Role):
    def __init__(self):
        super().__init__()
        self.name = "黒猫"
        self.is_villager = True

        self.initialize_role()


# 第三陣営
class Teruteru(Role):
    def __init__(self):
        super().__init__()
        self.name = "てるてる"
        self.is_neutral = True

        self.initialize_role()


class Fox(Role):
    def __init__(self):
        super().__init__()
        self.name = "妖狐"
        self.is_neutral = True

        self.initialize_role()

        self.is_kill_protected = True


# 役職のインスタンスを作成するリスト
role_classes = [
    Seer(),
    Medium(),
    Hunter(),
    Bakery(),
    Werewolf(),
    Madmate(),
    BlackCat(),
    Teruteru(),
    Fox(),
]

roles = {role.name: role for role in role_classes}
