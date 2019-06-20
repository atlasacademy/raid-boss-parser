import os
from datetime import datetime, timedelta
import asyncio
import pytz
import pandas as pd
import discord
# import eta

CHANNEL_ID = 581357626579746836
# CHANNEL_ID = 502556296789360640
MY_ID = 141381999674785792
OUTPUT_FILE = "https://assets.atlasacademy.io/raid_output/oni/parsed_hp.csv"
# OUTPUT_FILE = "parsed_hp.csv"
MENTIONED = "mentioned.txt"
with open("discord_api_token.txt") as f:
    discord_api_token = f.read().strip()


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f"Logged in as {client.user}")

    async def my_background_task(self):
        await self.wait_until_ready()
        myself = self.get_user(MY_ID)
        channel = self.get_channel(CHANNEL_ID)
        while not self.is_closed():
            all_df = pd.read_csv(OUTPUT_FILE, parse_dates=[0], dtype={"HP": "Int64"}, na_values=" ")
            all_df = eta.clean_data(all_df)
            # all_df["Pacific Time"] = all_df["Pacific Time"].dt.tz_localize(tz='US/Pacific')
            # last_parse = all_df.iloc[-1, 0]
            last_parse = pytz.timezone("US/Pacific").localize(all_df.iloc[-1, 0])
            now = datetime.now(tz=pytz.timezone("US/Pacific"))
            difference = now - last_parse
            print(f"{now:%Y-%m-%d %H:%M:%S} | Last parse: {difference} ago")
            if difference > timedelta(hours=1) and not os.path.exists(MENTIONED):
                await channel.send(f"{myself.mention} Last Onigashima parse was {difference} ago")
                with open(MENTIONED, "w") as file:
                    file.write("Already sent the message")
            await asyncio.sleep(300)

client = MyClient()
client.run(discord_api_token)
