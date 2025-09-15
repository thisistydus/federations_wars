import streamlit as st
from fw.db import ss, create_worker, employ_worker, current_week
from fw.models import FED_STYLES, GENDERS
ss(); db = st.session_state.db

st.header("Workers")

with st.expander("➕ Create Worker"):
    ring = st.text_input("Ring name")
    style = st.selectbox("Style", FED_STYLES, key="w_style")
    align = st.selectbox("Alignment", ["face","heel","neutral"])
    gender = st.selectbox("Gender", GENDERS, index=0)
    c1,c2,c3,c4 = st.columns(4)
    with c1: skill = st.slider("Skill", 0, 100, 60)
    with c2: ch = st.slider("Charisma", 0, 100, 60)
    with c3: pr = st.slider("Prestige", 0, 100, 40)
    with c4: rk = st.slider("Risk", 0, 100, 30)
    bio = st.text_area("Short bio", "")
    if st.button("Create Worker"):
        wid = create_worker(ring, style, align, skill, ch, pr, rk, bio, gender)
        st.success(f"Created {ring} ({wid})")

st.subheader("Hire / Transfer")
if db["workers"] and db["federations"]:
    wid = st.selectbox("Worker", list(db["workers"].keys()), format_func=lambda i: db["workers"][i]["ring_name"], key="hire_w")
    fid = st.selectbox("Federation", list(db["federations"].keys()), format_func=lambda i: db["federations"][i]["name"], key="hire_f")
    masked = st.checkbox("Perform masked in this federation?", value=False)
    if st.button("Employ (start this week)"):
        employ_worker(wid, fid, start_week=current_week(), masked=masked)
        st.success("Employment added.")

st.divider()
for wid, w in db["workers"].items():
    st.write(f"**{w['ring_name']}** — `{w['style']}` ({w['alignment']}, {w.get('gender','?')}) | "
             f"Skill {w['skill']} • Cha {w['charisma']} • Pres {w['prestige']} • Risk {w['risk']}")
    jobs = [e for e in db["employment"] if e["worker_id"]==wid]
    if jobs:
        st.caption("Employment: " + "; ".join([
            f"{db['federations'][e['fed_id']]['name']} "
            f"({'Masked' if e.get('masked') else 'Unmasked'}) "
            f"(wk {e['start_week']}→{e['end_week'] or '…'})"
            for e in jobs
        ]))
    else:
        st.caption("_No employment records_")
