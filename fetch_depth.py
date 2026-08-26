#!/usr/bin/env python3
"""
Build the per-team depth chart block: head coach, offensive coordinator.

Written into data.json as a 32-entry "coaches" map keyed by team abbreviation,
not repeated per player -- the board derives the skill-position depth itself
from the rankings it already has.

ESPN exposes a team's head coach but no coordinators, so the OC comes from
Wikipedia's "List of current NFL offensive coordinators", which is maintained
in-season and is the only structured source I found that carries them.

    python3 fetch_depth.py
"""

import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")
UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 Chrome/126.0 Safari/537.36")}
SEASON = 2026

TEAMS = {1:'ATL',2:'BUF',3:'CHI',4:'CIN',5:'CLE',6:'DAL',7:'DEN',8:'DET',9:'GB',10:'TEN',
         11:'IND',12:'KC',13:'LV',14:'LAR',15:'MIA',16:'MIN',17:'NE',18:'NO',19:'NYG',
         20:'NYJ',21:'PHI',22:'ARI',23:'PIT',24:'LAC',25:'SF',26:'SEA',27:'TB',28:'WSH',
         29:'CAR',30:'JAX',33:'BAL',34:'HOU'}

FULL = {
 'Arizona Cardinals':'ARI','Atlanta Falcons':'ATL','Baltimore Ravens':'BAL','Buffalo Bills':'BUF',
 'Carolina Panthers':'CAR','Chicago Bears':'CHI','Cincinnati Bengals':'CIN','Cleveland Browns':'CLE',
 'Dallas Cowboys':'DAL','Denver Broncos':'DEN','Detroit Lions':'DET','Green Bay Packers':'GB',
 'Houston Texans':'HOU','Indianapolis Colts':'IND','Jacksonville Jaguars':'JAX','Kansas City Chiefs':'KC',
 'Las Vegas Raiders':'LV','Los Angeles Chargers':'LAC','Los Angeles Rams':'LAR','Miami Dolphins':'MIA',
 'Minnesota Vikings':'MIN','New England Patriots':'NE','New Orleans Saints':'NO','New York Giants':'NYG',
 'New York Jets':'NYJ','Philadelphia Eagles':'PHI','Pittsburgh Steelers':'PIT','San Francisco 49ers':'SF',
 'Seattle Seahawks':'SEA','Tampa Bay Buccaneers':'TB','Tennessee Titans':'TEN','Washington Commanders':'WSH',
}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "ignore")


def head_coaches():
    """ESPN: one coach per team, which is the head coach."""
    out = {}
    base = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/%d/teams/%d/coaches"
    for tid, abbr in TEAMS.items():
        try:
            items = json.loads(get(base % (SEASON, tid))).get("items") or []
            if not items:
                continue
            d = json.loads(get(items[0]["$ref"].replace("http://", "https://")))
            name = " ".join(x for x in (d.get("firstName"), d.get("lastName")) if x).strip()
            if name:
                out[abbr] = name
        except Exception as e:
            print("  ! HC %s: %s" % (abbr, e), file=sys.stderr)
    return out


def coordinators():
    """Wikipedia's current-OC list. Rows read: [[Team]] || {{sortname|First|Last}}"""
    out = {}
    try:
        s = get("https://en.wikipedia.org/w/api.php?action=parse&page="
                "List_of_current_NFL_offensive_coordinators&prop=wikitext&format=json&formatversion=2")
        wt = (json.loads(s).get("parse") or {}).get("wikitext") or ""
    except Exception as e:
        print("  ! OC list: %s" % e, file=sys.stderr)
        return out
    for team, first, last in re.findall(
            r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]\s*\|\|\s*\{\{sortname\|([^|}]+)\|([^|}]+)", wt):
        abbr = FULL.get(team.strip())
        if abbr and abbr not in out:
            out[abbr] = ("%s %s" % (first.strip(), last.strip())).strip()
    # some rows spell the name plainly rather than via the sortname template
    for team, name in re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]\s*\|\|\s*\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", wt):
        abbr = FULL.get(team.strip())
        if abbr and abbr not in out:
            out[abbr] = name.strip()
    return out


def skill_depth():
    """Per-team WR/RB/TE order from the whole player universe.

    data.json only carries the top 300, which is why a team's third receiver
    often wasn't there to list. This pulls a much deeper pool so every team has
    a real depth chart, and stores it as part of the same 32-entry map.
    """
    POS = {1: "QB", 2: "RB", 3: "WR", 4: "TE"}
    flt = {"players": {"limit": 1200,
                       "sortDraftRanks": {"sortPriority": 100, "sortAsc": True, "value": "PPR"}}}
    url = ("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/%d"
           "/segments/0/leaguedefaults/3?scoringPeriodId=0&view=kona_player_info" % SEASON)
    req = urllib.request.Request(url, headers={**UA, "X-Fantasy-Filter": json.dumps(flt)})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode())

    order = {}
    for entry in data.get("players") or []:
        p = entry.get("player") or {}
        pos = POS.get(p.get("defaultPositionId"))
        team = TEAMS.get(p.get("proTeamId"))
        if not pos or not team or pos == "QB":
            continue
        rank = (((p.get("draftRanksByRankType") or {}).get("PPR") or {}).get("rank"))
        order.setdefault(team, {}).setdefault(pos, []).append(
            {"id": p.get("id"), "n": p.get("fullName"), "r": rank})
    keep = {"WR": 5, "RB": 4, "TE": 4}
    out = {}
    for team, by_pos in order.items():
        out[team] = {}
        for pos, n in keep.items():
            lst = [x for x in by_pos.get(pos, []) if x["n"]]
            lst.sort(key=lambda x: (x["r"] is None, x["r"] if x["r"] is not None else 1e9))
            out[team][pos] = lst[:n]
    return out


def main():
    data = json.load(open(DATA))
    print("head coaches...")
    hc = head_coaches()
    print("  got %d" % len(hc))
    print("offensive coordinators...")
    oc = coordinators()
    print("  got %d" % len(oc))

    print("skill-position depth...")
    depth = skill_depth()
    print("  got %d teams" % len(depth))

    coaches = {}
    for abbr in sorted(set(TEAMS.values())):
        coaches[abbr] = {"hc": hc.get(abbr), "oc": oc.get(abbr),
                         "depth": depth.get(abbr, {})}
    data["coaches"] = coaches
    json.dump(data, open(DATA, "w"))

    missing_hc = [a for a, v in coaches.items() if not v["hc"]]
    missing_oc = [a for a, v in coaches.items() if not v["oc"]]
    print("saved %s" % DATA)
    thin = [a for a, v in coaches.items() if len((v.get("depth") or {}).get("WR") or []) < 4]
    print("  teams: %d | missing HC: %s | missing OC: %s"
          % (len(coaches), missing_hc or "none", missing_oc or "none"))
    print("  teams with fewer than 4 ranked WRs: %s" % (thin or "none"))


if __name__ == "__main__":
    main()
