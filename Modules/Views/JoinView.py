import discord

from Modules.logger import make_logger

logger = make_logger("System")


class JoinView(discord.ui.View):
    def __init__(self, id: str, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.id = id

    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked join button.")

    @discord.ui.button(label="退出", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked leave button.")

    @discord.ui.button(label="開始", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked start button.")

    @discord.ui.button(label="中止", style=discord.ButtonStyle.grey)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked end button.")
