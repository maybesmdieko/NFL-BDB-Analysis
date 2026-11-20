"""Exploratory checks. Run: python followup.py --data-dir /path/to/csvs"""
from itertools import combinations
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from analyze import measure_attempt, game_routes, forecast


def followup(folder):
    wr = pd.read_csv(folder / "combine_results.csv").query("combine_position == 'WR'")
    names = pd.read_csv(folder / "players.csv", usecols=["nfl_id", "display_name"])
    chunks = pd.read_csv(folder / "combine_tracking.csv", chunksize=100000)
    drill = pd.concat(c.query("entity_type == 'PLAYER' and drill_type == 'SKILL_DRILLS_WR' "
                              "and drill_name == 'SLANT_ROUTE_LEFT'") for c in chunks)
    reps, traces = [], {}
    for (player, event), g in drill.groupby(["nfl_id", "event_id"]):
        measured = measure_attempt(g)
        if measured is None:
            continue
        gain, _, _, t = measured
        s = g.sort_values("time").s.to_numpy()
        row = dict(nfl_id=player, event=event, entry=s[t], gain=gain)
        for offset in (-1, 1):
            j = t + offset
            row[str(offset)] = s[j+5]-s[j] if 0 <= j and j+5 < len(s) else np.nan
        reps.append(row)
        traces[event] = (s, t)
    reps = pd.DataFrame(reps)
    feats = reps.groupby("nfl_id")[["gain", "entry", "-1", "1"]].median().reset_index()
    cohort = wr.merge(feats, on="nfl_id").merge(game_routes(folder, wr), on="nfl_id")
    cohort = cohort.dropna(subset=["forty"]).merge(names, on="nfl_id")
    main = cohort[cohort.routes >= 20]
    train, test = main[main.draft_year < 2025], main[main.draft_year == 2025]
    for cols in ([], ["forty"], ["forty","gain"], ["forty","gain","entry"]):
        print("All routes", cols, round(np.mean(abs(test.adjusted_gap-forecast(train,test,cols))),4))
    common = main.dropna(subset=["-1","1"])
    for key in ("-1","gain","1"):
        a,b = common[common.draft_year < 2025],common[common.draft_year == 2025]
        print("Marker", key,len(a),len(b),round(np.mean(abs(b.adjusted_gap-forecast(a,b,["forty",key]))),4))

    cols = ["game_id","play_id","nfl_id","route_ran","separation_at_pass_forward","cushion",
            "team_coverage_man_zone","possession_team","team_abbr","play_nullified_by_penalty"]
    plays = pd.read_csv(folder / "player_play.csv",usecols=cols)
    games = pd.read_csv(folder / "games.csv").query("season_type == 'REG'")
    sl = plays.merge(games[["game_id","season"]],on="game_id",validate="many_to_one")
    sl = sl.merge(cohort[["nfl_id","draft_year"]],on="nfl_id",validate="many_to_one")
    sl = sl.query("season == draft_year and route_ran == 'SLANT' and team_coverage_man_zone == 'MAN_COVERAGE'"
                  " and team_abbr == possession_team and play_nullified_by_penalty == 'N' and separation_at_pass_forward >= 0")
    assert not sl.duplicated(["game_id","play_id","nfl_id"]).any()
    summary = sl.groupby("nfl_id").agg(slants=("play_id","size"), gap=("separation_at_pass_forward","median"))
    same = cohort.merge(summary,on="nfl_id")
    print("Measured NFL slants",len(sl),"players",len(same),"cushion available",sl.cushion.count())
    for cutoff in (1,5,10,20):
        sub = same[same.slants >= cutoff].copy()
        sub["adjusted_gap"] = sub.gap
        a,b = sub[sub.draft_year<2025],sub[sub.draft_year==2025]
        print("NFL slant minimum",cutoff,len(a),len(b))
        if cutoff == 5 and len(b)>1:
            for cols in ([],["forty"],["forty","gain"]):
                print("Exploratory slant MAE",cols,round(np.mean(abs(b.gap-forecast(a,b,cols))),4))

    # Estimate the association with cushion only on training routes, then compare
    # receivers on separation relative to that pre-snap expectation.
    cush = sl.dropna(subset=["cushion"]).copy()
    old = cush[cush.season < 2025]
    slope, intercept = np.polyfit(old.cushion, old.separation_at_pass_forward, 1)
    cush["residual"] = cush.separation_at_pass_forward - (intercept + slope*cush.cushion)
    context = cush.groupby("nfl_id").residual.agg(["median","count"]).reset_index()
    ctx = cohort.merge(context,on="nfl_id").query("count >= 5").copy()
    ctx["adjusted_gap"] = ctx["median"]
    a,b = ctx[ctx.draft_year<2025],ctx[ctx.draft_year==2025]
    print("Cushion-adjusted slants",len(a),len(b),"MAE",[
        round(np.mean(abs(b.adjusted_gap-forecast(a,b,cols))),4)
        for cols in ([],["forty"],["forty","gain"])])

    # Select from training receivers with a single drill rep. Selection uses only
    # sensor measurements and eligibility, never NFL outcomes or names.
    one = reps[~reps.nfl_id.duplicated(keep=False)].merge(train,on="nfl_id",suffixes=("","_median"))
    pairs = [(a,b) for a,b in combinations(one.itertuples(),2) if abs(a.gain-b.gain)<=0.05]
    a,b = max(pairs,key=lambda pair:abs(pair[0].entry-pair[1].entry))
    fig,ax=plt.subplots(figsize=(7.2,3.3))
    for r,color,style in [(a,"#00746c","-"),(b,"#9c4019","--")]:
        s,t=traces[r.event]; times=(np.arange(len(s))-t)/10
        keep=(times>=-0.5)&(times<=0.7)
        ax.plot(times[keep],s[keep],style,color=color,label=r.display_name,linewidth=2.7)
        ax.scatter([0,.5],[r.entry,r.entry+r.gain],color=color)
        print(r.display_name,"entry/exit/gain",np.round([r.entry,r.entry+r.gain,r.gain],3),
              "routes",r.routes,"adjusted separation",round(r.adjusted_gap,3))
    ax.axvspan(0,.5,color="#bddbd4",alpha=.32)
    ax.set(xlabel="Seconds from detected turn",ylabel="Speed (yards/second)")
    ax.legend(frameon=False);fig.tight_layout()
    return fig


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",required=True,type=Path)
    fig=followup(parser.parse_args().data_dir)
    fig.savefig(Path(__file__).with_name("matched-receivers.png"),dpi=160)
