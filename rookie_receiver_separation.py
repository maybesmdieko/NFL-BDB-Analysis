"""Does combine sprint speed help predict rookie receiver separation?

Data: 2027 NFL Big Data Bowl (https://www.kaggle.com/competitions/nfl-big-data-bowl-2027).
Place combine_results.csv, games.csv and player_play.csv beside this script.
Run: python3 rookie_receiver_separation.py
Alternatively: python3 rookie_receiver_separation.py --data-dir "/path/to/csvs"
Python 3.9+; standard library only. The large play file is read one row at a time.

Outcome: a player's median separation at pass release on eligible rookie routes
against man coverage. Each receiver contributes one observation. Using a median
limits the influence of occasional wide-open routes. Primary minimum: 20 routes.
Baseline: the average training-player outcome (an intercept-only model).
Score both forecasts by mean absolute error in yards per receiver. Comparison: a straight line using 40-yard dash time alone.
Fit both on 2023–24 draft classes and evaluate on the untouched 2025 class.
This is a scouting test conditional on having enough recorded NFL routes.
"""
import argparse
import csv
from collections import defaultdict
from math import isfinite
from pathlib import Path
from statistics import mean, median


def rows(folder, filename, required):
    with (folder / filename).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{filename} is missing columns: {sorted(missing)}")
        yield from reader


def number(value):
    if value.strip() in {"", "NA", "NaN"}:
        return None
    result = float(value)
    return result if isfinite(result) else None


def build_sample(folder):
    receivers = {}
    for row in rows(folder, "combine_results.csv",
                    ["nfl_id", "draft_year", "combine_position", "forty"]):
        if row["combine_position"] == "WR" and row["draft_year"] in {"2023", "2024", "2025"}:
            player = row["nfl_id"]
            if player in receivers:
                raise ValueError(f"Duplicate combine entry for WR {player}")
            receivers[player] = (int(row["draft_year"]), number(row["forty"]))

    seasons = {r["game_id"]: int(r["season"])
               for r in rows(folder, "games.csv", ["game_id", "season", "season_type"])
               if r["season_type"] == "REG"}
    gaps = defaultdict(list)
    seen = set()
    missing_gap = 0
    fields = ["game_id", "play_id", "nfl_id", "play_nullified_by_penalty",
              "team_abbr", "possession_team", "route_ran", "team_coverage_man_zone",
              "separation_at_pass_forward"]
    for row in rows(folder, "player_play.csv", fields):
        player, game = row["nfl_id"], row["game_id"]
        if player not in receivers or seasons.get(game) != receivers[player][0]:
            continue
        if (row["team_abbr"] != row["possession_team"]
                or row["play_nullified_by_penalty"] != "N"
                or row["team_coverage_man_zone"] != "MAN_COVERAGE"
                or row["route_ran"] in {"NA", ""}):
            continue
        key = (game, row["play_id"], player)
        if key in seen:
            raise ValueError(f"Duplicate player-play: {key}")
        seen.add(key)
        gap = number(row["separation_at_pass_forward"])
        if gap is None or gap < 0:
            missing_gap += 1
        else:
            gaps[player].append(gap)

    sample = []
    for player, distances in gaps.items():
        year, sprint = receivers[player]
        if sprint is not None and sprint > 0:
            sample.append((year, sprint, median(distances), len(distances)))
    print(f"Combine WRs: {len(receivers)} | With measured rookie routes: {len(gaps)}"
          f" | With both routes and dash time: {len(sample)}")
    print(f"Eligible route records: {len(seen):,} | Missing/invalid separation: {missing_gap:,}")
    return sample


def evaluate(sample, minimum):
    eligible = [row for row in sample if row[3] >= minimum]
    train = [row for row in eligible if row[0] < 2025]
    test = [row for row in eligible if row[0] == 2025]
    if len(train) < 2 or not test:
        raise ValueError("Too few eligible receivers for the cohort comparison.")

    # Fit separation = training mean gap + slope * (dash time - training mean time).
    x_mean = mean(x for _, x, _, _ in train)
    y_mean = mean(y for _, _, y, _ in train)
    variance_sum = sum((x - x_mean) ** 2 for _, x, _, _ in train)
    if variance_sum == 0:
        raise ValueError("Training dash times have no variation.")
    slope = sum((x - x_mean) * (y - y_mean) for _, x, y, _ in train) / variance_sum
    baseline = y_mean
    baseline_error = mean(abs(y - baseline) for _, _, y, _ in test)
    speed_error = mean(abs(y - (y_mean + slope * (x - x_mean))) for _, x, y, _ in test)
    return len(train), len(test), baseline_error, speed_error


def main():
    parser = argparse.ArgumentParser(description="Test combine speed against rookie separation.")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent)
    folder = parser.parse_args().data_dir
    try:
        sample = build_sample(folder)
    except FileNotFoundError as exc:
        parser.exit(2, f"Missing {exc.filename}. Place the three CSVs beside the script "
                    "or pass --data-dir pointing to their folder.\n")

    print("\n2025 forecast error in yards per receiver (lower is better)")
    print("Min routes   Train WRs   Test WRs   Baseline   Dash model   Gain")
    # Nearby thresholds check whether the conclusion depends on the 20-route cutoff.
    for minimum in (10, 20, 30):
        train, test, baseline, speed = evaluate(sample, minimum)
        print(f"{minimum:10} {train:11} {test:10} {baseline:10.3f} {speed:12.3f}"
              f" {baseline - speed:+7.3f}")
        if minimum == 20:
            direction = "lower" if speed < baseline else "higher" if speed > baseline else "equal"
            print(f"  Primary result: dash-model error was {direction} on the 2025 class.")
    print("\nInterpretation is limited to observed routes and combine participants."
          " Route assignments, coverage and playing opportunities can differ across receivers.")


if __name__ == "__main__":
    main()
