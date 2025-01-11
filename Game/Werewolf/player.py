class Player:
    def __init__(self, id: int | str):
        self.id = id
        self.status = "Alive"
        self.is_alive = True
        self.role = None
        
        self.is_kill_protect = False

    def assign_role(self, role: Role):
        self.role = role

    def kill(self):
        if not self.is_kill_protect:
            self.status = "Killed"
            self.is_alive = False