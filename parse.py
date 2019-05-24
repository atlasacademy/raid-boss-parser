import os
from datetime import datetime, timedelta
import rashomon_screenshot_parse

LAST_PARSED_FILE = "output/last_parsed"
OUTPUT_FILE = "output/parsed_hp.csv"

if __name__ == "__main__":
    last_parsed = 0
    if os.path.isfile(LAST_PARSED_FILE):
        last_parsed = int(open(LAST_PARSED_FILE, "r").read())

    for file in sorted(os.listdir("input")):
        if not file.endswith(".png"):
            continue

        created_timestamp = os.path.basename(file).split(".")[0]
        if not int(created_timestamp) > last_parsed:
            continue

        result = rashomon_screenshot_parse.parse_screenshot("input/" + file)
        created_time = datetime.utcfromtimestamp(int(created_timestamp)) + timedelta(hours=-7)
        with open(OUTPUT_FILE, "a") as f:
            f.write(f"{created_time}, {result}, {file}\n")

        with open(LAST_PARSED_FILE, "w+") as f:
            f.write(f"{created_timestamp}")

        print(f"{file} {result}")
