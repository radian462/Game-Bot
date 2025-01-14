class Role:
    def __init__(self):
        self.name = ""
        self.is_villager = False
        self.is_werewolf = False
        self.is_neutral = False
        self.team = ""

        self.is_kill_protected = False


# 村人陣営
class Villager(Role):
    def __init__(self):
        super().__init__()
        self.name = "村人"
        self.is_villager = True
        self.team = "Villager"


class Seer(Role):
    def __init__(self):
        super().__init__()
        self.name = "占い師"
        self.is_villager = True
        self.team = "Villager"


class Medium(Role):
    def __init__(self):
        super().__init__()
        self.name = "霊媒師"
        self.is_villager = True
        self.team = "Villager"


# 人狼陣営
class Hunter(Role):
    def __init__(self):
        super().__init__()
        self.name = "狩人"
        self.is_villager = True
        self.team = "Villager"


class Bakery(Role):
    def __init__(self):
        super().__init__()
        self.name = "パン屋"
        self.is_villager = True
        self.team = "Villager"


# 人狼陣営
class Werewolf(Role):
    def __init__(self):
        super().__init__()
        self.name = "人狼"
        self.is_werewolf = True
        self.team = "Werewolf"


class Madmate(Role):
    def __init__(self):
        super().__init__()
        self.name = "狂人"
        self.is_villager = True
        self.team = "Werewolf"


class BlackCat(Role):
    def __init__(self):
        super().__init__()
        self.name = "黒猫"
        self.is_villager = True
        self.team = "Werewolf"


# 第三陣営
class Teruteru(Role):
    def __init__(self):
        super().__init__()
        self.name = "てるてる"
        self.is_neutral = True
        self.team = "Neutral"


class Fox(Role):
    def __init__(self):
        super().__init__()
        self.name = "妖狐"
        self.is_neutral = True
        self.team = "Neutral"

        self.is_kill_protected = True


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
