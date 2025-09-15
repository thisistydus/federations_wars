import streamlit as st
from fw.db import ss, current_week
ss()

db = st.session_state.db
st.header("Dashboard")
c1,c2,c3 = st.columns(3)

with c1:
    st.subheader("Federations")
    for f in db["federations"].values():
        st.write(f"**{f['name']}** — style: `{f['style']}`, pop: {f['popularity']}, safety: {f['safety']}")
        st.caption(f"Rules: intergender={'✅' if f.get('allow_intergender') else '⛔'} • "
                   f"tag={'✅' if f.get('allow_tag') else '⛔'} • "
                   f"trios={'✅' if f.get('allow_trios') else '⛔'}")

with c2:
    st.subheader("Upcoming (this week)")
    wk = current_week()
    ups = [s for s in db["shows"].values() if s["scheduled_week"]==wk and s["status"]=="upcoming"]
    if ups:
        for s in sorted(ups, key=lambda x: x["name"]):
            fed = db["federations"][s["federation_id"]]["name"]
            st.write(f"• **{s['name']}** ({fed}) — Week {s['scheduled_week']}")
    else:
        st.write("_None scheduled this week._")

with c3:
    st.subheader("Stats")
    st.write(f"Workers: {len(db['workers'])}")
    st.write(f"Feds: {len(db['federations'])}")
    st.write(f"Shows: {len(db['shows'])}")
