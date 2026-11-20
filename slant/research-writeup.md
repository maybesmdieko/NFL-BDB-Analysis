# Does speed gained out of a slant break predict rookie separation?

A scout watching two receivers run the same slant might notice that one accelerates sharply after turning inside. Is that burst evidence that he will get open against NFL man coverage? Across 15 receivers in the 2025 draft class, adding post-turn speed gain to the 40-yard dash increased average prediction error from **0.162 to 0.175 yards**. I would use the drill to select reps for film review. These results give me little reason to use speed gain alone to change a prospect’s grade.

## From a Combine route to a game outcome

I used player positions and speeds recorded ten times per second during the Combine left-slant drill. After the receiver travelled two yards downfield, I marked the first inward turn of at least 25 degrees sustained across two consecutive estimates. I subtracted the speed at that point from the speed half a second later. All 110 recorded attempts yielded a measurement. When a player ran multiple attempts, I used their median gain.

![110 left-slant trajectories aligned at the start, with a marker at the detected turn and another half a second later.](slant-window.svg)

*Figure 1. The measurement window follows each receiver’s turn. The markers estimate when the path bends inward. Video would be needed to identify the foot plant.*

I matched receivers to their rookie regular-season routes against man coverage, including plays where another receiver was targeted. The game outcome was distance to the nearest defender when the quarterback released the ball. To account for route assignments, I subtracted the 2023–24 median separation for that route type from each play. I then took each player’s median across plays. A positive result means that receiver typically had more space than the earlier norm for the routes they ran.

## Did the sensor measurement earn its place?

Sixty-nine receivers had a dash time, a slant measurement and at least one measured NFL route. The main comparison required 20 routes per player. I trained on 35 receivers from 2023–24 and evaluated every forecast on the same 15 receivers from 2025. Each player counted equally.

![Average absolute error for 15 test receivers: 0.135 yards using the training average, 0.162 using dash time, and 0.175 using dash time and post-turn speed gain.](forecast-error.svg)

*Figure 2. Lower error means a more accurate forecast of a receiver’s typical route-adjusted separation.*

| Minimum measured routes | Training receivers | Test receivers | Training average | Dash time | Dash + speed gain |
|---:|---:|---:|---:|---:|---:|
| 10 | 43 | 16 | 0.145 | 0.197 | 0.198 |
| **20** | **35** | **15** | **0.135** | **0.162** | **0.175** |
| 30 | 32 | 14 | 0.139 | 0.168 | 0.173 |

*Mean absolute error in yards per receiver. These thresholds use overlapping groups, so they provide a sensitivity check.*

At 20 routes, the estimated improvement from adding the sensor measurement was **−0.013 yards**. A player-level bootstrap gave an approximate 95% interval of **−0.036 to +0.011 yards**, holding the fitted models fixed. A small benefit remains plausible. The 2025 class had already been examined in the earlier dash-time study, making another draft class a stronger independent test.

## What I would take to a receiver coach

A small speed gain has two football explanations worth distinguishing on film. One receiver might carry speed through the break and have little to regain. Another might slow sharply and struggle to accelerate. I would show the coach reps with similar gains but different entry speeds and ask which pattern they recognize on game film. That is a concrete use for the tracking data while the predictive evidence is weak.

The game comparison includes many route types. Adjusting for their typical separation addresses some differences in assignments, but defender cushion and release timing still affect the space available. A sharper follow-up would pair Combine slants with NFL slants, check the detected turns against film, and test whether entry and exit speeds improve prediction on a fresh cohort. That would directly test whether the movement scouts see in the drill carries over to the same task on Sundays.

[Executed research notebook](slant-study.ipynb) · [Reproducible Python analysis](analyze.py)
