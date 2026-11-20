"""Does pitch type improve swing-and-miss forecasts for José Berríos?

A 2025 Toronto Blue Jays case study. Run with Python 3.10 or newer:
    python pitch_type_research.py
The default run uses included game-by-pitch counts and works offline.
In a notebook, paste and run the full script in one Python cell.
To rebuild the sample from MLB play-by-play, run:
    python pitch_type_research.py --live
Optional: --cache DIRECTORY selects the folder for downloaded MLB JSON.
No credentials or third-party packages needed.

Unit: one non-bunt swing. Outcome: the batter swings and misses (1) or
makes contact (0). A foul tip counts as contact. Taken pitches are excluded.
Question concerns swings already attempted; it does not predict whether a
batter will swing or establish which pitch a pitcher should throw.

Result: On 485 held-out swings, the pitch-type forecast scored 0.1322 versus
0.1452 for the overall rate (lower is better). This is evidence for one
pitcher and season; counts, locations and opponents could explain part of
the difference. A next test would compare these forecasts across pitchers.

Source: MLB Stats API, https://statsapi.mlb.com/api/v1/
"""
import argparse
import csv
import io
import sys
from collections import Counter, defaultdict
import json
from pathlib import Path
from random import Random
from statistics import mean
from urllib.request import urlopen

API = "https://statsapi.mlb.com/api/v1"
PITCHER = 621244
CUTOFF = "2025-07-01"
MISSES = {"Swinging Strike", "Swinging Strike (Blocked)"}
CONTACT = {"Foul", "Foul Tip"}
EXCLUDE = {"Ball", "Ball In Dirt", "Called Strike", "Hit By Pitch",
           "Pitchout", "Foul Bunt", "Missed Bunt", "Bunt Foul Tip"}


def fetch(url, path):
    if path.exists():
        return json.loads(path.read_bytes())
    with urlopen(url, timeout=60) as response:
        data = json.load(response)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def collect_swings(cache):
    cache.mkdir(parents=True, exist_ok=True)
    url = (f"{API}/people/{PITCHER}/stats?stats=gameLog&group=pitching"
           "&season=2025&gameType=R")
    games = fetch(url, cache / "games.json")["stats"][0]["splits"]
    swings = []
    excluded = Counter()
    for game in games:
        game_id = game["game"]["gamePk"]
        plays = fetch(f"{API}/game/{game_id}/playByPlay", cache / f"{game_id}.json")
        for play in plays["allPlays"]:
            if play["matchup"]["pitcher"]["id"] != PITCHER:
                continue
            for event in play["playEvents"]:
                if not event.get("isPitch"):
                    continue
                details = event["details"]
                call = details["call"]["description"]
                if call in EXCLUDE:
                    continue
                if call not in MISSES | CONTACT and not call.startswith("In play,"):
                    raise ValueError(f"Review unclassified pitch call: {call} (game {game_id})")
                pitch = details.get("type", {}).get("description")
                if not pitch or pitch == "Unknown":
                    excluded["unclassified pitch type on swing"] += 1
                    continue
                swings.append((game["date"], game_id, pitch, int(call in MISSES)))
    print(f"Games: {len(games)} | Excluded swings with missing type: {sum(excluded.values())}")
    return swings


def summarize(swings):
    counts, misses = Counter(), Counter()
    for _, _, pitch, miss in swings:
        counts[pitch] += 1
        misses[pitch] += miss
    return counts, misses


def analyze(swings):
    train = [s for s in swings if s[0] < CUTOFF]
    test = [s for s in swings if s[0] >= CUTOFF]
    if not train or not test:
        raise ValueError("Both training and evaluation periods need tracked swings.")
    n, misses = summarize(train)
    test_n, test_misses = summarize(test)
    baseline = sum(misses.values()) / len(train)
    # Fix five prior swings at the overall rate before evaluating. This limits
    # extreme predictions for rare pitches; unseen types use the baseline.
    prior = 5
    estimates = {p: (misses[p] + prior * baseline) / (n[p] + prior) for p in n}
    print(f"Training swings: {len(train)} | Held-out swings: {len(test)}")
    print(f"Overall training miss rate per swing: {baseline:.1%}")
    print(f"{'Pitch':20} {'Train N':>8} {'Forecast':>9} {'Test N':>8} {'Observed':>9}")
    for pitch in sorted(test_n):
        observed = test_misses[pitch] / test_n[pitch]
        print(f"{pitch:20} {n[pitch]:8} {estimates.get(pitch, baseline):9.1%}"
              f" {test_n[pitch]:8} {observed:9.1%}")

    # Brier score = mean squared probability error. Lower scores are better.
    base_errors, type_errors = [], []
    by_game = defaultdict(list)
    for _, game, pitch, outcome in test:
        base_error = (baseline - outcome) ** 2
        type_error = (estimates.get(pitch, baseline) - outcome) ** 2
        base_errors.append(base_error)
        type_errors.append(type_error)
        by_game[game].append(base_error - type_error)

    # Sample whole games to keep swings from the same outing together.
    # This describes test-game uncertainty conditional on the fitted forecasts.
    groups = [(sum(errors), len(errors)) for errors in by_game.values()]
    rng = Random(27)
    gains = []
    for _ in range(2000):
        sample = rng.choices(groups, k=len(groups))
        gains.append(sum(total for total, _ in sample) / sum(n for _, n in sample))
    gains.sort()
    difference = mean(base_errors) - mean(type_errors)
    print(f"Brier score | Overall: {mean(base_errors):.4f} | Pitch type: {mean(type_errors):.4f}")
    print(f"Gain from pitch type (positive favours pitch type): {difference:+.4f}")
    print(f"Approx. 95% interval resampling {len(groups)} held-out games:"
          f" [{gains[50]:+.4f}, {gains[1949]:+.4f}]")


