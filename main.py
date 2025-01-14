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


def make_participants_embed(game_info: dict) -> discord.Embed:
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
    return embed


all_game_info = {}


class JoinView(discord.ui.View):
    def __init__(self, id, timeout=180, limit=10):
        super().__init__(timeout=timeout)
        self.id = id
        self.limit = limit

    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in all_game_info[self.id]["players"]:
            if len(all_game_info[self.id]["players"]) + 1 >= self.limit:
                await interaction.response.send_message(
                    "人数制限に達しました", ephemeral=True
                )
                return

            if interaction.user.id != all_game_info[self.id]["host"]:
                all_game_info[self.id]["players"].add(interaction.user.id)

            await interaction.response.edit_message(
                embed=make_participants_embed(all_game_info[self.id]),
                view=self,
            )
        else:
            await interaction.response.send_message(
                "すでに参加しています", ephemeral=True
            )

    @discord.ui.button(label="退出", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in all_game_info[self.id]["players"]:
            if interaction.user.id != all_game_info[self.id]["host"]:
                all_game_info[self.id]["players"].remove(interaction.user.id)

            await interaction.response.edit_message(
                embed=make_participants_embed(all_game_info[self.id]),
                view=self,
            )
        elif interaction.user.id == all_game_info[self.id]["host"]:
            await interaction.response.send_message(
                "募集者は退出できません", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "あなたは参加していません", ephemeral=True
            )

    @discord.ui.button(label="開始", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == all_game_info[self.id]["host"]:
            pass
        else:
            await interaction.response.send_message(
                "あなたは募集者ではありません", ephemeral=True
            )

    @discord.ui.button(label="中止", style=discord.ButtonStyle.grey)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == all_game_info[self.id]["host"]:
            embed = discord.Embed(
                title=f"人狼ゲーム",
                description="募集が中止されました",
                color=discord.Color.red(),
            )

            await interaction.response.edit_message(embed=embed, view=None)
            del all_game_info[self.id]
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


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
@app_commands.describe(limit="人数制限")
@discord.app_commands.choices(
    limit=[discord.app_commands.Choice(name=i, value=i) for i in range(3, 16)]
)
async def werewolf(interaction: discord.Interaction, limit: int = 10):
    view = JoinView(id=interaction.id, timeout=None, limit=limit)

    game_info = {
        "host": interaction.user.id,
        "players": set(),
        "roles": {role.Werewolf(): 1},
        "limit": limit,
    }
    

    await interaction.response.defer()
    message = await interaction.followup.send(
        embed=make_participants_embed(game_info), view=view
    )
    
    game_info["message_id"] = message.id
    all_game_info[interaction.id] = game_info



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
        for game_id, game_info in all_game_info.items()
        if game_info["host"] == interaction.user.id
    ][0]

    if host_game_id:
        all_game_info[host_game_id]["roles"][role.roles[role_name]] = number
        await interaction.response.send_message(
            f"{role_name}を{number}人に設定しました", ephemeral=True
        )

        view = JoinView(
            id=host_game_id, timeout=None, limit=all_game_info[host_game_id]["limit"]
        )
        channel = client.get_channel(interaction.channel_id)
        message = await channel.fetch_message(all_game_info[host_game_id]["message_id"])
        await message.edit(
            embed=make_participants_embed(
                all_game_info[host_game_id],
            ),
            view=view
        )
    else:
        await interaction.response.send_message("ゲームが存在しません", ephemeral=True)


client.run(os.getenv("DISCORD_TOKEN"))
