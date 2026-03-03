import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="ITS Comparison Tool", layout="wide")

# -----------------------------
# Utility: Very-loose normalization
# -----------------------------
def normalize_skill(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)  # remove punctuation + whitespace
    return name


# -----------------------------
# Initialize session_state
# -----------------------------
if "master_list" not in st.session_state:
    if os.path.exists("master_skill_list.csv"):
        df = pd.read_csv("master_skill_list.csv", encoding="utf-8-sig")

        # Force correct header
        if df.shape[1] == 1:
            df.columns = ["Skill Name"]
        else:
            df = df.iloc[:, [0]]
            df.columns = ["Skill Name"]

        st.session_state.master_list = df
    else:
        st.session_state.master_list = pd.DataFrame({"Skill Name": []})

if "expected_tasks" not in st.session_state:
    st.session_state.expected_tasks = pd.DataFrame(columns=["UserID", "Skill Name", "NormSkill"])

if "its_data" not in st.session_state:
    st.session_state.its_data = pd.DataFrame()


# -----------------------------
# Save master list to CSV
# -----------------------------
def save_master_list():
    st.session_state.master_list.to_csv("master_skill_list.csv", index=False)


# -----------------------------
# Tabs
# -----------------------------
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
    remove_skill = st.selectbox("Select Skill to Remove", [""] + list(st.session_state.master_list["Skill Name"]))

    if st.button("Remove Skill"):
        if remove_skill:
            st.session_state.master_list = st.session_state.master_list[
                st.session_state.master_list["Skill Name"] != remove_skill
            ]
            save_master_list()
            st.experimental_rerun()


# ============================================================
# TAB 2 — EXPECTED TASK BUILDER
# ============================================================
with tab2:
    st.header("Expected Task Builder")

# DEBUG: show column names
    st.write("Master list columns:", st.session_state.master_list.columns)
    st.write("Expected tasks columns:", st.session_state.expected_tasks.columns)

    user_id = st.text_input("User ID")

    skill_choices = st.multiselect(
        "Select Skill Names",
        options=list(st.session_state.master_list["Skill Name"]),
        default=st.session_state.get("last_selected_skills", []),
    )

    if st.button("Add Tasks for User"):
        if user_id.strip() and skill_choices:
            st.session_state.last_selected_skills = skill_choices

            for skill in skill_choices:
                norm = normalize_skill(skill)

                duplicate = (
                    (st.session_state.expected_tasks["UserID"] == user_id)
                    & (st.session_state.expected_tasks["NormSkill"] == norm)
                ).any()

                if not duplicate:
                    st.session_state.expected_tasks.loc[len(st.session_state.expected_tasks)] = [
                        user_id,
                        skill,
                        norm,
                    ]

            st.experimental_rerun()

    st.subheader("Expected Task List (All Users)")
    st.dataframe(st.session_state.expected_tasks, use_container_width=True)


# ============================================================
# TAB 3 — ITS COMPARISON
# ============================================================
with tab3:
    st.header("ITS Report Comparison")

    uploaded = st.file_uploader("Upload ITS Excel File", type=["xlsx"])

    if uploaded:
        df = pd.read_excel(uploaded)
        required_cols = ["User Id", "Skill Name", "Status", "Method", "Evaluator"]

        if not all(col in df.columns for col in required_cols):
            st.error("Uploaded file is missing required ITS columns.")
        else:
            df["NormSkill"] = df["Skill Name"].apply(normalize_skill)
            st.session_state.its_data = df

            st.subheader("ITS Data Preview")
            st.dataframe(df, use_container_width=True)

    if not st.session_state.its_data.empty and not st.session_state.expected_tasks.empty:
        st.subheader("Comparison Results")

        its_df = st.session_state.its_data
        exp_df = st.session_state.expected_tasks
        master_norm = set(st.session_state.master_list["Skill Name"].apply(normalize_skill))

        # Missing tasks
        merged = exp_df.merge(
            its_df,
            left_on=["UserID", "NormSkill"],
            right_on=["User Id", "NormSkill"],
            how="left",
            indicator=True,
        )
        missing = merged[merged["_merge"] == "left_only"][["UserID", "Skill Name"]]

        # Unexpected tasks
        merged2 = its_df.merge(
            exp_df,
            left_on=["User Id", "NormSkill"],
            right_on=["UserID", "NormSkill"],
            how="left",
            indicator=True,
        )
        unexpected = merged2[merged2["_merge"] == "left_only"][
            ["User Id", "Skill Name", "Status", "Evaluator", "Method"]
        ]

        # Invalid skill names
        invalid = its_df[~its_df["NormSkill"].isin(master_norm)][
            ["User Id", "Skill Name", "Status", "Evaluator", "Method"]
        ]

        # Failed tasks
        failed = its_df[its_df["Status"].str.lower() == "failed"][
            ["User Id", "Skill Name", "Status", "Evaluator", "Method"]
        ]

        # Multiple attempts
        duplicates = (
            its_df.groupby(["User Id", "NormSkill"])
            .size()
            .reset_index(name="Attempts")
        )
        duplicates = duplicates[duplicates["Attempts"] > 1]

        st.write("Missing Tasks")
        st.dataframe(missing, use_container_width=True)

        st.write("Unexpected Tasks")
        st.dataframe(unexpected, use_container_width=True)

        st.write("Invalid Skill Names")
        st.dataframe(invalid, use_container_width=True)

        st.write("Failed Tasks")
        st.dataframe(failed, use_container_width=True)

        st.write("Multiple Attempts")
        st.dataframe(duplicates, use_container_width=True)

