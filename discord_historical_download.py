import os
# from datetime import timezone
from datetime import datetime, timedelta
import discord
import aiohttp
import aiofiles
from rashomon_screenshot_parse import parse_screenshot

CHANNEL = "rashoumon-raid"
USER = "solution"
OUTPUT_FILE = "historical_parse.csv"
FROM_TIME = datetime(2019, 5, 23, 17)
TO_TIME = datetime(2019, 5, 23, 17, 15)
HISTORY_LIMIT = 200

client = discord.Client()

with open("discord_api_token.txt") as f:
    discord_api_token = f.read().strip()
if not os.path.exists("screenshots"):
    os.mkdir("screenshots")


async def download_raid_screenshots(time, user, url, file_name):
    print(f"{time:%Y-%m-%d %H:%M:%S}|{user}|{url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                async with aiofiles.open(f"screenshots/{file_name}", mode="wb") as file:
                    await file.write(content)
                    await file.flush()
                ocr_output = parse_screenshot(f"screenshots/{file_name}")
                # ocr_output = parse_screenshot(bytearray(content))
                with open(OUTPUT_FILE, "a") as output_text:
                    output_text.write(f"{time}, {ocr_output}, {url}\n")
                os.remove(f"screenshots/{file_name}")


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    for channel in client.get_all_channels():
        if str(channel) == CHANNEL:
            async for message in channel.history(limit=HISTORY_LIMIT):
                created_time = message.created_at + timedelta(hours=-7)
                print(created_time)
                if message.attachments and FROM_TIME <= created_time <= TO_TIME:
                    user = str(message.author.display_name)
                    file_name = f"Screenshot_{created_time:%Y%m%d-%H%M%S}.png"
                    for attachment in message.attachments:
                        await download_raid_screenshots(created_time, user, attachment.url, file_name)


client.run(discord_api_token)
