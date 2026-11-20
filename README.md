# 2027 NFL Big Data Bowl | Wide receiver separation

The 2027 theme is **Combine to NFL Performance**. The challenge is to use movement recorded ten times per second during Combine drills to find traits that help coaches and scouts evaluate future regular-season performance. This project focuses on one question: **among wide receivers with similar 40-yard dash times, does the ability to regain speed after a route break help predict who creates separation against man coverage?**

[Official NFL overview](https://operations.nfl.com/programs-initiatives/innovation/big-data-bowl) · [Competition and data on Kaggle](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027)

## Completed benchmark: 40-yard dash

I started with the 40-yard dash. For each receiver, I measured their median distance from a defender when the quarterback released the pass on eligible rookie routes against man coverage. I used the 2023 and 2024 draft classes to build two forecasts: one gave every receiver the training-group average, and the other used the receiver’s dash time. I tested both on the 2025 draft class.

Among the 15 rookies with at least 20 measured routes, the average forecast missed by **0.209 yards per receiver**. Adding dash time increased the error to **0.246 yards**. The simpler forecast also performed better at minimums of 10 and 30 routes. For this group, straight-line speed alone added little information about who would get open.

## Planned sensor analysis

The tracking file includes a left slant drill (`SLANT_ROUTE_LEFT`). On a slant, a receiver changes direction to cut inside. Two receivers can run the same 40-yard dash yet lose different amounts of speed through that turn.

1. Use the tracked path to locate the turn in each attempt. Check those locations visually before calculating a metric.
2. Measure speed regained during the first half-second after the turn. Keep entry speed and the amount of speed lost through the turn for context. Summarize valid attempts per receiver and report how many players can be matched to NFL routes.
3. Compare a dash-only forecast with a forecast that also uses the sensor measurement, using the same players for both. Check whether any gain holds up on a later draft class and on comparable NFL routes. The 2025 class has already been examined for the benchmark, so that history should be disclosed in the writeup.

If the measurement adds predictive value, scouts could use it to identify receivers with ordinary sprint times whose route breaks merit a second look on film. Coaches could use the drill traces to investigate where a receiver loses speed. Whether training that movement improves game performance would need a separate test.

## Competition submission

The dash-time study is a benchmark. A scored entry must link Combine sensor tracking to regular-season performance. The final deliverables include a readable Markdown writeup with embedded visuals and an attached **public Kaggle Notebook**. The writeup is limited to 2,000 words and fewer than 10 tables or figures combined. The submission deadline is **January 6, 2027 at 11:59 p.m. UTC**.

[Competition and submission requirements](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027/overview/submission-requirements)

## Run the NFL analysis

Download `combine_results.csv`, `games.csv`, and `player_play.csv` from the competition data page into one folder. Run the script with Python 3.9 or later. It uses only the standard library.

```bash
python3 rookie_receiver_separation.py --data-dir /path/to/csvs
```

[NFL analysis code](rookie_receiver_separation.py)

## Additional baseball sample

A separate Python study tests whether pitch type improves swing-and-miss forecasts for José Berríos. It runs offline with the included game counts using Python 3.10 or later.

```bash
python3 pitch_type_research.py
```

[MLB analysis code](pitch_type_research.py)
