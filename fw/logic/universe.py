import random, streamlit as st
from fw.db import add_ticker

def schedule_weekly_if_missing(next_week):
    db = st.session_state.db
    by_fed = {}
    for s in db["shows"].values():
        by_fed.setdefault(s["federation_id"], set()).add(s["scheduled_week"])
    for fid, fed in db["federations"].items():
        if next_week not in by_fed.get(fid, set()):
            sh = __import__("fw.util.ids", fromlist=["new_id"]).new_id("show")
            num = sum(1 for s in db["shows"].values() if s["federation_id"]==fid) + 1
            db["shows"][sh] = {"id": sh, "federation_id": fid, "name": f"{fed['name']} Weekly #{num}",
                               "scheduled_week": next_week, "status":"upcoming",
                               "weirdness_snapshot": max(0, min(100, random.randint(10,25) + fed["popularity"]//10))}

def skip_time():
    db = st.session_state.db
    wk = db["universe"]["current_week"]
    # postpone overdue
    for s in db["shows"].values():
        if s["scheduled_week"] < wk and s["status"]=="upcoming":
            s["status"] = "postponed"
            add_ticker("SHOW_POSTPONED", f"Show postponed: {s['name']}", "", severity=2, entities={"show_id": s["id"]})
    # advance
    db["universe"]["current_week"] += 1
    new_wk = db["universe"]["current_week"]
    schedule_weekly_if_missing(new_wk)
    add_ticker("SCHEDULE_ROLLOVER", f"Advanced to Week {new_wk}", "Weekly shows scheduled.")
