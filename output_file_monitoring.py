import asyncio
import os
from datetime import datetime  # , timedelta

import discord
# import pytz
import pandas as pd

# import eta

CHANNEL_ID = 581357626579746836  # dev-corner
# CHANNEL_ID = 502556296789360640 # bots
MY_ID = 141381999674785792
OUTPUT_FILE = "https://assets.atlasacademy.io/raid_output/summer2-2/parsed_hp.csv"
# OUTPUT_FILE = "parsed_hp.csv"
MENTIONED = "mentioned.txt"
DAY_END = {1: datetime(2019, 7, 30, 9, 22), 2: datetime(2019, 7, 31, 21, 50)}
with open("discord_api_token.txt") as f:
    discord_api_token = f.read().strip()


def check_csv(csv_file):
    df = pd.read_csv(csv_file, parse_dates=[0], dtype={"HP": "Int64"}, na_values=" ")
    # df = df[df["Pacific Time"] > DAY_END[2]]
    df = df.sort_values("Pacific Time")
    df = df[df["HP"] < 1000]
    df = df.dropna()

    mentioned_hp = []
    if os.path.exists(MENTIONED):
        with open(MENTIONED, "r", encoding="utf-8") as file:
            mentioned_hp = file.readlines()
    mentioned_hp = [int(hp.strip()) for hp in mentioned_hp]
    if mentioned_hp:
        for hp in mentioned_hp:
            df = df[df["HP"] != hp]

    bosses = sorted(list(df["Team"].dropna().unique()))
    all_df_dict = {servant: df[df["Team"] == servant] for servant in bosses}
    last_hp = [all_df_dict[servant]["HP"].iloc[-1] for servant in all_df_dict]
    last_hp = list(set(last_hp))
    print(last_hp)
    if len(last_hp) == 1:
        hp = last_hp[0]
        print(f"All team stopped at {hp}.")
        return hp


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def my_background_task(self):
        await self.wait_until_ready()
        myself = self.get_user(MY_ID)
        channel = self.get_channel(CHANNEL_ID)
        while not self.is_closed():
            hp = check_csv(OUTPUT_FILE)
            if hp:
                await channel.send(f"{myself.mention} All teams stopped at {hp}.")
                with open(MENTIONED, "a", encoding="utf-8") as file:
                    file.write(f"{hp}\n")
            await asyncio.sleep(300)


if __name__ == "__main__":
    # client = MyClient()
    # client.run(discord_api_token)
    check_csv(OUTPUT_FILE)
