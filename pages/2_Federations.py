import streamlit as st
from fw.db import ss, create_fed, fed_employed_workers
from fw.models import FED_STYLES

ss(); db = st.session_state.db
st.header("Federations")

with st.expander("➕ Create Federation"):
    name = st.text_input("Name")
    style = st.selectbox("Style", FED_STYLES)
    c1,c2,c3 = st.columns(3)
    with c1: pop = st.slider("Popularity", 0, 100, 50)
    with c2: saf = st.slider("Safety", 0, 100, 50)
    with c3: liq = st.number_input("Liquidity", min_value=0, value=100000, step=10000)
    about = st.text_area("About", "")
    r1,r2,r3 = st.columns(3)
    with r1: allow_inter = st.checkbox("Allow intergender", value=(style in ("hardcore","lucha","sports_ent")))
    with r2: allow_tag = st.checkbox("Allow tag (2v2)", value=(style in ("sports_ent","hardcore","lucha")))
    with r3: allow_trios = st.checkbox("Allow trios (3v3)", value=(style in ("lucha",)))
    if st.button("Create Fed"):
        fid = create_fed(name, style, pop, saf, liq, about, allow_inter, allow_tag, allow_trios)
        st.success(f"Created {name} ({fid})")

for fid, fed in db["federations"].items():
    st.subheader(fed["name"])
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.write(f"Style: `{fed['style']}`")
    with c2: st.write(f"Popularity: {fed['popularity']}")
    with c3: st.write(f"Safety: {fed['safety']}")
    with c4: st.write(f"Liquidity: ${fed['liquidity']:,}")
    st.write(f"_About:_ {fed.get('about','')}")
    st.caption(f"Rules: intergender={'✅' if fed.get('allow_intergender') else '⛔'} • "
               f"tag={'✅' if fed.get('allow_tag') else '⛔'} • "
               f"trios={'✅' if fed.get('allow_trios') else '⛔'}")
    roster = fed_employed_workers(fid)
    st.write(f"**Roster** ({len(roster)}): " + ", ".join([w["ring_name"] for w in roster]) if roster else "_Empty_")
