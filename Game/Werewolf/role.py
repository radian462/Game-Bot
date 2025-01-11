class Role:
    def __init__(self):
        self.name = ""
        self.is_villager = False
        self.is_werewolf = False
        self.is_neutral = False
        self.team = ""


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


class Hunter(Role):
    def __init__(self):
        super().__init__()
        self.name = "狩人"
        self.is_villager = True
        self.team = "Villager"


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
