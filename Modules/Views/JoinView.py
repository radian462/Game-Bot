import traceback
from typing import Final

import discord

import Modules.global_value as g
from Modules.logger import make_logger

NOT_HOST_MSG: Final = "あなたは募集者ではありません"
NOT_PLAYER_MSG: Final = "あなたは参加していません"
ALREADY_PLAYER_MSG: Final = "すでに参加しています"
LIMIT_PLAYER_MSG: Final = "人数制限に達しました"
HOST_JOIN_MSG: Final = "募集者は参加できません"
HOST_LEAVE_MSG: Final = "募集者は退出できません"
ERROR_TEMPLATE: Final = "エラーが発生しました\n"

logger = make_logger("JoinView")


class JoinView(discord.ui.View):
    def __init__(self, id: str, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.id = id
        self.game = None

    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game is None:
            self.game = g.werewolf_games.get(self.id)

        logger.info(f"User {interaction.user.id} clicked join button.")
        try:
            # ホストかどうか
            if interaction.user.id == self.game.host_id:
                await interaction.response.send_message(HOST_JOIN_MSG, ephemeral=True)
                logger.info(f"User {interaction.user.id} (host) attempted to join but is not allowed.")
                return

            # すでに参加しているか
            if interaction.user.id in self.game.participant_ids:
                await interaction.response.send_message(ALREADY_PLAYER_MSG, ephemeral=True)
                logger.info(f"User {interaction.user.id} is already a participant.")
                return
            
            # 参加人数制限に達しているか
            if len(self.game.participant_ids) + 1 >= self.game.limit:
                await interaction.response.send_message(LIMIT_PLAYER_MSG, ephemeral=True)
                logger.info(f"User {interaction.user.id} could not join due to player limit.")
                return

            self.game.participant_ids.add(interaction.user.id)
            await self.game.update_recruiting_embed(interaction)
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(ERROR_TEMPLATE + str(e))

    @discord.ui.button(label="退出", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game is None:
            self.game = g.werewolf_games.get(self.id)

        logger.info(f"User {interaction.user.id} clicked leave button.")
        try:
            # ホストかどうか
            if interaction.user.id == self.game.host_id:
                await interaction.response.send_message(HOST_LEAVE_MSG, ephemeral=True)
                logger.info(f"User {interaction.user.id} (host) attempted to leave but is not allowed.")
                return
            
            # 参加しているか
            if interaction.user.id not in self.game.participant_ids:
                await interaction.response.send_message(NOT_PLAYER_MSG, ephemeral=True)
                logger.info(f"User {interaction.user.id} tried to leave but was not in the game.")
                return

            self.game.participant_ids.remove(interaction.user.id)
            await self.game.update_recruiting_embed(interaction)
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(ERROR_TEMPLATE + str(e))

    @discord.ui.button(label="開始", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"User {interaction.user.id} clicked start button.")

    @discord.ui.button(label="中止", style=discord.ButtonStyle.grey)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"User {interaction.user.id} clicked end button.")
