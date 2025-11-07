from dataclasses import dataclass, field

from discord import Client

from .phases.game_start_phase import GameStartPhase
from helpers.make_logger import make_logger


@dataclass
class WerewolfGameConfig:
    id: int
    player_ids: list[int] = field(default_factory=list)
    roles: dict[str, int] = field(default_factory=dict)


class WerewolfGameManager:
    def __init__(self, config: WerewolfGameConfig, client: Client | None = None):
        self.client = client
        self.config = config

        self.logger = make_logger("WerewolfGameManager", context=str(self.config.id))

        if self.client is not None:
            self.logger.info("Client is None, Starting game with test mode.")

    async def send_direct_message(self, player_id: int, message: str):
        if self.client is None:
            self.logger.info(f"(Test Mode) Sending DM to {player_id}: {message}")
            return

        user = await self.client.fetch_user(player_id)
        await user.send(message)

    def game_start(self):
        GameStartPhase()
