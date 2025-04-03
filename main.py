import os
import traceback
import uuid
from typing import Final, Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

import Modules.global_value as g
from Game.Werewolf.game import WerewolfGame
from Game.Werewolf.role import Bakery, Hunter, Medium, Teruteru, Werewolf
from Game.Werewolf.Roles.Neutral import Fox
from Game.Werewolf.Roles.Villiger import BlackCat, Madmate, Nekomata, Seer
from Modules.logger import make_logger
from Modules.translator import Translator
from Modules.Views.JoinView import JoinView

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

logger = make_logger("System")
t = Translator("ja")

GAME_NOT_EXIST_MSG: Final = "ゲームが存在しません"

ERROR_TEMPLATE: Final = "エラーが発生しました\n"


@client.event
async def on_ready():
    await tree.sync()
    logger.info(f"Successed to Log in")


# 役職のインスタンスを作成するリスト
role_classes = [
    Seer.Seer(),
    Medium(),
    Hunter(),
    Bakery(),
    Nekomata.Nekomata(),
    Werewolf(),
    Madmate.Madmate(),
    BlackCat.BlackCat(),
    Teruteru(),
    Fox.Fox(),
]

roles = {role.name: role for role in role_classes}


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
@app_commands.describe(limit="人数制限")
@discord.app_commands.choices(
    limit=[discord.app_commands.Choice(name=i, value=i) for i in range(3, 16)]
)
@discord.app_commands.guild_only()
async def werewolf(interaction: discord.Interaction, limit: int = 10):
    logger.info(f"{interaction.user.id} created a game.")
    try:
        id = int(uuid.uuid4().int)

        view = JoinView(id=id, timeout=None)
        await interaction.response.send_message(view=view)
        message = await interaction.original_response()

        game = WerewolfGame(
            id=id,
            host_id=interaction.user.id,
            limit=limit,
            message=message,
            channel=interaction.channel,
            client=client,
            joinview=view,
            logger=make_logger("Game", id),
            translator=Translator("ja"),
            roles={roles["Werewolf"]: 1},
        )
        g.werewolf_games[id] = game
        await game.update_recruiting_embed()
    except Exception as e:
        traceback.print_exc()
        await interaction.response.send_message(ERROR_TEMPLATE + str(e))


@tree.command(name="role", description="人狼ゲームの役職を設定します")
@app_commands.describe(role="役職名", number="人数")
@discord.app_commands.choices(
    role=[
        discord.app_commands.Choice(name=t.getstring(r.name), value=r.name)
        for r in roles.values()
    ],
    number=[discord.app_commands.Choice(name=i, value=i) for i in range(0, 15)],
)
@discord.app_commands.guild_only()
async def set_role(interaction: discord.Interaction, role: str, number: int):
    logger.info(f"{interaction.user.id} set {role} to {number}.")
    try:
        # ゲームの中で募集中かつあなたのゲームでこのチャンネル内であるゲームを取得
        recruiting_games = [
            game for game in g.werewolf_games.values() if game.is_started == False
        ]
        your_games = [
            game for game in recruiting_games if game.host_id == interaction.user.id
        ]
        setting_game = next(
            (game for game in your_games if game.channel.id == interaction.channel.id),
            None,
        )

        if setting_game is None:
            await interaction.response.send_message(GAME_NOT_EXIST_MSG, ephemeral=True)
            return
        else:
            setting_game.roles[roles[role]] = number
            await interaction.response.send_message(
                f"{role}を{number}人に設定しました", ephemeral=True
            )

            await setting_game.update_recruiting_embed()
    except Exception as e:
        traceback.print_exc()
        await interaction.response.send_message(ERROR_TEMPLATE + str(e))


load_dotenv()
client.run(os.getenv("DISCORD_TOKEN"))
