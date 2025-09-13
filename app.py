import random, time
from datetime import datetime
import streamlit as st

# --------------------------
# Helpers & bootstrap
# --------------------------
def ss():
    if "db" not in st.session_state:
        st.session_state.db = {
            "universe": {"name": "Universe 0", "current_week": 1, "rng_seed": 42, "archived": False},
            "federations": {},     # fed_id -> fed dict
            "workers": {},         # worker_id -> worker dict
            "employment": [],      # list of {worker_id, fed_id, start_week, end_week}
            "shows": {},           # show_id -> show dict
            "matches": {},         # match_id -> match dict
            "ticker": []           # list of events
        }
        random.seed(42)

def new_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time()*1000)}_{random.randint(100,999)}"

def add_ticker(event_type, headline, blurb="", severity=2, confidence=1.0, entities=None):
    ss()
    st.session_state.db["ticker"].insert(0, {
        "id": new_id("evt"),
        "ts": datetime.utcnow().isoformat()+"Z",
        "type": event_type,
        "severity": severity,
        "confidence": confidence,
        "entities": entities or {},
        "headline": headline,
        "blurb": blurb,
        "week": st.session_state.db["universe"]["current_week"]
    })

def clamp(v, lo, hi): return max(lo, min(hi, v))

# --------------------------
# Seed demo data
# --------------------------
def seed_demo():
    ss()
    db = st.session_state.db
    # Reset
    st.session_state.db = {
        "universe": {"name": "Universe 0", "current_week": 1, "rng_seed": 42, "archived": False},
        "federations": {},
        "workers": {},
        "employment": [],
        "shows": {},
        "matches": {},
        "ticker": []
    }
    db = st.session_state.db
    random.seed(db["universe"]["rng_seed"])

    # Federations
    feds = [
        {"name":"Supreme Wrestling Syndicate", "style":"sports_ent", "popularity":70, "safety":65, "liquidity":500_000, "about":"Big stage, big stories."},
        {"name":"Steel City Wrestling", "style":"hardcore", "popularity":40, "safety":25, "liquidity":80_000, "about":"Rust, rebar, and ultraviolence."},
        {"name":"Global MMA League", "style":"mma", "popularity":85, "safety":90, "liquidity":900_000, "about":"Corporate, serious, legit."}
    ]
    for f in feds:
        fid = new_id("fed")
        db["federations"][fid] = {"id": fid, **f}

    # Workers (12)
    names = [
        ("Doctor Nightmare","hardcore"), ("Brickhouse Johnson","shoot"), ("Iron Tiger Lily","mma"),
        ("The Accountant","sports_ent"), ("Chainsaw Charlie Jr.","hardcore"), ("El Vortex","lucha"),
        ("Randy Sharktank","shoot"), ("Ms. Voltage","sports_ent"), ("Tiger Mask β","lucha"),
        ("Diego 'The Anvil' Cortez","mma"), ("Oksana Volkov","mma"), ("Crown Prince Nebula","sports_ent")
    ]
    for nm, sty in names:
        wid = new_id("w")
        db["workers"][wid] = {
            "id": wid, "ring_name": nm, "style": sty,
            "alignment": random.choice(["face","heel","neutral"]),
            "skill": random.randint(50,90),
            "charisma": random.randint(40,95),
            "prestige": random.randint(20,80),
            "risk": random.randint(10,50),
            "bio_short": ""
        }

    # Employment: 4 per federation
    w_ids = list(db["workers"].keys())
    by = [w_ids[0:4], w_ids[4:8], w_ids[8:12]]
    for (fid, workers) in zip(db["federations"].keys(), by):
        for wid in workers:
            db["employment"].append({"worker_id": wid, "fed_id": fid, "start_week": 1, "end_week": None})

    # Schedule one show for each fed @ week 1
    for fid, fed in db["federations"].items():
        sh_id = new_id("show")
        db["shows"][sh_id] = {
            "id": sh_id,
            "federation_id": fid,
            "name": f"{fed['name']} Weekly #1",
            "scheduled_week": 1,
            "status": "upcoming",
            "weirdness_snapshot": 15
        }

    add_ticker("UNIVERSE_INIT", "Universe 0 initialized", "Demo feds/workers seeded.", severity=1)

