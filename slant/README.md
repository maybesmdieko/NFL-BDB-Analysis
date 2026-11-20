# Reproduce the Combine slant study

[Read the findings](research-writeup.md) · [View the executed notebook](slant-study.ipynb) · [Download the Word report](Combine_Slant_Research.docx)

## Competition inputs

Download these six CSVs from the [2027 NFL Big Data Bowl](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027/data) and extract them into one folder. The notebook joins records by player, game and play identifiers.

| File | Used for |
|---|---|
| `combine_tracking.csv` | Detect the turn and measure each receiver’s speed gain |
| `combine_results.csv` | Select wide receivers and obtain draft year and dash time |
| `games.csv` | Identify rookie regular-season games |
| `player_play.csv` | Filter eligible routes and measure separation, route type and defender cushion |
| `players.csv` | Label the receiver comparisons |
| `game_tracking_2023.csv` | Reconstruct the Tank Dell slant from snap to release |

## Run the full notebook

On Kaggle, import [slant-study.ipynb](slant-study.ipynb), attach the competition data and run all cells in order. The notebook searches the attached competition folders for the six files.

Locally, run the following from the repository root in a Python 3.12 environment. Replace the example path with your CSV folder. The requirements file records the numerical and plotting library versions used to verify the study.

```bash
python -m pip install -r slant/requirements.txt jupyterlab
export BDB_DATA_DIR="/path/to/extracted/csvs"
python -m jupyterlab slant/slant-study.ipynb
```

Choose **Run All Cells**. A successful run measures 110 of 110 attempts and reports 35 training receivers and 15 test receivers at the 20-route threshold in 2025. The notebook reads the CSVs and displays its results inline.

## Run individual analyses

```bash
python slant/analyze.py --data-dir "$BDB_DATA_DIR"
python slant/followup.py --data-dir "$BDB_DATA_DIR"
```

[analyze.py](analyze.py) runs the main 2025 comparison, route thresholds and player-level bootstrap, then writes the turn-window and forecast-error SVGs beside the script. [followup.py](followup.py) runs the timing, entry-speed, NFL-slant and cushion checks and writes a PNG of the matched receiver traces. Use the notebook for the full set of analyses and figures.

## Figures

- [Combine turn measurement](slant-window.svg)
- [Forecast errors in both draft classes](two-class-errors.svg)
- [Primary 2025 forecast comparison](forecast-error.svg)
- [2025 error changes by receiver](paired-errors.svg)
- [Iosivas and Douglas through the turn](matched-receivers.svg)
- [Tank Dell’s Combine and NFL slants](game-slant.svg)

The notebook and Word report also include the receiver-level scatterplot of Combine gain against adjusted NFL separation.
