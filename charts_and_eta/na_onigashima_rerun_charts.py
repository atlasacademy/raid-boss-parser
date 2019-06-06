import numpy as np
import pandas as pd
import pandas.plotting._converter as pandacnv
import matplotlib.pyplot as plt

# OUTPUT_FILE = "output/rashomon_parsed_hp.csv"
OUTPUT_FILE = "https://assets.atlasacademy.io/raid_output/oni/parsed_hp.csv"
BOSS_NAME = {
    0: "1st Gate: Kazakoemaru",
    1: "2nd Gate: Wazahamimaru",
    2: "3rd Gate: Gorikimaru",
    3: "Summit: Ushi Gozen"
}
BOSS_COLOR = {
    i: f"C{i}" for i in range(len(BOSS_NAME))
}


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
    return df


def calculate_eta(df, average=200, output="eta.txt"):
    df = df.iloc[-1 * average - 1 :, :2]
    avg_rate = -(df.iloc[-1, 1] - df.iloc[0, 1]) / (df.iloc[-1, 0] - df.iloc[0, 0]).total_seconds()
    remaining_time = df.iloc[-1, 1] / avg_rate
    remaining_time = pd.to_timedelta(remaining_time, unit="s")
    eta = df.iloc[-1, 0] + remaining_time
    # DPS and ETD for solution's site
    with open(f"output/{output}", "w") as f:
        f.write(f"DPS: {avg_rate:.0f}\n")
        f.write(f"ETA: {eta:%Y-%m-%d %H:%M:%S} UTC-7\n")
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
    y = -y/1000000
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
    fig, ax = plt.subplots(figsize=(14, 7.5))
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df["HP"] >= temp_df["HP"].shift(-1).fillna(0)]
        x = temp_df["Pacific Time"]
        if stacked:
            x = x - x.iloc[0]
            x = x.dt.total_seconds() / 3600
        y = temp_df["HP"] / (10**12)
        ax.plot(x, y, label=BOSS_NAME[boss], color=BOSS_COLOR[boss])
    fig.autofmt_xdate()
    ax.set_title(f"NA Onigashima rerun raid HP - updated {update_time:%b-%d %H:%M} PDT")
    if stacked:
        ax.set_xlabel("Time since raid started (hours)")
    else:
        ax.set_xlabel("Pacific Daylight Time (UTC-7)")
    ax.set_ylabel("HP (trillions)")
    # ax.set_yticklabels(['{:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
    ax.legend()
    fig.savefig(f"output/{output}", dpi=200, bbox_inches='tight')


def make_dps_all(boss_dict, update_time, output="dps_all.png", stacked=False):
    pandacnv.register()
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    for boss in boss_dict:
        temp_df = boss_dict[boss]
        # Decreasing HP only
        for _ in range(5):
            temp_df = temp_df[temp_df["HP"] >= temp_df["HP"].shift(-1).fillna(0)]
        x = temp_df.iloc[1:, 0]
        y = temp_df["HP"].diff()[1:] / temp_df["Pacific Time"].diff().dt.total_seconds()[1:]
        # x = x[y <= 0]
        # y = y[y <= 0]
        y = y.rolling(4, center=True).mean()
        y = -y / 1000000
        if stacked:
            x = x - x.iloc[0]
            x = x.dt.total_seconds() / 3600
        ax.plot(x, y, label=BOSS_NAME[boss], color=BOSS_COLOR[boss], marker='o', markersize=3, linestyle="None")
    fig.autofmt_xdate()
    ax.set_title(f"NA Onigashima rerun raid DPS - updated {update_time:%b-%d %H:%M} PDT")
    if stacked:
        ax.set_xlabel("Time since raid started (hours)")
    else:
        ax.set_xlabel("Pacific Daylight Time (UTC-7)")
    ax.set_ylabel("DPS (millions)")
    ax.legend()
    fig.savefig(f"output/{output}", dpi=200, bbox_inches='tight')


if __name__ == "__main__":
    all_df = pd.read_csv(OUTPUT_FILE, parse_dates=[0], dtype={"HP": "Int64"}, na_values=" ")
    all_df = clean_data(all_df)
    all_df.to_csv("cleaned.csv", index=False)

    all_df_dict = {}
    raid_start_times = list(all_df["Pacific Time"][all_df["HP"].diff() > 5*10**12])
    for i in range(len(raid_start_times) - 1):
        from_time = raid_start_times[i]
        end_time = raid_start_times[i+1]
        all_df_dict[i] = all_df[(all_df["Pacific Time"] >= from_time) & (all_df["Pacific Time"] < end_time)]
    current_boss = len(raid_start_times) - 1
    all_df_dict[current_boss] = all_df[all_df["Pacific Time"] >= raid_start_times[-1]]

    # for boss in all_df_dict:
    #     print(boss, len(all_df_dict[boss]), all_df_dict[boss].iloc[0, 0], all_df_dict[boss].iloc[-1, 0])

    calculate_eta(all_df_dict[current_boss])

    last_record_time = all_df.iloc[-1, 0]
    make_hp_all(all_df_dict, last_record_time)
    make_hp_all(all_df_dict, last_record_time, "hp_all_stacked.png", True)
    make_dps_all(all_df_dict, last_record_time)
    make_dps_all(all_df_dict, last_record_time, "dps_all_stacked.png", True)
