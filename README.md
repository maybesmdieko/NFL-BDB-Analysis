# 2027 NFL Big Data Bowl | Wide receiver separation

The 2027 NFL Big Data Bowl asks which traits measured at the NFL Scouting Combine carry over to regular-season performance. Participants can follow a prospect from drills tracked ten times per second to plays in NFL games. My project focuses on wide receivers and a question that matters to scouts: **what can we learn at the Combine about a receiver’s ability to get open against man coverage?**

[Official NFL overview](https://operations.nfl.com/programs-initiatives/innovation/big-data-bowl) · [Competition and data on Kaggle](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027)

## First experiment

I started with the 40-yard dash. For each receiver, I measured their median distance from a defender when the quarterback released the pass on eligible rookie routes against man coverage. I used the 2023 and 2024 draft classes to build two forecasts: one gave every receiver the training-group average, and the other used the receiver’s dash time. I tested both on the 2025 draft class.

Among the 15 rookies with at least 20 measured routes, the average forecast missed by **0.209 yards per receiver**. Adding dash time increased the error to **0.246 yards**. The simpler forecast also performed better at minimums of 10 and 30 routes. For this group, straight-line speed alone added little information about who would get open.

## Next experiment

A receiver often has to change direction to get open. I’d use the Combine sensor data to measure how quickly each receiver regains speed after a cut in the same drill. I’d then test whether that measurement improves on both forecasts above, accounting for the routes players ran in games. The dash-time result gives that experiment a benchmark to beat.

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
