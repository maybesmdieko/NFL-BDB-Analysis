# From Combine slants to NFL separation

Does the speed a wide receiver gains in the half-second after a Combine slant cut help predict how much space he creates against NFL man coverage as a rookie? Across two draft-class tests, adding post-cut speed gain to a forecast based on 40-yard dash time increased average error.

[Illustrated findings](slant/research-writeup.md) · [Executed notebook](slant/slant-study.ipynb) · [Word report](slant/Combine_Slant_Research.docx) · [Kaggle writeup](https://kaggle.com/competitions/nfl-big-data-bowl-2027/writeups/from-combine-slants-to-nfl-separation-does-speed)

## Results

The analysis measures speed gain on 110 Combine left-slant attempts tracked at 10 Hz. The NFL outcome is each receiver’s median separation at pass release relative to the typical separation for the routes he ran. Each receiver had at least 20 eligible rookie routes and counted once. Models used earlier draft classes to forecast a later class.

| Test class | Training / test receivers | Training average | Dash time | Dash + speed gain |
|---|---:|---:|---:|---:|
| 2024 | 18 / 17 | 0.206 | 0.202 | 0.218 |
| 2025 | 35 / 15 | 0.135 | 0.162 | 0.175 |

Values are mean absolute errors in yards per receiver. Lower is better. In 2025, adding gain helped four of 15 receivers. The small sample leaves uncertainty about future classes.

Two receivers can gain the same amount of speed while carrying different speeds into the turn. That makes the drill useful for choosing reps to compare on film. The results give little reason to add gain to a numerical separation grade. [See the paired receiver traces](slant/matched-receivers.svg).

## Reproduce the study

Start with the [setup instructions and file guide](slant/README.md). The [executed notebook](slant/slant-study.ipynb) contains the full analysis, including the earlier-class test, individual errors, cushion adjustment and Tank Dell game example. Obtain the six input CSVs from the [competition data page](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027/data).

## Earlier work and additional samples

The [initial dash-time experiment](rookie_receiver_separation.py) predicts raw separation. Its 2025 errors were 0.209 yards for the training average and 0.246 for dash time. The slant study adjusts for route type and requires a usable Combine rep, so compare models within each experiment.

```bash
python3 rookie_receiver_separation.py --data-dir /path/to/csvs
```

The separate [baseball sample](pitch_type_research.py) tests whether pitch type helps forecast swings and misses for José Berríos. Run it offline with `python3 pitch_type_research.py`.