# Frozen inputs from collect_swings: only counts, grouped by date, game, and pitch.
# These counts retain all information used by the model and game-level bootstrap.
GAME_COUNTS = """date,game,pitch,swings,misses
2025-03-27,778556,Sinker,10,2
2025-03-27,778556,Changeup,10,5
2025-03-27,778556,Slurve,11,4
2025-03-27,778556,Cutter,4,1
2025-03-27,778556,Four-Seam Fastball,4,0
2025-04-01,778491,Four-Seam Fastball,12,1
2025-04-01,778491,Slurve,12,3
2025-04-01,778491,Changeup,5,3
2025-04-01,778491,Sinker,9,1
2025-04-01,778491,Cutter,3,0
2025-04-07,778426,Four-Seam Fastball,7,0
2025-04-07,778426,Changeup,6,2
2025-04-07,778426,Sinker,14,0
2025-04-07,778426,Slurve,6,0
2025-04-07,778426,Cutter,2,0
2025-04-13,778344,Four-Seam Fastball,8,0
2025-04-13,778344,Slurve,4,2
2025-04-13,778344,Sinker,11,3
2025-04-13,778344,Cutter,1,0
2025-04-13,778344,Changeup,13,6
2025-04-19,778258,Cutter,1,0
2025-04-19,778258,Sinker,12,0
2025-04-19,778258,Slurve,8,1
2025-04-19,778258,Four-Seam Fastball,7,1
2025-04-19,778258,Changeup,6,2
2025-04-25,778185,Four-Seam Fastball,7,0
2025-04-25,778185,Sinker,13,0
2025-04-25,778185,Changeup,7,2
2025-04-25,778185,Cutter,4,0
2025-04-25,778185,Slurve,9,2
2025-05-01,778095,Sinker,17,3
2025-05-01,778095,Slurve,6,0
2025-05-01,778095,Four-Seam Fastball,7,0
2025-05-01,778095,Changeup,8,5
2025-05-01,778095,Cutter,6,1
2025-05-07,778009,Sinker,9,2
2025-05-07,778009,Slurve,20,11
2025-05-07,778009,Changeup,9,4
2025-05-07,778009,Cutter,1,0
2025-05-07,778009,Four-Seam Fastball,1,0
2025-05-13,777935,Four-Seam Fastball,7,0
2025-05-13,777935,Changeup,12,4
2025-05-13,777935,Slurve,11,5
2025-05-13,777935,Sinker,8,0
2025-05-13,777935,Cutter,4,0
2025-05-18,777871,Sinker,12,2
2025-05-18,777871,Slurve,11,5
2025-05-18,777871,Cutter,6,0
2025-05-18,777871,Four-Seam Fastball,8,3
2025-05-18,777871,Changeup,10,1
2025-05-24,777795,Sinker,11,0
2025-05-24,777795,Four-Seam Fastball,3,0
2025-05-24,777795,Slurve,9,3
2025-05-24,777795,Changeup,14,4
2025-05-24,777795,Cutter,7,1
2025-05-29,777727,Sinker,16,2
2025-05-29,777727,Changeup,7,3
2025-05-29,777727,Four-Seam Fastball,8,5
2025-05-29,777727,Slurve,4,1
2025-05-29,777727,Cutter,4,0
2025-06-04,777651,Slurve,14,5
2025-06-04,777651,Changeup,6,1
2025-06-04,777651,Sinker,13,1
2025-06-04,777651,Four-Seam Fastball,11,5
2025-06-04,777651,Cutter,1,0
2025-06-09,777581,Slurve,7,2
2025-06-09,777581,Changeup,6,1
2025-06-09,777581,Cutter,5,0
2025-06-09,777581,Sinker,12,1
2025-06-09,777581,Four-Seam Fastball,9,1
2025-06-15,777499,Sinker,12,1
2025-06-15,777499,Slurve,15,5
2025-06-15,777499,Changeup,6,1
2025-06-15,777499,Four-Seam Fastball,9,0
2025-06-15,777499,Cutter,4,3
2025-06-21,777418,Four-Seam Fastball,7,1
2025-06-21,777418,Cutter,3,1
2025-06-21,777418,Sinker,11,0
2025-06-21,777418,Slurve,12,3
2025-06-21,777418,Changeup,8,2
2025-06-27,777345,Cutter,5,1
2025-06-27,777345,Four-Seam Fastball,8,0
2025-06-27,777345,Sinker,7,0
2025-06-27,777345,Slurve,18,10
2025-06-27,777345,Changeup,10,2
2025-07-02,777274,Sinker,12,1
2025-07-02,777274,Changeup,11,4
2025-07-02,777274,Slurve,10,2
2025-07-02,777274,Four-Seam Fastball,8,0
2025-07-02,777274,Cutter,2,0
2025-07-07,777212,Four-Seam Fastball,8,0
2025-07-07,777212,Sinker,12,1
2025-07-07,777212,Changeup,4,1
2025-07-07,777212,Slurve,7,1
2025-07-07,777212,Cutter,4,2
2025-07-13,777116,Changeup,6,3
2025-07-13,777116,Sinker,14,0
2025-07-13,777116,Cutter,3,0
2025-07-13,777116,Four-Seam Fastball,2,0
2025-07-13,777116,Slurve,4,0
2025-07-20,777079,Four-Seam Fastball,12,2
2025-07-20,777079,Sinker,7,0
2025-07-20,777079,Slurve,13,4
2025-07-20,777079,Cutter,1,0
2025-07-20,777079,Changeup,4,1
2025-07-25,777016,Sinker,14,1
2025-07-25,777016,Slurve,9,3
2025-07-25,777016,Cutter,2,1
2025-07-25,777016,Four-Seam Fastball,4,0
2025-07-25,777016,Changeup,9,2
2025-07-30,776948,Sinker,10,0
2025-07-30,776948,Slurve,11,3
2025-07-30,776948,Cutter,8,1
2025-07-30,776948,Four-Seam Fastball,6,0
2025-07-30,776948,Changeup,5,2
2025-08-05,776854,Sinker,18,1
2025-08-05,776854,Changeup,14,4
2025-08-05,776854,Slurve,4,1
2025-08-05,776854,Cutter,1,0
2025-08-05,776854,Four-Seam Fastball,6,1
2025-08-12,776768,Four-Seam Fastball,9,0
2025-08-12,776768,Changeup,7,1
2025-08-12,776768,Sinker,10,0
2025-08-12,776768,Slurve,14,5
2025-08-12,776768,Cutter,1,0
2025-08-17,776710,Cutter,3,0
2025-08-17,776710,Sinker,11,1
2025-08-17,776710,Changeup,12,4
2025-08-17,776710,Four-Seam Fastball,8,0
2025-08-17,776710,Slurve,7,3
2025-08-23,776630,Four-Seam Fastball,2,1
2025-08-23,776630,Changeup,11,7
2025-08-23,776630,Sinker,14,1
2025-08-23,776630,Slurve,6,1
2025-08-23,776630,Cutter,1,0
2025-09-02,776491,Sinker,9,0
2025-09-02,776491,Changeup,6,2
2025-09-02,776491,Slurve,3,0
2025-09-02,776491,Four-Seam Fastball,2,0
2025-09-02,776491,Cutter,2,0
2025-09-10,776385,Sinker,16,3
2025-09-10,776385,Slurve,9,2
2025-09-10,776385,Changeup,4,2
2025-09-10,776385,Cutter,2,0
2025-09-10,776385,Four-Seam Fastball,3,0
2025-09-16,776305,Four-Seam Fastball,9,2
2025-09-16,776305,Slurve,6,0
2025-09-16,776305,Cutter,1,0
2025-09-16,776305,Changeup,8,0
2025-09-16,776305,Sinker,7,0
2025-09-24,776206,Slurve,6,4
2025-09-24,776206,Sinker,8,1
2025-09-24,776206,Changeup,3,2
"""


def offline_swings():
    swings = []
    for row in csv.DictReader(io.StringIO(GAME_COUNTS)):
        key = (row["date"], int(row["game"]), row["pitch"])
        total, misses = int(row["swings"]), int(row["misses"])
        swings.extend([(*key, 1)] * misses)
        swings.extend([(*key, 0)] * (total - misses))
    games = {s[1] for s in swings}
    print(f"Games: {len(games)} | Data source: included MLB game counts")
    return swings


if __name__ == "__main__":
    # Notebook kernels supply their own command-line arguments.
    if "ipykernel" in sys.modules:
        analyze(offline_swings())
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--live", action="store_true", help="use MLB data via local cache")
        parser.add_argument("--cache", type=Path, default=Path("berrios_2025_cache"))
        args = parser.parse_args()
        analyze(collect_swings(args.cache) if args.live else offline_swings())
