import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="ITS Comparison Tool", layout="wide")

# ============================================================
# SIDEBAR RESET BUTTON — SAFE (NO INFINITE LOOP)
# ============================================================
with st.sidebar:
    if st.button("Reset App State"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

# ============================================================
# NORMALIZATION UTILITY
# ============================================================
def normalize_skill(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name

# ============================================================
# MASTER LIST INITIALIZATION
# ============================================================
if "master_list" not in st.session_state:
    if os.path.exists("master_skill_list.csv"):
        df = pd.read_csv("master_skill_list.csv", encoding="utf-8-sig")

        # Clean header
        df.columns = [str(c).strip() for c in df.columns]

        # Force single correct column
        df = df.iloc[:, [0]]
        df.columns = ["Skill Name"]

        st.session_state.master_list = df
    else:
        st.session_state.master_list = pd.DataFrame({"Skill Name": []})

# ============================================================
# EXPECTED TASKS INITIALIZATION
# ============================================================
if "expected_tasks" not in st.session_state:
    st.session_state.expected_tasks = pd.DataFrame(
        columns=["UserID", "Skill Name", "NormSkill"]
    )

# FORCE correct structure
expected_cols = ["UserID", "Skill Name", "NormSkill"]
if list(st.session_state.expected_tasks.columns) != expected_cols:
    st.session_state.expected_tasks = pd.DataFrame(columns=expected_cols)

# ============================================================
# ITS DATA INITIALIZATION
# ============================================================
if "its_data" not in st.session_state:
    st.session_state.its_data = pd.DataFrame()

# ============================================================
# SAVE MASTER LIST
# ============================================================
def save_master_list():
    st.session_state.master_list.to_csv("master_skill_list.csv", index=False)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3 = st.tabs(["Master Skill List", "Expected Tasks", "ITS Comparison"])

# ============================================================
# TAB 1 — MASTER SKILL LIST
# ============================================================
with tab1:
    st.header("Master Skill Name List")

    st.subheader("Current Skills")
    st.dataframe(st.session_state.master_list, use_container_width=True)

    st.subheader("Add a New Skill")
    new_skill = st.text_input("Skill Name to Add")

    if st.button("Add Skill"):
        if new_skill.strip():
            if new_skill not in st.session_state.master_list["Skill Name"].values:
                st.session_state.master_list.loc[len(st.session_state.master_list)] = [new_skill]
                save_master_list()
                st.experimental_rerun()

    st.subheader("Remove a Skill")
    remove_skill = st.selectbox(
        "Select Skill to Remove
