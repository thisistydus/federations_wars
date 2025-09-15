import random, streamlit as st
from fw.db import add_ticker, clamp
from fw.sim.booking import star_score, ensure_card

def run_match(match_id):
    db = st.session_state.db
    m = db["matches"][match_id]
    show = db["shows"][m["show_id"]]
    fed = db["federations"][show["federation_id"]]
    fed_style = fed["style"]

    # Simple cancellation chance for MMA/Hardcore
    if random.random() < 0.05 and fed_style in ("mma","hardcore"):
        m["result"] = {"canceled": True, "reason": "Injury in camp"}
        m["recap_text"] = "Bout canceled due to injury."
        add_ticker("MATCH_CANCELED", f"Match canceled on {show['name']}", "Injury in camp.", severity=3,
                   entities={"show_id": show["id"]})
        return

    teams = m.get("teams")
    if not teams:
        # fallback 1v1
        parts = [db["workers"][pid] for pid in m["participants"]]
        scored = sorted([(p["id"], star_score(p, fed_style)) for p in parts], key=lambda x: x[1], reverse=True)
        winner = scored[0][0]; loser = [pid for pid,_ in scored if pid != winner][0]
        method = random.choice(["pinfall","submission","KO/TKO","judges' decision"])
        time_s = random.randint(180, 1200)
        m["result"] = {"winners":[winner], "losers":[loser], "method": method, "time_s": time_s}
        wr = db["workers"][winner]["ring_name"]; lr = db["workers"][loser]["ring_name"]
        m["recap_text"] = f"{wr} defeated {lr} by {method} at {time_s}s."
        add_ticker("MATCH_RESULT", f"{wr} def. {lr} by {method}", f"Event: {show['name']}", severity=2,
                   entities={"show_id": show["id"], "winner_id": winner, "loser_id": loser})
        return

    # team scoring
    scores = []
    for team in teams:
        members = [db["workers"][pid] for pid in team]
        s = sum(star_score(p, fed_style) for p in members) / max(1,len(members))
        s += random.uniform(-3,3)
        scores.append(s)

    win_idx = 0 if scores[0] >= scores[1] else 1
    winners = teams[win_idx]; losers = teams[1-win_idx]
    method = random.choice(["pinfall","submission","KO/TKO","judges' decision"])
    time_s = random.randint(240, 1500)
    m["result"] = {"winners": winners, "losers": losers, "method": method, "time_s": time_s}
    wnames = ", ".join([db["workers"][wid]["ring_name"] for wid in winners])
    lnames = ", ".join([db["workers"][wid]["ring_name"] for wid in losers])
    m["recap_text"] = f"{wnames} defeated {lnames} by {method} at {time_s}s."
    add_ticker("MATCH_RESULT", f"{wnames} def. {lnames} by {method}",
               f"Event: {show['name']}", severity=2,
               entities={"show_id": show["id"], "winner_ids": winners, "loser_ids": losers})

def run_card(show_id):
    db = st.session_state.db
    ensure_card(show_id)
    show = db["shows"][show_id]
    matches = sorted([m for m in db["matches"].values() if m["show_id"]==show_id], key=lambda x: x["order"])
    if not matches:
        add_ticker("BOOKING_UPDATE", f"No matches available for {show['name']}", "Roster too thin?", severity=2)
        return
    for m in matches: run_match(m["id"])
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
        fed = db["federations"][s["federation_id"]]
        delta = max(-3, min(3, random.randint(-2,3)))
        fed["popularity"] = max(0, min(100, fed["popularity"] + delta))
