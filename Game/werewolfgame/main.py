from dataclasses import dataclass, field

from discord import Client

from helpers.make_logger import make_logger

from .phases.game_start_phase import GameStartPhase
from .player import Player
from .roles.role import Role


@dataclass
class WerewolfGameConfig:
    id: int
    player_ids: list[int] = field(default_factory=list)
    roles: dict[Role, int] = field(default_factory=dict)

    channel_id: int | None = None
    guild_id: int | None = None

class WerewolfGameManager:
    def __init__(self, config: WerewolfGameConfig, client: Client | None = None):
        self.client = client
        self.config = config

        self.logger = make_logger("WerewolfGameManager", context=str(self.config.id))

        if self.client is not None:
            self.logger.info("Client is None, Starting game with test mode.")

    async def send_direct_message(self, player: Player, message: str):
        if self.client is None:
            self.logger.info(f"(Test Mode) Sending DM to {player.id}: {message}")
            return

        await player.member.send(message)

    async def send_announce(self, message: str):
        if self.client is None:
            self.logger.info(
                f"(Test Mode) Announcing to game {self.config.id}: {message}"
            )
            return

    def game_start(self):
        GameStartPhase.run()

    def morning_phase(self):
        pass

    def voting_phase(self):
        pass

    def night_phase(self):
        pass

    def game_end(self):
        pass
