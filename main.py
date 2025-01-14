import os

import discord
from discord import app_commands

import Game.Werewolf.role as role

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print("ログインしました")


class JoinView(discord.ui.View):
    def __init__(self, id: str, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.id = id

    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in werewolf_manager.games[self.id]["players"]:
            if (
                len(werewolf_manager.games[self.id]["players"]) + 1
                >= werewolf_manager.games[self.id]["limit"]
            ):
                await interaction.response.send_message(
                    "人数制限に達しました", ephemeral=True
                )
                return

            if interaction.user.id != werewolf_manager.games[self.id]["host"]:
                werewolf_manager.games[self.id]["players"].add(interaction.user.id)
            else:
                await interaction.response.send_message(
                    "募集者は参加できません", ephemeral=True
                )
                return

            await update_recruiting_embed(self.id, interaction)
        else:
            await interaction.response.send_message(
                "すでに参加しています", ephemeral=True
            )

    @discord.ui.button(label="退出", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in werewolf_manager.games[self.id]["players"]:
            if interaction.user.id != werewolf_manager.games[self.id]["host"]:
                werewolf_manager.games[self.id]["players"].remove(interaction.user.id)

            await update_recruiting_embed(self.id, interaction)
        elif interaction.user.id == werewolf_manager.games[self.id]["host"]:
            await interaction.response.send_message(
                "募集者は退出できません", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "あなたは参加していません", ephemeral=True
            )

    @discord.ui.button(label="開始", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == werewolf_manager.games[self.id]["host"]:
            pass
        else:
            await interaction.response.send_message(
                "あなたは募集者ではありません", ephemeral=True
            )

    @discord.ui.button(label="中止", style=discord.ButtonStyle.grey)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == werewolf_manager.games[self.id]["host"]:
            embed = discord.Embed(
                title=f"人狼ゲーム",
                description="募集が中止されました",
                color=discord.Color.red(),
            )

            await interaction.response.edit_message(embed=embed, view=None)
            del werewolf_manager.games[self.id]
        else:
            await interaction.response.send_message(
                "あなたは募集者ではありません", ephemeral=True
            )

    """
    @discord.ui.button(label="⚙️", style=discord.ButtonStyle.grey)
    async def setting(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
    """


class WerewolfManager:
    def __init__(self):
        self.games = {}

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
            "host": host_id,
            "players": set(),
            "roles": {role.Werewolf(): 1},
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
    game_id: int, interaction: discord.Interaction | None = None
) -> discord.Embed:
    game_info = werewolf_manager.games[game_id]

    embed = discord.Embed(
        title=f"人狼ゲーム({len(game_info['players']) + 1}/{game_info['limit']}人)",
        description=f"募集者:<@!{game_info['host']}>",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="参加者",
        value="\n".join([f"<@!{player}>" for player in game_info["players"]]) or "なし",
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
    if interaction:
        await interaction.response.edit_message(embed=embed, view=game_info["view"])
    else:
        channel = client.get_channel(game_info["channel_id"])
        message = await channel.fetch_message(game_info["message_id"])
        await message.edit(embed=embed, view=game_info["view"])


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
@app_commands.describe(limit="人数制限")
@discord.app_commands.choices(
    limit=[discord.app_commands.Choice(name=i, value=i) for i in range(3, 16)]
)
async def werewolf(interaction: discord.Interaction, limit: int = 10):
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


@tree.command(name="role", description="人狼ゲームの役職を設定します")
@app_commands.describe(role_name="役職名", number="人数")
@discord.app_commands.choices(
    role_name=[
        discord.app_commands.Choice(name=role.name, value=role.name)
        for role in role.roles.values()
    ],
    number=[discord.app_commands.Choice(name=i, value=i) for i in range(0, 15)],
)
async def set_role(interaction: discord.Interaction, role_name: str, number: int):
    host_game_id = [
        game_id
        for game_id, game_info in werewolf_manager.games.items()
        if game_info["host"] == interaction.user.id
    ][0]

    if host_game_id:
        werewolf_manager.games[host_game_id]["roles"][role.roles[role_name]] = number
        await interaction.response.send_message(
            f"{role_name}を{number}人に設定しました", ephemeral=True
        )

        await update_recruiting_embed(host_game_id)
    else:
        await interaction.response.send_message("ゲームが存在しません", ephemeral=True)


client.run(os.getenv("DISCORD_TOKEN"))
