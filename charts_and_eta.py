from datetime import datetime
import numpy as np
import pandas as pd
import pandas.plotting._converter as pandacnv
import matplotlib.pyplot as plt

# OUTPUT_FILE = "output/parsed_hp.csv"
OUTPUT_FILE = "https://assets.atlasacademy.io/raid_output/parsed_hp.csv"
DAY_COLOR = {
    2: '#d62728',
    3: '#9467bd',
    4: '#1f77b4',
    5: '#ff7f0e',
    6: '#bcbd22',
    7: '#7f7f7f',
    1: '#e377c2'
}


def mad(x):
    return np.median(np.abs(x - np.median(x)))


def import_data(csv_file, filter_window=7, filter_offset=3):
    df = pd.read_csv(csv_file, parse_dates=[0], dtype={1: "Int64"}, na_values=" ")
    df.columns = df.columns.str.strip()
    df = df.dropna()
    df = df.sort_values(df.columns[0])
    rolling_median = (
        df.iloc[:, 1]
        .rolling(filter_window, center=True)
        .median()
        .fillna(method="ffill")
        .fillna(0)
    )
    rolling_mad = (
        df.iloc[:, 1]
        .rolling(filter_window, center=True)
        .apply(mad, raw=True)
        .fillna(method="ffill")
        .fillna(0)
    )
    lower_bound = rolling_median - filter_offset * rolling_mad
    upper_bound = rolling_median + filter_offset * rolling_mad
    index = (lower_bound <= df.iloc[:, 1]) & (df.iloc[:, 1] <= upper_bound)
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
    pandacnv.register()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    ax.plot(x, y, color=DAY_COLOR[day])
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
    pandacnv.register()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    ax.plot(x, y, color=DAY_COLOR[day], marker='o', markersize=3, linestyle="None")
    fig.autofmt_xdate()
    update_time = x.iloc[-1]
    ax.set_title(f"Day {day} NA Rashomon raid DPS - updated {update_time:%Y-%m-%d %H:%M} PST")
    ax.set_xlabel("Pacific Standard Time")
    ax.set_ylabel("DPS (millions)")
    fig.savefig(output, dpi=200, bbox_inches='tight')


def make_hp_all(df, output="hp_all.png", stacked=False):
    pandacnv.register()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    update_time = datetime(2019, 1, 1)
    for day in range(2, 7):
        temp_idx = (df.iloc[:, 0] > datetime(2019, 5, 21 + day, 17, 1)) \
                & (df.iloc[:, 0] < datetime(2019, 5, 21 + day + 1, 17, 1))
        temp_df = df[temp_idx]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df.iloc[:, 1] >= temp_df.iloc[:, 1].shift(-1).fillna(0)]
        x = temp_df.iloc[:, 0]
        if x.iloc[-1] > update_time:
            update_time = x.iloc[-1]
        if stacked:
            x = x - datetime(2019, 5, 21 + day, 17)
            x = x.dt.total_seconds() / 3600
        y = temp_df.iloc[:, 1] / 1000000000000
        ax.plot(x, y, label=f"Day {day}", color=DAY_COLOR[day])
    fig.autofmt_xdate()
    ax.set_title(f"NA Rashomon raid HP - updated {update_time:%Y-%m-%d %H:%M} PST")
    if stacked:
        ax.set_xlabel("Time since day start (hours)")
    else:
        ax.set_xlabel("Pacific Standard Time")
    ax.set_ylabel("HP (trillions)")
    ax.legend()
    fig.savefig(output, dpi=200, bbox_inches='tight')


def make_dps_all(df, output="dps_all.png", stacked=False):
    pandacnv.register()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    update_time = datetime(2019, 1, 1)
    for day in range(2, 7):
        temp_idx = (df.iloc[:, 0] > datetime(2019, 5, 21 + day, 17, 1)) \
                & (df.iloc[:, 0] < datetime(2019, 5, 21 + day + 1, 17, 1))
        temp_df = df[temp_idx]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df.iloc[:, 1] >= temp_df.iloc[:, 1].shift(-1).fillna(0)]
        x = temp_df.iloc[1:, 0]
        y = temp_df.iloc[:, 1].diff()[1:] / temp_df.iloc[:, 0].diff().dt.total_seconds()[1:]
        x = x[y <= 0]
        y = y[y <= 0]
        y = y.rolling(4, center=True).mean()
        y = -y/1000000
        if x.iloc[-1] > update_time:
            update_time = x.iloc[-1]
        if stacked:
            x = x - datetime(2019, 5, 21 + day, 17)
            x = x.dt.total_seconds() / 3600
        ax.plot(x, y, label=f"Day {day}", color=DAY_COLOR[day], marker='o', markersize=3, linestyle="None")
    fig.autofmt_xdate()
    ax.set_title(f"NA Rashomon raid DPS - updated {update_time:%Y-%m-%d %H:%M} PST")
    if not stacked:
        ax.set_xlabel("Time since day start (hours)")
    else:
        ax.set_xlabel("Pacific Standard Time")
    ax.set_ylabel("DPS (millions)")
    ax.legend()
    fig.savefig(output, dpi=200, bbox_inches='tight')


if __name__ == "__main__":
    data = import_data(OUTPUT_FILE)
    make_hp_all(data)
    make_hp_all(data, "hp_all_stacked.png", stacked=True)
    make_dps_all(data)
    make_dps_all(data, "dps_all_stacked.png", stacked=True)
    event_day = 6
    # for event_day in range(2, 6):
    idx = (data.iloc[:, 0] > datetime(2019, 5, 21 + event_day, 17, 1)) \
            & (data.iloc[:, 0] < datetime(2019, 5, 21 + event_day + 1, 17, 1))
    day_data = data[idx]
    # Decreasing HP only
    for _ in range(5):
        day_data = day_data[day_data.iloc[:, 1] >= day_data.iloc[:, 1].shift(-1).fillna(0)]
    rate, time_finish, time_left = calculate_eta(day_data)
    make_hp_chart(day_data, event_day, f"hp_day_{event_day}.png")
    make_dps_chart(day_data, event_day, f"dps_day_{event_day}.png")
