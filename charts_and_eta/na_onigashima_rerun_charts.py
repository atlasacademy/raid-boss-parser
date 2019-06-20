from datetime import datetime
import numpy as np
import pandas as pd
import pandas.plotting._converter as pandacnv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# OUTPUT_FILE = "parsed_hp.csv"
OUTPUT_FILE = "https://assets.atlasacademy.io/raid_output/oni/parsed_hp.csv"
BOSS_NAME = {
    0: "1st Gate: Kazakoemaru",
    1: "2nd Gate: Wazahamimaru",
    2: "3rd Gate: Gorikimaru",
    3: "Summit: Ushi Gozen",
    4: "Return: Kazakoemaru",
    5: "Return: Wazahamimaru",
    6: "Return: Gorikimaru"
}
BOSS_COLOR = {
    0: "C1",
    1: "C0",
    2: "C2",
    3: "C3",
    4: "C1",
    5: "C0",
    6: "C2"
}
BOSS_linestyle = {b: "-" if b <= 3 else "--" for b in range(len(BOSS_NAME))}
BOSS_marker = {b: "o" if b <= 3 else "^" for b in range(len(BOSS_NAME))}
BOSS_START_TIME = {
    0: "2019-06-06 00:00:00",
    1: "2019-06-06 18:14:53",
    2: "2019-06-08 00:00:27",
    3: "2019-06-09 05:52:52",
    4: "2019-06-11 17:00:00",
    5: "2019-06-14 17:00:00",
    6: "2019-06-17 17:00:00"
}
BOSS_START_TIME = {boss: datetime.strptime(time, "%Y-%m-%d %H:%M:%S") for boss, time in BOSS_START_TIME.items()}
ETA_HISTORY = "output/eta_history.csv"
H_FMT = mdates.DateFormatter("%m/%d")


def mad(x):
    return np.median(np.abs(x - np.median(x)))


def clean_data(df, filter_window=7, filter_offset=3):
    df.columns = df.columns.str.strip()
    df = df.dropna()
    df = df.sort_values("Pacific Time")
    rolling_median = (
        df["HP"]
        .rolling(filter_window, center=True)
        .median()
        .fillna(method="ffill")
        .fillna(method="bfill")
        .fillna(0)
    )
    rolling_mad = (
        df["HP"]
        .rolling(filter_window, center=True)
        .apply(mad, raw=True)
        .fillna(method="ffill")
        .fillna(method="bfill")
        .fillna(0)
    )
    lower_bound = rolling_median - filter_offset * rolling_mad
    upper_bound = rolling_median + filter_offset * rolling_mad
    index = (lower_bound <= df["HP"]) & (df["HP"] <= upper_bound)
    df = df[index]
    df = df[df.iloc[:, 1] != 3]
    return df


def calculate_eta(df, update_time, average=1000, output="eta.txt"):
    df = df.iloc[-1 * average - 1:, :2]
    avg_rate = -(df.iloc[-1, 1] - df.iloc[0, 1]) / (df.iloc[-1, 0] - df.iloc[0, 0]).total_seconds()
    remaining_time = df.iloc[-1, 1] / avg_rate
    remaining_time = pd.to_timedelta(remaining_time, unit="s")
    eta = df.iloc[-1, 0] + remaining_time
    # DPS and ETD for solution's site
    with open(f"output/{output}", "w") as f:
        f.write(f"DPS: {avg_rate:.0f}\n")
        f.write(f"ETA: {eta:%Y-%m-%d %H:%M:%S} PDT\n")
    with open(ETA_HISTORY, "a") as f:
        f.write(f"{update_time:%Y-%m-%d %H:%M:%S},{eta:%Y-%m-%d %H:%M:%S}\n")
    return avg_rate, eta, remaining_time


def make_hp_chart(df, day, output="hp.png"):
    x = df["Pacific Time"]
    y = df["HP"] / 1000000000000
    pandacnv.register()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    ax.plot(x, y, color=BOSS_COLOR[day])
    fig.autofmt_xdate()
    update_time = x.iloc[-1]
    ax.set_title(f"Day {day} NA Rashomon raid HP - updated {update_time:%Y-%m-%d %H:%M} PST")
    ax.set_xlabel("Pacific Standard Time")
    ax.set_ylabel("HP (trillions)")
    fig.savefig(output, dpi=200, bbox_inches='tight')


def make_dps_chart(df, day, output="dps.png"):
    x = df.iloc[1:, 0]
    y = df["HP"].diff()[1:] / df["Pacific Time"].diff().dt.total_seconds()[1:]
    x = x[y <= 0]
    y = y[y <= 0]
    y = y.rolling(4, center=True).mean()
    y = -y / 1000000
    pandacnv.register()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    ax.plot(x, y, color=BOSS_COLOR[day], marker='o', markersize=3, linestyle="None")
    fig.autofmt_xdate()
    update_time = x.iloc[-1]
    ax.set_title(f"Day {day} NA Rashomon raid DPS - updated {update_time:%Y-%m-%d %H:%M} PST")
    ax.set_xlabel("Pacific Standard Time")
    ax.set_ylabel("DPS (millions)")
    fig.savefig(output, dpi=200, bbox_inches='tight')


