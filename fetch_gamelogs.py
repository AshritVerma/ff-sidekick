"""Fetch weekly PPR game logs (2025 + 2024) for all players in data.json."""
import json, os, urllib.request, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")

BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

TEAMS = {0:'FA',1:'ATL',2:'BUF',3:'CHI',4:'CIN',5:'CLE',6:'DAL',7:'DEN',8:'DET',9:'GB',10:'TEN',11:'IND',12:'KC',13:'LV',14:'LAR',15:'MIA',16:'MIN',17:'NE',18:'NO',19:'NYG',20:'NYJ',21:'PHI',22:'ARI',23:'PIT',24:'LAC',25:'SF',26:'SEA',27:'TB',28:'WSH',29:'CAR',30:'JAX',33:'BAL',34:'HOU'}

def get(url, headers=None):
    h = dict(UA)
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    return json.load(urllib.request.urlopen(req, timeout=30))

def schedules(season):
    """team -> week -> (opp abbrev, is_home)"""
    d = get(f"{BASE}/{season}?view=proTeamSchedules_wl")
    out = {}
    for t in d["settings"]["proTeams"]:
        tid = t["id"]
        for wk, games in (t.get("proGamesByScoringPeriod") or {}).items():
            for g in games:
                h, a = g["homeProTeamId"], g["awayProTeamId"]
                if tid == h: out.setdefault(tid, {})[int(wk)] = (TEAMS.get(a,'?'), True)
                elif tid == a: out.setdefault(tid, {})[int(wk)] = (TEAMS.get(h,'?'), False)
    return out

def weekly(season, ids):
    """Actual and projected weekly points.

    ESPN returns both in the same payload: statSourceId 0 is what happened,
    statSourceId 1 is what they projected beforehand. We keep both so a game
    log can show the miss as well as the result.
    """
    f = {"players": {"filterIds": {"value": ids},
         "filterStatsForTopScoringPeriodIds": {"value": 18, "additionalValue": [f"00{season}", f"10{season}"]}}}
    d = get(f"{BASE}/{season}/segments/0/leaguedefaults/3?view=kona_playercard",
            {"X-Fantasy-Filter": json.dumps(f)})
    out = {}
    for w in d.get("players", []):
        p = w.get("player") or {}
        actual, proj = {}, {}
        for st in p.get("stats", []):
            if st.get("statSplitTypeId") != 1 or st.get("seasonId") != season:
                continue
            wk = st.get("scoringPeriodId")
            pts = round(st.get("appliedTotal", 0), 1)
            if st.get("statSourceId") == 0:
                actual[wk] = {"pts": pts, "tm": st.get("proTeamId", 0)}
            elif st.get("statSourceId") == 1:
                proj[wk] = pts
        rows = [{"w": wk, "pts": v["pts"], "tm": v["tm"], "proj": proj.get(wk)}
                for wk, v in sorted(actual.items())]
        out[p["id"]] = rows
    return out


def main():
    data = json.load(open(DATA))
    ids = [p["id"] for p in data["players"]]
    abbr2id = {v: k for k, v in TEAMS.items()}
    for season, key, byekey in ((2025, "g25", "bye25"), (2024, "g24", "bye24")):
        sched = schedules(season)
        logs = {}
        for i in range(0, len(ids), 50):
            logs.update(weekly(season, ids[i:i+50]))
            time.sleep(0.4)

        # A week a team simply doesn't play is a bye. Without this the game log
        # can't tell a bye from a game the player missed -- they both just aren't
        # there.
        byes = {}
        for tid, weeks in sched.items():
            miss = [w for w in range(1, 19) if w not in weeks]
            if miss:
                byes[tid] = miss[0]

        for p in data["players"]:
            rows = logs.get(p["id"], [])
            out = []
            for r in rows:
                opp = sched.get(r["tm"], {}).get(r["w"])
                out.append([r["w"], r["pts"],
                            (("" if opp[1] else "@") + opp[0]) if opp else "",
                            r.get("proj")])
            p[key] = out
            tid = abbr2id.get(p.get("team"))
            # prefer the team the player actually played for that season
            if rows:
                tid = rows[-1].get("tm") or tid
            p[byekey] = byes.get(tid)
        print(season, "logs:", sum(1 for p in data["players"] if p[key]),
              "| with projections:", sum(1 for p in data["players"]
                                         for g in p[key] if len(g) > 3 and g[3] is not None),
              "| byes known:", sum(1 for p in data["players"] if p.get(byekey)))
    json.dump(data, open(DATA, "w"))
    print("saved", DATA)


if __name__ == "__main__":
    main()
