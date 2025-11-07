from dataclasses import dataclass, field

from discord import Client

from .phases.game_start_phase import GameStartPhase

@dataclass
class WerewolfGameConfig:
    player_ids: list[int] = field(default_factory=list)
    roles: dict[str, int] = field(default_factory=dict)

class WerewolfGameManager():
    def __init__(self, config: WerewolfGameConfig, client: Client | None = None):
        self.client = client
        self.config = config

    def game_start(self):
        GameStartPhase()