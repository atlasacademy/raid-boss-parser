# from datetime import datetime
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# OUTPUT_FILE = "parsed_hp.csv"
OUTPUT_FILE = "https://assets.atlasacademy.io/raid_output/summer2/parsed_hp.csv"
ETA_HISTORY = "output/eta_history.csv"
BOSS_COLOR = {
    "Fran": "C1",
    "Helena": "C5",
    "Nito": "C0",
    "Nobu": "C2",
    "Raikou": "C3",
    "Sabers": "C4"
}
H_FMT = mdates.DateFormatter("%m/%d")


def mad(x):
    return np.median(np.abs(x - np.median(x)))


def clean_data(df, filter_window=7, filter_offset=3):
    df = df.sort_values("Pacific Time")
    df = df[df["HP"] > 1000]
    df = df.drop_duplicates(["Team", "HP"])
    df = df.dropna()
    df["Screenshot"] = df["Screenshot"].str[-14:-4]
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


def make_hp_all(boss_dict, update_time, output="hp_all.png"):
    register_matplotlib_converters()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5), dpi=200)
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        # for _ in range(5):
        #     temp_df = temp_df[temp_df["HP"] >= temp_df["HP"].shift(-1).fillna(0)]
        x = temp_df["Pacific Time"]
        y = temp_df["HP"] / 100000
        ax.plot(x, y, label=boss, marker=".", linestyle="None", color=BOSS_COLOR[boss])
    fig.autofmt_xdate()
    ax.set_title(f"NA Deadheat Summer Race distance - updated {update_time:%b %d %H:%M} PDT")
    ax.set_xlabel("Pacific Daylight Time (UTC-7)")
    # ax.xaxis.set_major_formatter(H_FMT)
    ax.set_ylabel("Distance Left (100 km)")
    # ax.set_yticklabels(['{:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
    ax.legend()
    fig.savefig(f"output/{output}", bbox_inches="tight")


def make_dps_all(boss_dict, update_time, output="dps_all.png"):
    register_matplotlib_converters()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5), dpi=200)
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        # for _ in range(5):
        #     temp_df = temp_df[temp_df["HP"] >= temp_df["HP"].shift(-1).fillna(0)]
        x = temp_df.iloc[1:, 0]
        y = temp_df["HP"].diff()[1:] / temp_df["Pacific Time"].diff().dt.total_seconds()[1:]
        y = y.rolling(7, center=True).mean()
        y = -y
        ax.plot(x, y, label=boss, marker=".", linestyle="None", color=BOSS_COLOR[boss])
    fig.autofmt_xdate()
    ax.set_title(f"NA Deadheat Summer Race speed - updated {update_time:%b %d %H:%M} PDT")
    ax.set_xlabel("Pacific Daylight Time (UTC-7)")
    # ax.xaxis.set_major_formatter(H_FMT)
    ax.set_ylabel("Speed (m/s)")
    # ax.set_yticklabels(['{:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
    ax.legend()
    fig.savefig(f"output/{output}", bbox_inches="tight")


def make_dps_all_mph(boss_dict, update_time, output="dps_all.png"):
    register_matplotlib_converters()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5), dpi=200)
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        # for _ in range(5):
        #     temp_df = temp_df[temp_df["HP"] >= temp_df["HP"].shift(-1).fillna(0)]
        x = temp_df.iloc[1:, 0]
        y = temp_df["HP"].diff()[1:] / temp_df["Pacific Time"].diff().dt.total_seconds()[1:]
        y = y.rolling(7, center=True).mean()
        y = -y * 3600 / 1609.344
        ax.plot(x, y, label=boss, marker=".", linestyle="None", color=BOSS_COLOR[boss])
    fig.autofmt_xdate()
    ax.set_title(f"NA Deadheat Summer Race speed - updated {update_time:%b %d %H:%M} PDT")
    ax.set_xlabel("Pacific Daylight Time (UTC-7)")
    # ax.xaxis.set_major_formatter(H_FMT)
    ax.set_ylabel("Speed (m/s)")
    # ax.set_yticklabels(['{:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
    ax.legend()
    fig.savefig(f"output/{output}", bbox_inches="tight")


if __name__ == "__main__":
    all_df = pd.read_csv(OUTPUT_FILE, parse_dates=[0], dtype={"HP": "Int64"})
    # all_df = clean_data(all_df)

    bosses = sorted(list(all_df["Team"].dropna().unique()))
    all_df_dict = {}
    for servant in bosses:
        all_df_dict[servant] = clean_data(all_df[all_df["Team"] == servant])
    last_record_time = all_df.iloc[-1, 0]
    make_hp_all(all_df_dict, last_record_time)
    make_dps_all(all_df_dict, last_record_time)
