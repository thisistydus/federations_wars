import random
import streamlit as st
from fw.db import fed_employed_workers
from fw.util.ids import new_id

STYLE_FIT = {
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
    show = db["shows"][show_id]; fid = show["federation_id"]; fed = db["federations"][fid]
    roster = fed_employed_workers(fid, show["scheduled_week"])

    # (id, gender) pool minus already booked
    pool = [(w["id"], db["workers"][w["id"]]["gender"]) for w in roster]
    existing = [m for m in db["matches"].values() if m["show_id"]==show_id]
    used = set(pid for m in existing for pid in m.get("participants", []))
    pool = [(pid,g) for (pid,g) in pool if pid not in used]
    if existing: return

    def pick_recipe():
        if fed["style"] == "mma": return [1,1]
        choices = [[1,1]]*5
        if fed.get("allow_tag"): choices += [[2,2]]*3
        if fed.get("allow_trios"): choices += [[3,3]]*2
        return random.choice(choices)

    def can_form_team(k, pool_local, allow_inter):
        if k<=0 or len(pool_local)<k: return None
        if allow_inter: return random.sample(pool_local, k)
        by_g = {}
        for p in pool_local: by_g.setdefault(p[1], []).append(p)
        genders = [g for g in by_g if len(by_g[g])>=k]
        if not genders: return None
        g = random.choice(genders); return random.sample(by_g[g], k)

    def pop_ids(picks, pool_local):
        ids = [pid for (pid,_) in picks]
        return ids, [x for x in pool_local if x[0] not in ids]

    matches = []
    random.shuffle(pool)
    for _ in range(4):
        k = pick_recipe()[0]; allow_inter = fed.get("allow_intergender", True)
        a = can_form_team(k, pool, allow_inter)
        if not a: break
        a_ids, pool = pop_ids(a, pool)
        b = can_form_team(k, pool, allow_inter)
        if not b:
            pool += [(pid, db["workers"][pid]["gender"]) for pid in a_ids]; break
        b_ids, pool = pop_ids(b, pool)
        matches.append((a_ids, b_ids))

    order = 1
    for (a_ids, b_ids) in matches:
        mid = new_id("match")
        db["matches"][mid] = {
            "id": mid, "show_id": show_id, "order": order,
            "stipulation":"Standard", "is_title_match": False,
            "participants": a_ids+b_ids, "teams":[a_ids, b_ids],
            "result": None, "recap_text": ""
        }
        order += 1
