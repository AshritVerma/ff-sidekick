import json, os, time, concurrent.futures, urllib.request

# Resolve paths next to this script so it runs anywhere, not just in the
# original /home/user/workspace sandbox.
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")
SOS  = os.path.join(HERE, "sos_map.json")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

TEAMS = {0:'FA',1:'ATL',2:'BUF',3:'CHI',4:'CIN',5:'CLE',6:'DAL',7:'DEN',8:'DET',9:'GB',10:'TEN',11:'IND',12:'KC',13:'LV',14:'LAR',15:'MIA',16:'MIN',17:'NE',18:'NO',19:'NYG',20:'NYJ',21:'PHI',22:'ARI',23:'PIT',24:'LAC',25:'SF',26:'SEA',27:'TB',28:'WSH',29:'CAR',30:'JAX',33:'BAL',34:'HOU'}
POS = {1:'QB',2:'RB',3:'WR',4:'TE',5:'K',16:'D/ST'}

def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

# 1) Top players with stats
flt = {"players": {
    "limit": 300,
    "sortDraftRanks": {"sortPriority": 100, "sortAsc": True, "value": "PPR"},
    "filterRanksForScoringPeriodIds": {"value": [1]},
    "filterStatsForExternalIds": {"value": [2025, 2026]}
}}
url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/segments/0/leaguedefaults/3?scoringPeriodId=0&view=kona_player_info"
data = get(url, {"X-Fantasy-Filter": json.dumps(flt)})
players = []
for entry in data["players"]:
    p = entry["player"]
    pid = p["id"]
    rec = {
        "id": pid,
        "name": p.get("fullName"),
        "team": TEAMS.get(p.get("proTeamId"), "FA"),
        "pos": POS.get(p.get("defaultPositionId"), "?"),
        "injuryStatus": p.get("injuryStatus"),
        "pctOwned": round((p.get("ownership") or {}).get("percentOwned", 0), 1),
        "pctStarted": round((p.get("ownership") or {}).get("percentStarted", 0), 1),
        "rank": ((p.get("draftRanksByRankType") or {}).get("PPR") or {}).get("rank"),
        "adp": round((p.get("ownership") or {}).get("averageDraftPosition") or 0, 2) or None,
        "outlook": p.get("seasonOutlook") or "",
        "proj26": None, "projAvg26": None,
        "pts25": None, "avg25": None, "gp25": None,
        "raw25": {}, "raw26": {},
    }
    KEEP = ["0","1","3","4","20","23","24","25","42","43","53","58","72",
            "74","83","84","86","87",
            "95","96","99","105","106","120","127"]
    def keep_stats(s):
        st = s.get("stats") or {}
        return {k: round(st[k], 1) for k in KEEP if k in st and st[k]}
    for s in p.get("stats", []):
        if s.get("id") == "102026":  # 2026 season projection
            rec["proj26"] = s.get("appliedTotal")
            rec["projAvg26"] = s.get("appliedAverage")
            rec["raw26"] = keep_stats(s)
        elif s.get("id") == "002025":  # 2025 actuals
            rec["pts25"] = s.get("appliedTotal")
            rec["avg25"] = s.get("appliedAverage")
            rec["raw25"] = keep_stats(s)
            gp = (s.get("stats") or {}).get("210")
            if gp is None and s.get("appliedAverage"):
                gp = round(s["appliedTotal"] / s["appliedAverage"])
            rec["gp25"] = int(gp) if gp else None
    players.append(rec)
print("players:", len(players))

# 2) News per player
def fetch_news(pid):
    try:
        d = get(f"https://site.web.api.espn.com/apis/fantasy/v2/games/ffl/news/players?playerId={pid}&limit=3")
        items = []
        for f in d.get("feed", [])[:3]:
            link = ((f.get("links") or {}).get("web") or {}).get("href", "")
            items.append({"h": f.get("headline", ""), "d": (f.get("description") or "")[:280],
                          "t": f.get("published", ""), "u": link})
        return pid, items
    except Exception as e:
        return pid, []

news = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    for pid, items in ex.map(fetch_news, [r["id"] for r in players]):
        news[pid] = items
print("news fetched for", sum(1 for v in news.values() if v), "players")

for r in players:
    r["news"] = news.get(r["id"], [])

# draft rank = ESPN draft-board order (verified against a practice mock draft room:
# the board lists players by overall PPR rank, densely renumbered 1..N)
ranked = sorted([r for r in players if r.get("rank")], key=lambda r: r["rank"])
for i, r in enumerate(ranked):
    r["adpRank"] = i + 1
for r in players:
    r.setdefault("adpRank", None)

# strength of schedule from FantasyPros (sos_map.json: team abbrev -> pos -> 0-5)
POSMAP = {"QB": "QB", "RB": "RB", "WR": "WR", "TE": "TE", "K": "K", "D/ST": "DST"}
if os.path.exists(SOS):
    sos = json.load(open(SOS))
    for r in players:
        m = sos.get(r["team"]); k = POSMAP.get(r["pos"])
        r["sos"] = m[k] if (m and k) else None
else:
    for r in players:
        r["sos"] = None

# Preserve any other top-level keys already in data.json (sched26, oppRk, ...)
# so a stats refresh does not wipe the schedule data the dashboard also reads.
out = {}
if os.path.exists(DATA):
    try:
        out = json.load(open(DATA))
    except Exception:
        out = {}
out["generated"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
out["players"] = players
with open(DATA, "w") as f:
    json.dump(out, f)
print("saved", DATA)
# sanity
for r in players[:5]:
    print(r["name"], r["team"], r["pos"], r["proj26"], r["projAvg26"], r["pts25"], r["avg25"], r["gp25"], len(r["news"]))
