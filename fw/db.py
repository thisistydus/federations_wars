import json, random
import streamlit as st
from fw.util.ids import new_id
from fw.models import FED_STYLES, GENDERS

def ss():
    if "db" not in st.session_state:
        st.session_state.db = {
            "universe": {"name": "Universe 0", "current_week": 1, "rng_seed": 42, "archived": False},
            "federations": {},     # fed_id -> dict
            "workers": {},         # worker_id -> dict
            "employment": [],      # list of {worker_id, fed_id, start_week, end_week, masked}
            "shows": {},           # show_id -> dict
            "matches": {},         # match_id -> dict
            "ticker": []           # list of events
        }
        random.seed(42)

def add_ticker(event_type, headline, blurb="", severity=2, confidence=1.0, entities=None):
    ss()
    db = st.session_state.db
    db["ticker"].insert(0, {
        "id": new_id("evt"),
        "ts": __import__("datetime").datetime.utcnow().isoformat()+"Z",
        "type": event_type,
        "severity": severity,
        "confidence": confidence,
        "entities": entities or {},
        "headline": headline,
        "blurb": blurb,
        "week": db["universe"]["current_week"]
    })

def clamp(v, lo, hi): return max(lo, min(hi, v))
def current_week(): return st.session_state.db["universe"]["current_week"]

# ---------- Save/Load ----------
def export_universe_json() -> str:
    ss(); return json.dumps(st.session_state.db, indent=2)

def import_universe_json(text: str):
    data = json.loads(text)
    if not isinstance(data, dict) or "universe" not in data or "federations" not in data:
        raise ValueError("Invalid universe JSON (missing keys).")
    st.session_state.db = data
    add_ticker("UNIVERSE_IMPORT", "Universe imported", "Loaded from JSON file.", severity=1)

# ---------- Seed ----------
def seed_demo():
    ss()
    st.session_state.db = {
        "universe": {"name": "Universe 0", "current_week": 1, "rng_seed": 42, "archived": False},
        "federations": {}, "workers": {}, "employment": [],
        "shows": {}, "matches": {}, "ticker": []
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

    # Defaults by style
    for f in db["federations"].values():
        f.setdefault("allow_intergender", f["style"] in ("hardcore","lucha","sports_ent"))
        f.setdefault("allow_tag", f["style"] in ("sports_ent","hardcore","lucha"))
        f.setdefault("allow_trios", f["style"] in ("lucha",))

    # Workers
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
            "skill": random.randint(50,90), "charisma": random.randint(40,95),
            "prestige": random.randint(20,80), "risk": random.randint(10,50),
            "bio_short": "", "gender": random.choice(GENDERS)
        }

    # Employment: 4 per fed; masked if lucha
    w_ids = list(db["workers"].keys())
    slices = [w_ids[0:4], w_ids[4:8], w_ids[8:12]]
    for (fid, ws) in zip(db["federations"].keys(), slices):
        fed_style = db["federations"][fid]["style"]
        for wid in ws:
            masked = (fed_style == "lucha") and (random.random() < 0.7)
            db["employment"].append({"worker_id": wid, "fed_id": fid, "start_week": 1, "end_week": None, "masked": masked})

    # One show each @ wk1
    for fid, fed in db["federations"].items():
        sh = new_id("show")
        db["shows"][sh] = {"id": sh, "federation_id": fid, "name": f"{fed['name']} Weekly #1",
                           "scheduled_week": 1, "status":"upcoming", "weirdness_snapshot":15}

    add_ticker("UNIVERSE_INIT", "Universe 0 initialized", "Demo feds/workers seeded.", severity=1)

# ---------- CRUD ----------
def create_fed(name, style, popularity, safety, liquidity, about, allow_intergender=None, allow_tag=None, allow_trios=None):
    ss()
    fid = new_id("fed")
    f = {
        "id": fid, "name": name, "style": style, "popularity": popularity,
        "safety": safety, "liquidity": liquidity, "about": about,
        "allow_intergender": bool(allow_intergender if allow_intergender is not None else (style in ("hardcore","lucha","sports_ent"))),
        "allow_tag": bool(allow_tag if allow_tag is not None else (style in ("sports_ent","hardcore","lucha"))),
        "allow_trios": bool(allow_trios if allow_trios is not None else (style in ("lucha",)))
    }
    st.session_state.db["federations"][fid] = f
    add_ticker("FED_CREATED", f"Federation created: {name}", "", severity=1)
    return fid

def create_worker(ring_name, style, alignment, skill, charisma, prestige, risk, bio, gender):
    ss()
    wid = new_id("w")
    st.session_state.db["workers"][wid] = {
        "id": wid, "ring_name": ring_name, "style": style, "alignment": alignment,
        "skill": skill, "charisma": charisma, "prestige": prestige, "risk": risk,
        "bio_short": bio, "gender": gender
    }
    add_ticker("WORKER_CREATED", f"Worker created: {ring_name}", f"Gender: {gender}", severity=1)
    return wid

def employ_worker(worker_id, fed_id, start_week=None, masked=False):
    ss()
    if start_week is None: start_week = current_week()
    st.session_state.db["employment"].append({
        "worker_id": worker_id, "fed_id": fed_id, "start_week": start_week, "end_week": None, "masked": bool(masked)
    })
    w = st.session_state.db['workers'][worker_id]['ring_name']
    f = st.session_state.db['federations'][fed_id]['name']
    add_ticker("EMPLOYMENT", f"Hired: {w} → {f}", "Masked" if masked else "Unmasked")

# ---------- Queries ----------
def fed_employed_workers(fid, week=None):
    ss(); db = st.session_state.db
    week = week or current_week()
    ids = {e["worker_id"] for e in db["employment"]
           if e["fed_id"]==fid and (e["end_week"] is None or e["end_week"]>=week) and e["start_week"]<=week}
    return [{"id": wid, **db["workers"][wid]} for wid in ids]

def shows_for_week(week):
    ss(); return [s for s in st.session_state.db["shows"].values() if s["scheduled_week"]==week]
