import os
import traceback
from typing import final

import discord
from discord import app_commands
from dotenv import load_dotenv

import Game.Werewolf.main as werewolf_main
import Game.Werewolf.role as werewolf_role
from Modules.logger import make_logger

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

NOT_HOST_MSG: final = "あなたは募集者ではありません"
NOT_PLAYER_MSG: final = "あなたは参加していません"
ALREADY_PLAYER_MSG: final = "すでに参加しています"
LIMIT_PLAYER_MSG: final = "人数制限に達しました"
HOST_JOIN_MSG: final = "募集者は参加できません"
HOST_LEAVE_MSG: final = "募集者は退出できません"
GAME_NOT_EXIST_MSG: final = "ゲームが存在しません"

ERROR_TEMPLATE: final = "エラーが発生しました\n"


logger = make_logger("System")


@client.event
async def on_ready():
    await tree.sync()
    logger.info(f"ログインしました")


class JoinView(discord.ui.View):
    def __init__(self, id: str, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.id = id

    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked join button.")
        try:
            self.game = werewolf_manager.games[self.id]
            if interaction.user.id not in self.game["participants"]:
                if len(self.game["participants"]) + 1 >= self.game["limit"]:
                    await interaction.response.send_message(
                        LIMIT_PLAYER_MSG, ephemeral=True
                    )
                    logger.info(
                        f"{interaction.user.id} could not join the game for limit."
                    )
                    return

                if interaction.user.id != self.game["host"]:
                    werewolf_manager.games[self.id]["participants"].add(
                        interaction.user.id
                    )
                    logger.info(f"{interaction.user.id} joined the game.")
                else:
                    await interaction.response.send_message(
                        HOST_JOIN_MSG, ephemeral=True
                    )
                    return

                await update_recruiting_embed(self.id, interaction)
            else:
                await interaction.response.send_message(
                    ALREADY_PLAYER_MSG, ephemeral=True
                )
        except Exception as e:
            traceback.print_exc()
            logger.debug(self.game)
            await interaction.response.send_message(ERROR_TEMPLATE + str(e))

    @discord.ui.button(label="退出", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked leave button.")
        try:
            self.game = werewolf_manager.games[self.id]
            if interaction.user.id in self.game["participants"]:
                if interaction.user.id != self.game["host"]:
                    werewolf_manager.games[self.id]["participants"].remove(
                        interaction.user.id
                    )

                logger.info(f"{interaction.user.id} leaved the game.")
                await update_recruiting_embed(self.id, interaction)
            elif interaction.user.id == self.game["host"]:
                await interaction.response.send_message(HOST_LEAVE_MSG, ephemeral=True)
            else:
                await interaction.response.send_message(NOT_PLAYER_MSG, ephemeral=True)
        except Exception as e:
            traceback.print_exc()
            logger.debug(self.game)
            await interaction.response.send_message(ERROR_TEMPLATE + str(e))

    @discord.ui.button(label="開始", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked start button.")
        self.game = werewolf_manager.games[self.id]
        if interaction.user.id == self.game["host"]:
            await update_recruiting_embed(self.id, interaction, show_view=False)
            await werewolf_main.main(self.game, client)
        else:
            await interaction.response.send_message(NOT_HOST_MSG, ephemeral=True)

    @discord.ui.button(label="中止", style=discord.ButtonStyle.grey)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"{interaction.user.id} clicked end button.")
        try:
            if interaction.user.id == werewolf_manager.games[self.id]["host"]:
                embed = discord.Embed(
                    title=f"人狼ゲーム",
                    description="募集が中止されました",
                    color=discord.Color.red(),
                )

                await interaction.response.edit_message(embed=embed, view=None)
                del werewolf_manager.games[self.id]

                logger.info(
                    f"{interaction.user.id} canceled the game of {self.id}."
                )
            else:
                await interaction.response.send_message(NOT_HOST_MSG, ephemeral=True)
        except Exception as e:
            traceback.print_exc()
            logger.debug(self.game)
            await interaction.response.send_message(ERROR_TEMPLATE + str(e))

    """
    @discord.ui.button(label="⚙️", style=discord.ButtonStyle.grey)
    async def setting(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
    """


class WerewolfManager:
    def __init__(self):
        self.games: dict[int, dict[str, int | set | dict | discord.ui.View]] = {}

    def create_game(
        self,
        game_id: int,
        host_id: int,
        limit: int,
        message_id: int,
        channel_id: int,
        view: JoinView,
    ) -> int:
        self.games[game_id] = {
            "id": game_id,
            "host": host_id,
            "participants": set(),
            "players": [],
            "roles": {werewolf_role.roles["人狼"]: 1},
            "limit": limit,
            "message_id": message_id,
            "channel_id": channel_id,
            "view": view,
        }

        return game_id

    def delete_game(self, game_id: int):
        del self.games[game_id]


werewolf_manager = WerewolfManager()


async def update_recruiting_embed(
    game_id: int, interaction: discord.Interaction | None = None, show_view: bool = True
) -> discord.Embed:
    game_info = werewolf_manager.games[game_id]

    embed = discord.Embed(
        title=f"人狼ゲーム({len(game_info["participants"]) + 1}/{game_info['limit']}人)",
        description=f"募集者:<@!{game_info['host']}>",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="参加者",
        value="\n".join([f"<@!{player}>" for player in game_info["participants"]])
        or "なし",
        inline=False,
    )
    embed.add_field(
        name="役職",
        value="\n".join(
            [
                f"{role.name} {count}人"
                for role, count in game_info["roles"].items()
                if count > 0
            ]
        )
        or "なし",
        inline=False,
    )

    view = game_info["view"] if show_view == True else None

    if interaction:
        await interaction.response.edit_message(embed=embed, view=view)
    else:
        channel = client.get_channel(game_info["channel_id"])
        message = await channel.fetch_message(game_info["message_id"])
        await message.edit(embed=embed, view=view)


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
@app_commands.describe(limit="人数制限")
@discord.app_commands.choices(
    limit=[discord.app_commands.Choice(name=i, value=i) for i in range(3, 16)]
)
@discord.app_commands.guild_only()
async def werewolf(interaction: discord.Interaction, limit: int = 10):
    logger.info(f"{interaction.user.id} created a game.")
    try:
        view = JoinView(id=interaction.id, timeout=None)

        await interaction.response.defer()
        message = await interaction.followup.send(view=view)

        werewolf_manager.create_game(
            game_id=interaction.id,
            host_id=interaction.user.id,
            limit=limit,
            message_id=message.id,
            channel_id=interaction.channel_id,
            view=view,
        )

        await update_recruiting_embed(interaction.id)
    except Exception as e:
        traceback.print_exc()
        await interaction.response.send_message(ERROR_TEMPLATE + str(e))


@tree.command(name="role", description="人狼ゲームの役職を設定します")
@app_commands.describe(role="役職名", number="人数")
@discord.app_commands.choices(
    role=[
        discord.app_commands.Choice(name=r.name, value=r.name)
        for r in werewolf_role.roles.values()
    ],
    number=[discord.app_commands.Choice(name=i, value=i) for i in range(0, 15)],
)
@discord.app_commands.guild_only()
async def set_role(interaction: discord.Interaction, role: str, number: int):
    logger.info(f"{interaction.user.id} set {role} to {number}.")
    try:
        # 現在の募集中のゲームを取得
        host_game_list = [
            werewolf_manager.games[game_id]
            for game_id, game_info in werewolf_manager.games.items()
            if game_info["host"] == interaction.user.id
        ]

        # ここの処理は削除されたメッセージを除外するため
        for game_info in host_game_list:
            try:
                channel = client.get_channel(game_info["channel_id"])
                await channel.fetch_message(game_info["message_id"])
                host_game_id = game_info["id"]
                break
            except discord.errors.NotFound:
                del werewolf_manager.games[game_info["id"]]
                continue

        else:
            host_game_id = None

        if host_game_id is not None:
            werewolf_manager.games[host_game_id]["roles"][
                werewolf_role.roles[role]
            ] = number
            await interaction.response.send_message(
                f"{role}を{number}人に設定しました", ephemeral=True
            )

            await update_recruiting_embed(host_game_id)
        else:
            await interaction.response.send_message(GAME_NOT_EXIST_MSG, ephemeral=True)
    except Exception as e:
        traceback.print_exc()
        await interaction.response.send_message(ERROR_TEMPLATE + str(e))


load_dotenv()

client.run(os.getenv("DISCORD_TOKEN"))
