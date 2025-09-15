import streamlit as st
from fw.db import ss, seed_demo, export_universe_json, import_universe_json, current_week
from fw.sim.engine import run_all_cards_this_week
from fw.logic import universe as uni  # for schedule utils if you add later

st.set_page_config(page_title="Federation Wars — Alpha", layout="wide")
ss()  # ensure db exists

with st.sidebar:
    st.title("Federation Wars α")
    st.caption("Text sim • early alpha")
    st.metric("In-game Week", current_week())

    if st.button("Seed Demo Data"):
        seed_demo()
        st.success("Seeded demo data.")

    if st.button("Run All Cards (This Week)"):
        run_all_cards_this_week()

    if st.button("Skip Time (+1 week)"):
        uni.skip_time()

    st.divider()
    st.subheader("Save / Load")
    st.download_button(
        "Download universe.json",
        data=export_universe_json(),
        file_name="universe.json",
        mime="application/json"
    )
    uploaded = st.file_uploader("Load JSON", type=["json"])
    if uploaded:
        try:
            import_universe_json(uploaded.read().decode("utf-8"))
            st.success("Loaded universe.json")
        except Exception as e:
            st.error(f"Import failed: {e}")

# Small ticker strip visible on every page
def render_ticker_strip(n=6):
    events = st.session_state.db["ticker"][:n]
    if events:
        line = " | ".join([f"[{e['type']}] {e['headline']}" for e in events])
        st.info(line, icon="📰")

render_ticker_strip()

st.write("Use the **Pages** menu (left sidebar) to navigate → Dashboard / Federations / Workers / Shows / News.")