# --------------------------
# Query helpers
# --------------------------
def current_week(): return st.session_state.db["universe"]["current_week"]

def fed_employed_workers(fid, week=None):
    ss(); db = st.session_state.db
    week = week or current_week()
    active_ids = {e["worker_id"] for e in db["employment"] if e["fed_id"]==fid and (e["end_week"] is None or e["end_week"]>=week) and e["start_week"]<=week}
    return [db["workers"][wid] for wid in active_ids]

def shows_for_week(week):
    return [s for s in st.session_state.db["shows"].values() if s["scheduled_week"]==week]

# --------------------------
# Simulation logic
# --------------------------
STYLE_FIT = {
    # how worker.style fits when performing under fed.style (multiplier)
    "sports_ent": {"sports_ent":1.15, "lucha":1.05, "shoot":0.95, "hardcore":1.00, "mma":0.90},
    "hardcore":   {"hardcore":1.15, "sports_ent":1.05, "lucha":1.00, "shoot":0.95, "mma":0.90},
    "mma":        {"mma":1.15, "shoot":1.08, "sports_ent":0.92, "hardcore":0.92, "lucha":0.95},
    "lucha":      {"lucha":1.15, "sports_ent":1.05, "shoot":0.95, "hardcore":0.95, "mma":0.92},
    "shoot":      {"shoot":1.15, "mma":1.08, "sports_ent":0.95, "hardcore":0.95, "lucha":0.98}
}

def style_fit(worker_style, fed_style):
    return STYLE_FIT.get(fed_style, {}).get(worker_style, 1.0)

def star_score(wrk, fed_style):
    base = 0.6*wrk["skill"] + 0.3*wrk["charisma"] + 0.1*wrk["prestige"]
    return base * style_fit(wrk["style"], fed_style) + random.randint(-10,10)

def ensure_card(show_id):
    db = st.session_state.db
    show = db["shows"][show_id]
    fid = show["federation_id"]
    fed = db["federations"][fid]
    roster = fed_employed_workers(fid, show["scheduled_week"])
    roster_ids = [w["id"] for w in roster]
    # Remove anyone already on card
    existing = [m for m in db["matches"].values() if m["show_id"]==show_id]
    used = set()
    for m in existing:
        for p in m["participants"]: used.add(p)
    pool = [w for w in roster_ids if w not in used]
    # Auto-book 4 matches if none
    if len(existing)==0:
        random.shuffle(pool)
        pairs = []
        while len(pool) >= 2 and len(pairs)<4:
            a = pool.pop()
            b = pool.pop()
            pairs.append((a,b))
        order = 1
        for a,b in pairs:
            mid = new_id("match")
            db["matches"][mid] = {
                "id": mid, "show_id": show_id, "order": order,
                "stipulation": "Standard", "is_title_match": False,
                "participants": [a,b], "result": None, "recap_text": ""
            }
            order += 1

def run_match(mid):
    db = st.session_state.db
    m = db["matches"][mid]
    show = db["shows"][m["show_id"]]
    fed = db["federations"][show["federation_id"]]
    fed_style = fed["style"]
    parts = [db["workers"][pid] for pid in m["participants"]]
    # injuries / cancellations (simple MVP)
    if random.random() < 0.05 and fed["style"] in ("mma","hardcore"):
        # 50% cancel, 50% late replacement (skip replacement in MVP: cancel)
        m["result"] = {"canceled": True, "reason": "Injury in camp"}
        m["recap_text"] = "Bout canceled due to injury."
        add_ticker("MATCH_CANCELED", f"Match canceled on {show['name']}", "Injury in camp.", severity=3,
                   entities={"show_id": show["id"]})
        return

    # score everyone
    scored = [(p["id"], star_score(p, fed_style)) for p in parts]
    scored.sort(key=lambda x: x[1], reverse=True)
    winner = scored[0][0]
    loser = [pid for pid,_ in scored if pid != winner][0]
    method = random.choice(["pinfall","submission","KO/TKO","judges' decision"])
    time_s = random.randint(180, 1200)
    m["result"] = {"winners":[winner], "losers":[loser], "method": method, "time_s": time_s}
    wr = db["workers"][winner]["ring_name"]; lr = db["workers"][loser]["ring_name"]
    m["recap_text"] = f"{wr} defeated {lr} by {method} at {time_s}s."
    add_ticker("MATCH_RESULT", f"{wr} def. {lr} by {method}", f"Event: {show['name']}", severity=2,
               entities={"show_id": show["id"], "winner_id": winner, "loser_id": loser})

