# NFL Big Data Bowl Analysis

Does a receiver’s 40-yard dash time at the NFL Combine help predict separation from a defender when the quarterback releases the ball against man coverage?

The Python sample trains on rookie receivers from the 2023 and 2024 draft classes and tests its predictions on the 2025 class. For the 15 test receivers with at least 20 eligible routes, the dash-time model had a mean absolute error of 0.246 yards. Predicting the training-group average for everyone produced a smaller error of 0.209 yards.

Download the competition files and run the following command with Python 3.9 or later. The data directory must contain `combine_results.csv`, `games.csv`, and `player_play.csv`. The script uses only the standard library.

```bash
python3 rookie_receiver_separation.py --data-dir /path/to/csvs
```

[2027 NFL Big Data Bowl dataset](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027/data)

## Additional baseball sample

The second script tests whether pitch type improves swing-and-miss forecasts for José Berríos. Run it offline with the included game counts using Python 3.10 or later.

```bash
python3 pitch_type_research.py
```
