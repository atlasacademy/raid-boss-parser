from datetime import datetime
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import matplotlib.pyplot as plt

# OUTPUT_FILE = "output/parsed_hp.csv"
OUTPUT_FILE = "https://assets.atlasacademy.io/raid_output/apo/parsed_hp.csv"
BOSS_COLOR = {
    "Astolfo": "C0",
    "Atalante": "C1",
    "Avicebron": "C2",
    "Frankenstein": "C3",
    "Jack": "C4",
    "Karna": "C5",
    "Mordred": "C6",
    "Semiramis": "C7",
    "Siegfried": "C8",
    "Spartacus": "C9",
    "Vlad III": "r",
    "William Shakespeare": "g"
}
TODAY = 7


def mad(x):
    return np.median(np.abs(x - np.median(x)))


def clean_data(df, filter_window=7, filter_offset=3):
    df.columns = df.columns.str.strip()
    df = df.dropna()
    df = df.sort_values(df.columns[0])
    rolling_median = (
        df.iloc[:, 2]
        .rolling(filter_window, center=True)
        .median()
        .fillna(method="ffill")
        .fillna(method="bfill")
        .fillna(0)
    )
    rolling_mad = (
        df.iloc[:, 2]
        .rolling(filter_window, center=True)
        .apply(mad, raw=True)
        .fillna(method="ffill")
        .fillna(method="bfill")
        .fillna(0)
    )
    lower_bound = rolling_median - filter_offset * rolling_mad
    upper_bound = rolling_median + filter_offset * rolling_mad
    index = (lower_bound <= df.iloc[:, 2]) & (df.iloc[:, 2] <= upper_bound)
    df = df[index]
    return df


def calculate_eta(df, average=200, output="eta.txt"):
    df = df.iloc[-1 * average - 1 :, :2]
    avg_rate = -(df.iloc[-1, 1] - df.iloc[0, 1]) / (df.iloc[-1, 0] - df.iloc[0, 0]).total_seconds()
    remaining_time = df.iloc[-1, 1] / avg_rate
    remaining_time = pd.to_timedelta(remaining_time, unit="s")
    eta = df.iloc[-1, 0] + remaining_time
    with open(output, "w") as f:
        f.write(f"Average DPS: {avg_rate:,.0f}\n")
        f.write(f"Remaining Time: {remaining_time}\n")
        f.write(f"ETA: {eta:%Y-%m-%d %H:%M:%S} PST\n")
    return avg_rate, eta, remaining_time


def make_hp_chart(df, day, output="hp.png"):
    x = df.iloc[:, 0]
    y = df.iloc[:, 1] / 1000000000000
    register_matplotlib_converters()
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
    y = df.iloc[:, 1].diff()[1:] / df.iloc[:, 0].diff().dt.total_seconds()[1:]
    x = x[y <= 0]
    y = y[y <= 0]
    y = y.rolling(4, center=True).mean()
    y = -y/1000000
    register_matplotlib_converters()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    ax.plot(x, y, color=BOSS_COLOR[day], marker='o', markersize=3, linestyle="None")
    fig.autofmt_xdate()
    update_time = x.iloc[-1]
    ax.set_title(f"Day {day} NA Rashomon raid DPS - updated {update_time:%Y-%m-%d %H:%M} PST")
    ax.set_xlabel("Pacific Standard Time")
    ax.set_ylabel("DPS (millions)")
    fig.savefig(output, dpi=200, bbox_inches='tight')


def make_hp_all(boss_dict, output="hp_all.png"):
    register_matplotlib_converters()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    update_time = datetime(2019, 1, 1)
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df.iloc[:, 2] >= temp_df.iloc[:, 2].shift(-1).fillna(0)]
        x = temp_df.iloc[:, 0]
        if x.iloc[-1] > update_time:
            update_time = x.iloc[-1]
        y = temp_df.iloc[:, 2] / 1000
        ax.plot(x, y, label=boss, color=BOSS_COLOR[boss])
    fig.autofmt_xdate()
    ax.set_title(f"CN Apocrypha raid HP - updated {update_time:%Y-%m-%d %H:%M} GMT+8")
    ax.set_xlabel("China Standard Time (GMT+8)")
    ax.set_ylabel("HP (thousands)")
    ax.set_yticklabels(['{:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
    ax.legend()
    fig.savefig(output, dpi=200, bbox_inches='tight')


def make_dps_all(boss_dict, output="dps_all.png", stacked=False):
    register_matplotlib_converters()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    update_time = datetime(2019, 1, 1)
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df.iloc[:, 2] >= temp_df.iloc[:, 2].shift(-1).fillna(0)]
        x = temp_df.iloc[1:, 0]
        y = temp_df.iloc[:, 2].diff()[1:] / temp_df.iloc[:, 0].diff().dt.total_seconds()[1:]
        x = x[y <= 0]
        y = y[y <= 0]
        y = y.rolling(4, center=True).mean()
        y = -y
        if x.iloc[-1] > update_time:
            update_time = x.iloc[-1]
        ax.plot(x, y, label=boss, color=BOSS_COLOR[boss], marker='o', markersize=3, linestyle="None")
    fig.autofmt_xdate()
    ax.set_title(f"CN Apocrypha raid KPS - updated {update_time:%Y-%m-%d %H:%M} GMT+8")
    ax.set_xlabel("China Standard Time (GMT+8)")
    ax.set_ylabel("KPS")
    ax.legend()
    fig.savefig(output, dpi=200, bbox_inches='tight')


if __name__ == "__main__":
    all_df = pd.read_csv(OUTPUT_FILE, parse_dates=[0], dtype={"HP": "Int64"}, na_values=" ")
    bosses = sorted(list(all_df["Boss"].dropna().unique()))
    all_df_dict = {}
    for servant in bosses:
        all_df_dict[servant] = clean_data(all_df[all_df["Boss"] == servant])
    make_hp_all(all_df_dict)
    make_dps_all(all_df_dict)
