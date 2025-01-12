from dataclasses import dataclass
import os

import discord
from discord import app_commands

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print("ログインしました")


def make_participants_embed(participants: dict, limit: int):
    embed = discord.Embed(
        title=f"人狼ゲーム({len(participants['players']) + 1}/{limit})",
        description=f"募集者:<@!{participants['host']}>",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="参加者",
        value="\n".join([f"<@!{player}>" for player in participants["players"]])
        or "なし",
    )
    return embed


game_participants = {}


class JoinView(discord.ui.View):
    def __init__(self, id, timeout=180, limit=10):
        super().__init__(timeout=timeout)
        self.id = id
        self.limit = limit

    @discord.ui.button(label="開始", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == game_participants[self.id]["host"]:
            pass
        else:
            await interaction.response.send_message(
                "あなたは募集者ではありません", ephemeral=True
            )

    @discord.ui.button(label="中止", style=discord.ButtonStyle.grey)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == game_participants[self.id]["host"]:
            embed = discord.Embed(
                title=f"人狼ゲーム",
                description="募集が中止されました",
                color=discord.Color.red(),
            )

            await interaction.response.edit_message(embed=embed, view=None)
            del game_participants[self.id]
        else:
            await interaction.response.send_message(
                "あなたは募集者ではありません", ephemeral=True
            )

    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in game_participants[self.id]["players"]:
            if len(game_participants[self.id]["players"]) + 1 >= self.limit:
                await interaction.response.send_message(
                    "人数制限に達しました", ephemeral=True
                )
                return

            if interaction.user.id != game_participants[self.id]["host"]:
                game_participants[self.id]["players"].add(interaction.user.id)

            await interaction.response.edit_message(
                embed=make_participants_embed(game_participants[self.id], self.limit),
                view=self,
            )
        else:
            await interaction.response.send_message(
                "すでに参加しています", ephemeral=True
            )

    @discord.ui.button(label="退出", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in game_participants[self.id]["players"]:
            if interaction.user.id != game_participants[self.id]["host"]:
                game_participants[self.id]["players"].remove(interaction.user.id)

            await interaction.response.edit_message(
                embed=make_participants_embed(game_participants[self.id], self.limit),
                view=self,
            )
        elif interaction.user.id == game_participants[self.id]["host"]:
            await interaction.response.send_message(
                "募集者は退出できません", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "あなたは参加していません", ephemeral=True
            )


@tree.command(name="werewolf", description="人狼ゲームをプレイします")
@app_commands.describe(limit="人数制限")
async def werewolf(interaction: discord.Interaction, limit: int = 10):
    view = JoinView(id=interaction.id, timeout=None, limit=limit)

    participants = {"host": interaction.user.id, "players": set()}
    game_participants[interaction.id] = participants

    await interaction.response.defer()
    await interaction.followup.send(
        embed=make_participants_embed(participants, limit), view=view
    )


client.run(os.getenv("DISCORD_TOKEN"))
