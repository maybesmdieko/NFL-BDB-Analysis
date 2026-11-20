"""Run: python analyze.py --data-dir /path/to/competition/csvs
Requires Python 3.10+, pandas, numpy and matplotlib. Writes two figures beside this file.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTPUT = Path(__file__).resolve().parent
plt.rcParams.update({"svg.fonttype": "none", "svg.hashsalt": "receiver-study",
                     "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def measure_attempt(group):
    """Turn proxy for this left slant: motion downfield (+x) and inside (-y)."""
    g = group.sort_values("time")
    if len(g) < 10 or g[["x", "y", "s"]].isna().any().any():
        return None
    x, y, speed = (g[column].to_numpy() for column in ["x", "y", "s"])
    dt = pd.to_datetime(g.time).diff().dt.total_seconds().iloc[1:]
    if not np.allclose(dt, 0.1):
        return None
    # Two-frame displacement is less sensitive to jitter than a single step.
    dx = x[2:] - x[:-2]
    dy = y[2:] - y[:-2]
    angle = np.degrees(np.arctan2(-dy, dx))
    inside = (angle >= 25) & (dx > 0) & (x[1:-1] - x[0] >= 2)
    hits = np.flatnonzero(inside[:-1] & inside[1:])
    if not len(hits):
        return None
    turn = int(hits[0] + 1)
    if turn + 5 >= len(speed):
        return None
    return speed[turn + 5] - speed[turn], x - x[0], y[0] - y, turn


def sensors(folder):
    columns = ["draft_year", "nfl_id", "event_id", "entity_type", "drill_type",
               "drill_name", "time", "x", "y", "s"]
    chunks = pd.read_csv(folder / "combine_tracking.csv", usecols=columns, chunksize=100000)
    drill = pd.concat(c.query("entity_type == 'PLAYER' and drill_type == 'SKILL_DRILLS_WR' "
                              "and drill_name == 'SLANT_ROUTE_LEFT'") for c in chunks)
    records, paths = [], []
    attempts = drill.groupby(["draft_year", "nfl_id", "event_id"])
    for (year, player, _), frames in attempts:
        measured = measure_attempt(frames)
        if measured is not None:
            gain, x, y, turn = measured
            records.append((year, player, gain))
            paths.append((x, y, turn))
    print(f"Usable attempts: {len(records)}/{len(attempts)}")
    features = pd.DataFrame(records, columns=["draft_year", "nfl_id", "gain"])
    return features.groupby(["draft_year", "nfl_id"], as_index=False).gain.median(), paths


def game_routes(folder, wr):
    games = pd.read_csv(folder / "games.csv", usecols=["game_id", "season", "season_type"])
    reg = games.query("season_type == 'REG'")
    cols = ["game_id", "play_id", "nfl_id", "team_abbr", "possession_team", "route_ran",
            "team_coverage_man_zone", "play_nullified_by_penalty", "separation_at_pass_forward"]
    plays = pd.read_csv(folder / "player_play.csv", usecols=cols)
    plays = plays.merge(reg, on="game_id", validate="many_to_one").merge(
        wr[["nfl_id", "draft_year"]], on="nfl_id", validate="many_to_one")
    plays = plays.query("season == draft_year and team_abbr == possession_team and "
                        "team_coverage_man_zone == 'MAN_COVERAGE' and play_nullified_by_penalty == 'N'")
    plays = plays.dropna(subset=["route_ran", "separation_at_pass_forward"])
    plays = plays[plays.separation_at_pass_forward.ge(0)].copy()
    if plays.duplicated(["nfl_id", "game_id", "play_id"]).any():
        raise ValueError("Duplicate receiver-play records")
    # Centre separation by route type using earlier cohorts only.
    train = plays[plays.season < 2025]
    typical = train.groupby("route_ran").separation_at_pass_forward.median()
    plays["gap"] = plays.separation_at_pass_forward - plays.route_ran.map(typical)
    return plays.dropna(subset=["gap"]).groupby("nfl_id").gap.agg(
        routes="count", adjusted_gap="median").reset_index()


def forecast(train, test, features):
    def design(frame):
        return np.column_stack([np.ones(len(frame)), frame[features].to_numpy()])
    coef = np.linalg.lstsq(design(train), train.adjusted_gap, rcond=None)[0]
    return design(test) @ coef


def compare(data, minimum):
    eligible = data[data.routes >= minimum]
    train, test = eligible[eligible.draft_year < 2025], eligible[eligible.draft_year == 2025]
    if len(train) < 4 or len(test) < 2:
        raise ValueError("Insufficient eligible players")
    errors = np.array([abs(test.adjusted_gap - forecast(train, test, features)).to_numpy()
                       for features in ([], ["forty"], ["forty", "gain"])])
    difference = errors[1] - errors[2]
    rng = np.random.default_rng(2027)
    interval = np.quantile(rng.choice(difference, (5000, len(test)), replace=True).mean(axis=1),
                           [0.025, 0.975])
    print(f"{minimum} routes | train {len(train)}, test {len(test)} | "
          f"MAE {errors.mean(axis=1).round(4)} | dash minus combined "
          f"{difference.mean():+.4f}, interval {interval.round(4)}")
    return errors.mean(axis=1), len(test)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUTPUT / name, metadata={"Date": None}, bbox_inches="tight")
    plt.close(fig)


def figures(paths, scores, test_size):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for x, y, turn in paths:
        ax.plot(x[:turn + 6], y[:turn + 6], color="#64748b", alpha=.14, lw=.8)
        ax.scatter(x[turn], y[turn], s=7, color="#006761", alpha=.45)
        ax.scatter(x[turn+5], y[turn+5], s=7, color="#b84b08", alpha=.45)
    for color, label in [("#006761", "Detected turn"), ("#b84b08", "0.5 seconds later")]:
        ax.scatter([], [], color=color, label=label)
    ax.legend(frameon=False)
    ax.set(xlabel="Downfield distance from start (yards)", ylabel="Inward distance (yards)",
           title=f"Where the half-second window falls on {len(paths)} measured slants")
    ax.set_aspect("equal", adjustable="datalim")
    save(fig, "slant-window.svg")
    fig, ax = plt.subplots(figsize=(7, 3))
    labels = ["Training average", "40-yard dash", "Dash + slant speed gain"]
    bars = ax.barh(labels, scores, color=["#8998a6", "#375672", "#006761"])
    ax.invert_yaxis()
    ax.bar_label(bars, fmt="%.3f", padding=5)
    ax.set_xlim(0, max(scores)*1.22)
    ax.set(title=f"Prediction error across {test_size} rookie receivers in 2025",
           xlabel="Mean absolute error (yards per receiver; lower is better)")
    save(fig, "forecast-error.svg")


def main(folder):
    wr = pd.read_csv(folder / "combine_results.csv").query("combine_position == 'WR'")
    features, paths = sensors(folder)
    data = wr.merge(features, on=["nfl_id", "draft_year"], validate="one_to_one")
    data = data.merge(game_routes(folder, wr), on="nfl_id", validate="one_to_one").dropna(subset=["forty"])
    print(f"WRs with sensor, dash and measured NFL route: {len(data)}")
    for minimum in (10, 20, 30):
        scores, count = compare(data, minimum)
        if minimum == 20:
            figures(paths, scores, count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    main(parser.parse_args().data_dir)