def make_hp_all(boss_dict, update_time, output="hp_all.png", stacked=False):
    pandacnv.register()
    plt.style.use('seaborn')
    if stacked:
        fig, ax = plt.subplots(figsize=(14, 7.5), dpi=200)
    else:
        fig, ax = plt.subplots(figsize=(17, 7.5), dpi=200)
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df["HP"] >= temp_df["HP"].shift(-1).fillna(0)]
        x = temp_df["Pacific Time"]
        if stacked:
            if boss in BOSS_START_TIME.keys():
                x = x - BOSS_START_TIME[boss]
            else:
                x = x - x.iloc[0]
            x = x.dt.total_seconds() / 3600
        y = temp_df["HP"] / (10**12)
        ax.plot(x, y, label=BOSS_NAME[boss], color=BOSS_COLOR[boss], linestyle=BOSS_linestyle[boss])
    fig.autofmt_xdate()
    ax.set_title(f"NA Onigashima rerun raid HP - updated {update_time:%b %d %H:%M} PDT")
    if stacked:
        ax.set_xlabel("Time since raid started (hours)")
    else:
        ax.set_xlabel("Pacific Daylight Time (UTC-7)")
        ax.xaxis.set_major_formatter(H_FMT)
    ax.set_ylabel("HP (trillions)")
    # ax.set_yticklabels(['{:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
    ax.legend()
    fig.savefig(f"output/{output}", bbox_inches="tight")


def make_dps_all(boss_dict, update_time, output="dps_all.png", stacked=False):
    pandacnv.register()
    plt.style.use('seaborn')
    if stacked:
        fig, ax = plt.subplots(figsize=(14, 7.5), dpi=200)
    else:
        fig, ax = plt.subplots(figsize=(17, 7.5), dpi=200)
    max_y = 0
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df["HP"] > temp_df["HP"].shift(-1).fillna(0)]
        x = temp_df.iloc[1:, 0]
        y = temp_df["HP"].diff()[1:] / temp_df["Pacific Time"].diff().dt.total_seconds()[1:]
        y = y.rolling(4, center=True).mean()
        y = -y / 1000000
        if y.max(skipna=True) > max_y:
            max_y = y.max(skipna=True)
        if stacked:
            if boss in BOSS_START_TIME.keys():
                x = x - BOSS_START_TIME[boss]
            else:
                x = x - x.iloc[0]
            x = x.dt.total_seconds() / 3600
        ax.plot(x, y, label=BOSS_NAME[boss], color=BOSS_COLOR[boss], marker=BOSS_marker[boss], markersize=4, linestyle="None")
    fig.autofmt_xdate()
    ax.set_title(f"NA Onigashima rerun raid DPS - updated {update_time:%b %d %H:%M} PDT")
    if stacked:
        ax.set_xlabel("Time since raid started (hours)")
    else:
        ax.set_xlabel("Pacific Daylight Time (UTC-7)")
        ax.xaxis.set_major_formatter(H_FMT)
    ax.set_ylim(-10, 1.1 * max_y)
    ax.set_ylabel("DPS (millions)")
    ax.legend()
    fig.savefig(f"output/{output}", bbox_inches="tight")


if __name__ == "__main__":
    all_df = pd.read_csv(OUTPUT_FILE, parse_dates=[0], dtype={"HP": "Int64"}, na_values=" ")
    all_df = clean_data(all_df)

    all_df_dict = {}
    raid_start_times = list(all_df["Pacific Time"][all_df["HP"].diff() > 5 * 10**12])
    if not raid_start_times:
        all_df_dict[0] = all_df
        current_boss = 0
    else:
        all_df_dict[0] = all_df[all_df["Pacific Time"] < raid_start_times[0]]
        for i in range(0, len(raid_start_times) - 1):
            from_time = raid_start_times[i]
            end_time = raid_start_times[i + 1]
            all_df_dict[i+1] = all_df[(all_df["Pacific Time"] >= from_time) & (all_df["Pacific Time"] < end_time)]
        current_boss = len(raid_start_times)
        all_df_dict[current_boss] = all_df[all_df["Pacific Time"] >= raid_start_times[-1]]

    for bo in all_df_dict:
        print(f"{bo} {all_df_dict[bo].iloc[0, 1]} {len(all_df_dict[bo]):4d} {all_df_dict[bo].iloc[0, 0]} {all_df_dict[bo].iloc[-1, 0]}")

    last_record_time = all_df.iloc[-1, 0]
    calculate_eta(all_df_dict[current_boss], last_record_time)
    make_hp_all(all_df_dict, last_record_time)
    make_hp_all(all_df_dict, last_record_time, "hp_all_stacked.png", True)
    make_dps_all(all_df_dict, last_record_time)
    make_dps_all(all_df_dict, last_record_time, "dps_all_stacked.png", True)
    # BOSS_HP = {
    #     0: 11.8,
    #     1: 15.8,
    #     2: 19.8,
    #     3: 36.8,
    #     4: 20,
    #     5: 20
    # }
    # for CHOSEN_BOSS in range(5, 6):
    #     print(CHOSEN_BOSS)
    #     test_df = all_df_dict[CHOSEN_BOSS]
    #     avg_rate = -(test_df.iloc[-1, 1] - test_df.iloc[0, 1]) / (test_df.iloc[-1, 0] - test_df.iloc[0, 0]).total_seconds()
    #     MAX_HP = BOSS_HP[CHOSEN_BOSS]*10**12
    #     total_run_time = MAX_HP / avg_rate
    #     print(total_run_time)
    #     total_run_time = pd.to_timedelta(total_run_time, unit="s")
    #     print(total_run_time)
    #     run_time = (MAX_HP - test_df.iloc[-1, 1]) / avg_rate
    #     run_time = pd.to_timedelta(run_time, unit="s")
    #     start_time = test_df.iloc[-1, 0] - run_time
    #     print(start_time)
