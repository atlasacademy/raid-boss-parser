import os
import re
# import subprocess
from datetime import datetime
import pandas as pd
import pandas.plotting._converter as pandacnv
import matplotlib.pyplot as plt
from rashomon_screenshot_parse import parse_screenshot

HP = 60000000


# atlasacademy/capy-drop-parser/fgo_mat_counter.py
def get_qp_from_text(text):
    qp = 0
    power = 1
    # re matches left to right so reverse the list to process lower orders of magnitude first.
    for match in re.findall('[0-9]+', text)[::-1]:
        qp += int(match) * power
        power *= 1000

    return qp


if os.path.exists("manual_data.csv"):
    manual_data = pd.read_csv("manual_data.csv", parse_dates=["Time"])

dict_df = {"File": [], "Time": [], "Kills": []}

file_list = os.listdir(f"screenshots")
file_list = [f for f in file_list if f.lower().endswith(".jpg") or f.lower().endswith(".png")]

for file in file_list:
    time = file[11:26]
    time = datetime.strptime(time, "%Y%m%d-%H%M%S")

    path = f"screenshots/{file}"
    ocr = parse_screenshot(path)

    if ocr != 0:
        dict_df["Time"].append(time)
        dict_df["Kills"].append(ocr)
        dict_df["File"].append(file)
    if ocr == 0:
        if manual_data is not None and file not in list(manual_data["File"]):
            print(f"{file},{time}")

df = pd.DataFrame.from_dict(dict_df)
df = df.sort_values("Time")
df.to_csv("parsed_data.csv", index=False)

if manual_data is not None:
    raid_data = pd.concat([manual_data, df])
else:
    raid_data = df
raid_data = raid_data.drop_duplicates("Time").sort_values("Time")

# Increasing kill count only
for _ in range(10):
    raid_data = raid_data[raid_data["Kills"] > raid_data["Kills"].shift(1).fillna(0)]

x = raid_data["Time"][1:]
y = raid_data["Kills"].diff()[1:] / raid_data['Time'].diff().dt.total_seconds()[1:]
x = x[1:-1]
y = y.rolling(3, center=True).mean()[1:-1]

pandacnv.register()
plt.style.use('seaborn')
fig1, ax1 = plt.subplots(figsize=(14, 7.5))
ax1.plot(x, y)
fig1.autofmt_xdate()
update_time = x.iloc[-1]
ax1.set_title(f"MA Rashomon rerun raid - updated {update_time:%Y-%m-%d %H:%M} PDT")
ax1.set_xlabel("Japan Standard Time")
ax1.set_ylabel("Kills per Second")
file_name = "chart.png"
fig1.savefig(file_name, dpi=200, bbox_inches='tight')
# with open(os.devnull, "w") as f:
#     subprocess.call(["/usr/local/bin/ect", file_name], stdout=f)

x = raid_data["Time"]
y = raid_data["Kills"] / 1000000
fig2, ax2 = plt.subplots(figsize=(14, 7.5))
ax2.plot(x, y)
fig2.autofmt_xdate()
update_time = x.iloc[-1]
ax2.set_title(f"NA Rashomon rerun raid - updated {update_time:%Y-%m-%d %H:%M} PDT")
ax2.set_xlabel("Japan Standard Time")
ax2.set_ylabel("Kills Count (millions)")
file_name = "kills_count.png"
fig2.savefig(file_name, dpi=200, bbox_inches='tight')
# with open(os.devnull, "w") as f:
#     subprocess.call(["/usr/local/bin/ect", file_name], stdout=f)

avg_rate = raid_data["Kills"].iloc[-1] / (raid_data["Time"].iloc[-1] - raid_data["Time"].iloc[0]).total_seconds()
time_to_kill = (HP - raid_data["Kills"].iloc[-1]) / avg_rate
time_to_kill = pd.to_timedelta(time_to_kill, unit='s')

print(f"Time to death: {time_to_kill}")
with open("time_to_complete.txt", "w") as f:
    f.write(str(time_to_kill))