def run_card(show_id):
    ensure_card(show_id)
    db = st.session_state.db
    show = db["shows"][show_id]
    cards = [m for m in db["matches"].values() if m["show_id"]==show_id]
    cards.sort(key=lambda x: x["order"])
    if len(cards)==0:
        add_ticker("BOOKING_UPDATE", f"No matches available for {show['name']}", "Roster too thin?", severity=2)
    for m in cards:
        run_match(m["id"])
    show["status"] = "completed"
    add_ticker("SHOW_COMPLETED", f"Show completed: {show['name']}", "", severity=2)

def run_all_cards_this_week():
    db = st.session_state.db
    wk = db["universe"]["current_week"]
    todays = [s for s in db["shows"].values() if s["scheduled_week"]==wk and s["status"]=="upcoming"]
    if not todays:
        add_ticker("SCHEDULE_NOTE", f"No shows scheduled for Week {wk}", "", severity=1)
    for s in todays:
        run_card(s["id"])
        # minor popularity nudge
        fed = db["federations"][s["federation_id"]]
        delta = clamp(random.randint(-2,3), -3, 3)
        fed["popularity"] = clamp(fed["popularity"] + delta, 0, 100)

def schedule_weekly_if_missing(next_week):
    db = st.session_state.db
    by_fed = {}
    for s in db["shows"].values():
        by_fed.setdefault(s["federation_id"], set()).add(s["scheduled_week"])
    for fid, fed in db["federations"].items():
        weeks = by_fed.get(fid, set())
        if next_week not in weeks:
            sh_id = new_id("show")
            num = sum(1 for s in db["shows"].values() if s["federation_id"]==fid) + 1
            db["shows"][sh_id] = {
                "id": sh_id, "federation_id": fid,
                "name": f"{fed['name']} Weekly #{num}",
                "scheduled_week": next_week,
                "status": "upcoming",
                "weirdness_snapshot": clamp(random.randint(10, 25) + fed["popularity"]//10, 0, 100)
            }

def skip_time():
    db = st.session_state.db
    wk = db["universe"]["current_week"]
    # Mark overdue shows as postponed
    for s in db["shows"].values():
        if s["scheduled_week"] < wk and s["status"]=="upcoming":
            s["status"] = "postponed"
            add_ticker("SHOW_POSTPONED", f"Show postponed: {s['name']}", "", severity=2,
                       entities={"show_id": s["id"]})
    # Advance week
    db["universe"]["current_week"] += 1
    new_wk = db["universe"]["current_week"]
    # Auto-schedule weekly shows
    schedule_weekly_if_missing(new_wk)
    add_ticker("SCHEDULE_ROLLOVER", f"Advanced to Week {new_wk}", "Weekly shows scheduled.")

# --------------------------
# CRUD utilities
# --------------------------
def create_fed(name, style, popularity, safety, liquidity, about):
    fid = new_id("fed")
    st.session_state.db["federations"][fid] = {
        "id": fid, "name": name, "style": style, "popularity": popularity,
        "safety": safety, "liquidity": liquidity, "about": about
    }
    add_ticker("FED_CREATED", f"Federation created: {name}", "", severity=1)
    return fid

def create_worker(ring_name, style, alignment, skill, charisma, prestige, risk, bio):
    wid = new_id("w")
    st.session_state.db["workers"][wid] = {
        "id": wid, "ring_name": ring_name, "style": style, "alignment": alignment,
        "skill": skill, "charisma": charisma, "prestige": prestige, "risk": risk, "bio_short": bio
    }
    add_ticker("WORKER_CREATED", f"Worker created: {ring_name}", "", severity=1)
    return wid

def employ_worker(worker_id, fed_id, start_week=None):
    if start_week is None: start_week = current_week()
    st.session_state.db["employment"].append({"worker_id": worker_id, "fed_id": fed_id, "start_week": start_week, "end_week": None})
    add_ticker("EMPLOYMENT", f"Hired: {st.session_state.db['workers'][worker_id]['ring_name']} → {st.session_state.db['federations'][fed_id]['name']}")

# --------------------------
# UI
# --------------------------
st.set_page_config(page_title="Federation Wars — Alpha", layout="wide")
ss()

with st.sidebar:
    st.title("Federation Wars α")
    st.caption("Text sim • early alpha")
    wk = current_week()
    st.metric("In-game Week", wk)
    if st.button("Seed Demo Data"):
        seed_demo()
        st.success("Seeded demo data.")
    if st.button("Run All Cards (This Week)"):
        run_all_cards_this_week()
    if st.button("Skip Time (+1 week)"):
        skip_time()
    st.divider()
    page = st.radio("Pages", ["Dashboard", "Federations", "Workers", "Shows", "News"], index=0)

# Ticker strip
def render_ticker_strip(n=6):
    events = st.session_state.db["ticker"][:n]
    if not events: return
    lines = " | ".join([f"[{e['type']}] {e['headline']}" for e in events])
    st.info(lines, icon="📰")

render_ticker_strip()

# Pages
db = st.session_state.db

if page == "Dashboard":
    st.header("Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Federations")
        for f in db["federations"].values():
            st.write(f"**{f['name']}** — style: `{f['style']}`, pop: {f['popularity']}, safety: {f['safety']}")
    with col2:
        st.subheader("Upcoming Shows (this week)")
        wk = current_week()
        ups = [s for s in db["shows"].values() if s["scheduled_week"]==wk and s["status"]=="upcoming"]
        if ups:
            for s in sorted(ups, key=lambda x: x["name"]):
                fed = db["federations"][s["federation_id"]]["name"]
                st.write(f"• **{s['name']}** ({fed}) — Week {s['scheduled_week']}")
        else:
            st.write("_None scheduled this week._")
    with col3:
        st.subheader("Quick Actions")
        if st.button("Schedule next week's shows"):
            schedule_weekly_if_missing(current_week()+1)
            st.success("Scheduled.")

elif page == "Federations":
    st.header("Federations")
    with st.expander("➕ Create Federation"):
        name = st.text_input("Name")
        style = st.selectbox("Style", ["sports_ent","hardcore","mma","lucha","shoot"])
        c1,c2,c3 = st.columns(3)
        with c1: pop = st.slider("Popularity", 0, 100, 50)
        with c2: saf = st.slider("Safety", 0, 100, 50)
        with c3: liq = st.number_input("Liquidity", min_value=0, value=100000, step=10000)
        about = st.text_area("About", "")
        if st.button("Create Fed"):
            fid = create_fed(name, style, pop, saf, liq, about)
            st.success(f"Created {name} ({fid})")

    for fid, fed in db["federations"].items():
        st.subheader(fed["name"])
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.write(f"Style: `{fed['style']}`")
        with c2: st.write(f"Popularity: {fed['popularity']}")
        with c3: st.write(f"Safety: {fed['safety']}")
        with c4: st.write(f"Liquidity: ${fed['liquidity']:,}")
        st.write(f"_About:_ {fed.get('about','')}")
        roster = fed_employed_workers(fid)
        st.write(f"**Roster** ({len(roster)}): " + ", ".join([w["ring_name"] for w in roster]) if roster else "_Empty_")
        # Schedule a show quick
        if st.button(f"Schedule Weekly for {fed['name']}", key=f"sch_{fid}"):
            wk = current_week()
            sh_id = new_id("show")
            num = sum(1 for s in db["shows"].values() if s["federation_id"]==fid) + 1
            db["shows"][sh_id] = {"id":sh_id,"federation_id":fid,"name":f"{fed['name']} Weekly #{num}","scheduled_week":wk,"status":"upcoming","weirdness_snapshot":20}
            add_ticker("BOOKING_UPDATE", f"Show booked: {db['shows'][sh_id]['name']}")
            st.success("Scheduled.")

elif page == "Workers":
    st.header("Workers")
    with st.expander("➕ Create Worker"):
        ring = st.text_input("Ring name")
        style = st.selectbox("Style", ["sports_ent","hardcore","mma","lucha","shoot"], key="w_style")
        align = st.selectbox("Alignment", ["face","heel","neutral"])
        c1,c2,c3,c4 = st.columns(4)
        with c1: skill = st.slider("Skill", 0, 100, 60)
        with c2: ch = st.slider("Charisma", 0, 100, 60)
        with c3: pr = st.slider("Prestige", 0, 100, 40)
        with c4: rk = st.slider("Risk", 0, 100, 30)
        bio = st.text_area("Short bio", "")
        if st.button("Create Worker"):
            wid = create_worker(ring, style, align, skill, ch, pr, rk, bio)
            st.success(f"Created {ring} ({wid})")

    # transfer/hire
    st.subheader("Hire / Transfer")
    if db["workers"] and db["federations"]:
        wid = st.selectbox("Worker", list(db["workers"].keys()), format_func=lambda i: db["workers"][i]["ring_name"], key="hire_w")
        fid = st.selectbox("Federation", list(db["federations"].keys()), format_func=lambda i: db["federations"][i]["name"], key="hire_f")
        if st.button("Employ (start this week)"):
            employ_worker(wid, fid, start_week=current_week())
            st.success("Employment added.")

    st.divider()
    for wid, w in db["workers"].items():
        st.write(f"**{w['ring_name']}** — `{w['style']}` ({w['alignment']}) | Skill {w['skill']} • Cha {w['charisma']} • Pres {w['prestige']} • Risk {w['risk']}")
        # employment history
        jobs = [e for e in db["employment"] if e["worker_id"]==wid]
        if jobs:
            st.caption("Employment: " + "; ".join([f"{db['federations'][e['fed_id']]['name']} (wk {e['start_week']}→{e['end_week'] or '…'})" for e in jobs]))
        else:
            st.caption("_No employment records_")

elif page == "Shows":
    st.header("Shows")
    wk = current_week()
    st.caption(f"In-game Week {wk}")
    # Filters
    fchoice = st.selectbox("Filter by Federation", ["All"] + list(db["federations"].keys()), format_func=lambda i: "All" if i=="All" else db["federations"][i]["name"])
    shows = list(db["shows"].values())
    if fchoice != "All":
        shows = [s for s in shows if s["federation_id"]==fchoice]
    shows.sort(key=lambda s: (s["scheduled_week"], s["name"]))
    for s in shows:
        fed = db["federations"][s["federation_id"]]["name"]
        st.subheader(f"{s['name']} — {fed} (Week {s['scheduled_week']}) [{s['status']}]")
        # list matches
        ms = [m for m in db["matches"].values() if m["show_id"]==s["id"]]
        ms.sort(key=lambda x: x["order"])
        if ms:
            for m in ms:
                names = [db["workers"][pid]["ring_name"] for pid in m["participants"]]
                line = " vs ".join(names)
                if m["result"] and m["result"].get("canceled"):
                    st.write(f"• {line} — **CANCELED** ({m['result']['reason']})")
                elif m["result"]:
                    r = m["result"]; wnames = ", ".join([db["workers"][wid]["ring_name"] for wid in r["winners"]])
                    st.write(f"• {line} — **{wnames}** by {r['method']} ({r['time_s']}s)")
                else:
                    st.write(f"• {line} — _(not run)_")
        else:
            st.caption("_No matches booked yet_")
        c1,c2 = st.columns(2)
        with c1:
            if s["status"]=="upcoming" and st.button(f"Run Card: {s['name']}", key=f"run_{s['id']}"):
                run_card(s["id"]); st.success("Show completed.")
        with c2:
            if st.button(f"Auto-book card: {s['name']}", key=f"book_{s['id']}"):
                ensure_card(s["id"]); st.success("Card auto-booked.")

elif page == "News":
    st.header("News")
    types = ["All"] + sorted({e["type"] for e in db["ticker"]})
    tsel = st.selectbox("Filter by type", types)
    for e in db["ticker"]:
        if tsel!="All" and e["type"]!=tsel: continue
        st.write(f"**[{e['type']}] {e['headline']}**  \n{e['blurb']}  \n*Week {e['week']} • {e['ts']}*")
