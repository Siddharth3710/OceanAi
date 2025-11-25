import json
import re
import pandas as pd
import plotly.express as px
import streamlit as st
import os


from core.ingest import load_mock_inbox
from core.prompts import load_prompts, save_prompts
from core.agent import ask_grok, generate_reply_draft
from core.processing import run_ingestion_pipeline, load_processed
from core.dashboard import prepare_email_dataframe, get_keyword_counts
from core.drafts import load_drafts, save_drafts

# --------------------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------------------
st.set_page_config(
    page_title="Email Productivity Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------
# Custom CSS for Better UI
# --------------------------------------------------------------
st.markdown(
    """
<style>
    /* Main background and text */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 18px;
        font-weight: 600;
        color: #e2e8f0;
        padding: 10px 0;
    }
    
    /* Main content area */
    .main .block-container {
        padding: 2rem 3rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: 2rem auto;
    }
    
    /* Headers */
    h1 {
        color: #2d3748;
        font-weight: 700;
        border-bottom: 3px solid #667eea;
        padding-bottom: 15px;
        margin-bottom: 30px;
    }
    
    h2, h3 {
        color: #4a5568;
        font-weight: 600;
        margin-top: 25px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 28px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Text inputs and text areas */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        padding: 12px;
        font-size: 14px;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Info/Warning/Success boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
        padding: 15px 20px;
    }
    
    /* Cards effect for sections */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------
# Initialize Session State
# --------------------------------------------------------------
if "processed_data_loaded" not in st.session_state:
    st.session_state.processed_data_loaded = False

if "processed" not in st.session_state:
    st.session_state.processed = []

if "processed_by_id" not in st.session_state:
    st.session_state.processed_by_id = {}

# --------------------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------------------
st.sidebar.title("📧 Email Agent")
st.sidebar.markdown("---")
section = st.sidebar.radio(
    "Navigate to:",
    ["📥 Inbox", "🧠 Prompt Brain", "🤖 Email Agent", "📊 Insights Dashboard"],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Process your inbox first to enable all features!")

# --------------------------------------------------------------
# Load state data
# --------------------------------------------------------------
emails = load_mock_inbox()
prompts = load_prompts()
drafts = load_drafts()


# --------------------------------------------------------------
# Helper: Email Selector
# --------------------------------------------------------------
def select_email():
    if not emails:
        st.warning(
            "📭 No emails loaded yet. Put a mock_inbox.json in the data/ folder."
        )
        return None

    options = {f"📧 {e['subject']} — from {e['sender']}": e for e in emails}
    label = st.selectbox("Select an email:", list(options.keys()))
    return options[label]


# ==============================================================
# 📥 Inbox Section
# ==============================================================
if section == "📥 Inbox":
    st.title("📥 Inbox Viewer")
    st.markdown("View and process your emails with AI-powered categorization")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("🚀 Run Inbox Processing", use_container_width=True):
            try:
                with st.spinner("🤖 Processing emails with AI model..."):
                    processed = run_ingestion_pipeline()
                    st.session_state.processed = processed
                    st.session_state.processed_by_id = {p["id"]: p for p in processed}
                    st.session_state.processed_data_loaded = True
                st.success(f"✅ Successfully processed {len(processed)} emails!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error while processing inbox: {e}")

    st.markdown("---")

    if not emails:
        st.info("📭 No emails found. Please create data/mock_inbox.json.")
    else:
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📬 Total Emails", len(emails))
        with col2:
            processed_count = (
                len(st.session_state.processed)
                if st.session_state.processed_data_loaded
                else 0
            )
            st.metric("✅ Processed", processed_count)
        with col3:
            unique_senders = len(set(e.get("sender") for e in emails))
            st.metric("👥 Senders", unique_senders)
        with col4:
            if st.session_state.processed_data_loaded:
                urgent_count = sum(
                    1
                    for p in st.session_state.processed
                    if "urgent" in str(p.get("category", "")).lower()
                )
                st.metric("🔴 Urgent", urgent_count)
            else:
                st.metric("🔴 Urgent", "—")

        st.markdown("---")
        st.subheader("📋 Email List")

        # Display table
        table_data = []
        for e in emails:
            row = {
                "📌 ID": e.get("id", ""),
                "👤 Sender": e.get("sender", ""),
                "📧 Subject": e.get("subject", ""),
                "🕐 Time": e.get("timestamp", ""),
            }

            if st.session_state.processed_data_loaded:
                category = st.session_state.processed_by_id.get(e.get("id"), {}).get(
                    "category", ""
                )
                row["🏷️ Category"] = category
            else:
                row["🏷️ Category"] = "Not processed"

            table_data.append(row)

        st.dataframe(table_data, use_container_width=True, height=300)

        st.markdown("---")
        st.subheader("📄 Email Details")

        selected = select_email()
        if selected:
            eid = selected.get("id")

            # Email header in a card-like style
            st.markdown(
                f"""
            <div style='background: #f7fafc; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea;'>
                <p style='margin: 5px 0; color: #2d3748;'><strong>From:</strong> {selected.get('sender')}</p>
                <p style='margin: 5px 0; color: #2d3748;'><strong>Subject:</strong> {selected.get('subject')}</p>
                <p style='margin: 5px 0; color: #2d3748;'><strong>Time:</strong> {selected.get('timestamp')}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            if st.session_state.processed_data_loaded:
                processed_entry = st.session_state.processed_by_id.get(eid, {})
                category = processed_entry.get("category", "Not processed")
                st.markdown(f"**🏷️ Category:** `{category}`")
            else:
                st.info("💡 Click 'Run Inbox Processing' to categorize this email")

            st.markdown("---")
            st.markdown("**📝 Email Body:**")
            st.text_area(
                "",
                value=selected.get("body", ""),
                height=200,
                disabled=True,
                label_visibility="collapsed",
            )

            st.markdown("---")
            st.markdown("**✅ Action Items:**")

            if not st.session_state.processed_data_loaded:
                st.info("💡 Click 'Run Inbox Processing' to extract action items")
            else:
                processed_entry = st.session_state.processed_by_id.get(eid, {})
                actions = processed_entry.get("actions")

                if actions is None:
                    st.info("No action items found for this email")
                else:
                    if isinstance(actions, (dict, list)):
                        st.json(actions)
                    elif isinstance(actions, str):
                        cleaned = actions.strip()
                        if cleaned.startswith("```"):
                            cleaned = (
                                cleaned.replace("```json", "")
                                .replace("```", "")
                                .strip()
                            )
                        cleaned = re.sub(
                            r"^\s*\d+\s*:\s*", "", cleaned, flags=re.MULTILINE
                        )
                        cleaned = cleaned.replace("\r", " ").replace("\n", " ").strip()

                        try:
                            parsed = json.loads(cleaned)
                            st.json(parsed)
                        except Exception:
                            st.text(actions)
                    else:
                        st.text(str(actions))


# ==============================================================
# 🧠 Prompt Brain Section
# ==============================================================
elif section == "🧠 Prompt Brain":
    st.title("🧠 Prompt Brain")
    st.markdown("Configure AI behavior by customizing prompts")

    prompts = load_prompts()

    st.markdown("---")

    with st.form("prompt_form"):
        st.subheader("📂 Categorization Prompt")
        st.caption("Controls how emails are categorized")
        categorization_prompt = st.text_area(
            "Categorization Prompt",
            value=prompts.get("categorization_prompt", ""),
            height=120,
            label_visibility="collapsed",
        )

        st.markdown("")
        st.subheader("✅ Action Item Extraction Prompt")
        st.caption("Controls how tasks are extracted from emails")
        action_item_prompt = st.text_area(
            "Action Item Extraction Prompt",
            value=prompts.get("action_item_prompt", ""),
            height=120,
            label_visibility="collapsed",
        )

        st.markdown("")
        st.subheader("✉️ Auto-Reply Draft Prompt")
        st.caption("Controls the style of generated reply drafts")
        auto_reply_prompt = st.text_area(
            "Auto-Reply Draft Prompt",
            value=prompts.get("auto_reply_prompt", ""),
            height=120,
            label_visibility="collapsed",
        )

        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button(
                "💾 Save Prompts", use_container_width=True
            )

        if submitted:
            prompts["categorization_prompt"] = categorization_prompt
            prompts["action_item_prompt"] = action_item_prompt
            prompts["auto_reply_prompt"] = auto_reply_prompt

            save_prompts(prompts)
            st.success("✅ Prompts saved successfully!")
            st.info("💡 New prompts will be used in the next operation")


# ==============================================================
# 🤖 Email Agent
# ==============================================================
elif section == "🤖 Email Agent":
    st.title("🤖 Email Agent")
    st.markdown("Interact with your emails using AI assistance")

    selected = select_email()
    if not selected:
        st.info("👆 Select an email from the dropdown to get started")
    else:
        # Email preview card
        st.markdown("### 📧 Selected Email")
        st.markdown(
            f"""
        <div style='background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <p style='margin: 8px 0; color: #2d3748;'><strong>From:</strong> {selected.get('sender')}</p>
            <p style='margin: 8px 0; color: #2d3748;'><strong>Subject:</strong> {selected.get('subject')}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.expander("📄 View Full Email Body"):
            st.text(selected.get("body"))

        # Free-form agent
        st.markdown("---")
        st.subheader("💬 Ask the Agent")
        st.caption(
            "Ask questions about this email: summarize, extract tasks, analyze tone, etc."
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            user_query = st.text_input(
                "Your question:",
                placeholder="e.g., What are the main points? What should I do?",
                label_visibility="collapsed",
            )
        with col2:
            run_agent = st.button("🚀 Ask", use_container_width=True)

        if run_agent:
            if not user_query:
                st.warning("⚠️ Please type a question first")
            else:
                with st.spinner("🤔 Thinking..."):
                    try:
                        output = ask_grok(user_query, selected)
                        st.markdown("**💡 Agent Response:**")
                        st.markdown(
                            f"""
                        <div style='background: #f7fafc; padding: 20px; border-radius: 10px; border-left: 4px solid #48bb78;'>
                            {output}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

        # Reply draft
        st.markdown("---")
        st.subheader("✉️ Reply Draft Generator")
        st.caption("Generate and edit AI-powered reply drafts")

        draft_text = st.session_state.get("reply_draft_text", "")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✨ Auto-generate Reply Draft", use_container_width=True):
                with st.spinner("✍️ Generating reply..."):
                    try:
                        current_prompts = load_prompts()
                        generated = generate_reply_draft(selected)
                        st.session_state["reply_draft_text"] = generated
                        draft_text = generated
                        st.success("✅ Draft generated!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

        draft_text = st.text_area(
            "Reply Draft (editable):",
            value=draft_text,
            height=250,
            key="reply_draft_editor",
            placeholder="Click 'Auto-generate Reply Draft' to create a draft...",
        )

        with col2:
            if st.button("💾 Save Draft", use_container_width=True):
                if not draft_text.strip():
                    st.warning("⚠️ Draft is empty!")
                else:
                    followups = []
                    if "Followups:" in draft_text:
                        after = draft_text.split("Followups:", 1)[1]
                        lines = after.split("\n")
                        for ln in lines:
                            ln = ln.strip("-• ").strip()
                            if ln:
                                followups.append(ln)

                    if st.session_state.processed_data_loaded:
                        processed_entry = st.session_state.processed_by_id.get(
                            selected.get("id"), {}
                        )
                        metadata = {
                            "category": processed_entry.get("category"),
                            "actions": processed_entry.get("actions"),
                        }
                    else:
                        metadata = {}

                    new_draft = {
                        "email_id": selected.get("id"),
                        "original_subject": selected.get("subject"),
                        "draft_subject": f"Re: {selected.get('subject')}",
                        "draft_body": draft_text.strip(),
                        "suggested_followups": followups,
                        "metadata": metadata,
                    }

                    existing = load_drafts()
                    existing.append(new_draft)
                    save_drafts(existing)

                    st.success("✅ Draft saved successfully!")
                    st.balloons()


# ==============================================================
# 📊 Insights Dashboard
# ==============================================================
elif section == "📊 Insights Dashboard":
    st.title("📊 Inbox Insights Dashboard")
    st.markdown("Visualize your email patterns and productivity metrics")

    if not st.session_state.processed_data_loaded:
        st.info(
            "📭 No processed data available. Please go to the 📥 Inbox section and click 'Run Inbox Processing' first."
        )
    else:
        processed_dashboard = st.session_state.processed

        if not processed_dashboard:
            st.info("No emails were processed")
        else:
            df = prepare_email_dataframe(processed_dashboard)

            if df.empty:
                st.info("No valid data to analyze")
            else:
                # Metrics with icons
                st.subheader("📈 Overview")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📧 Total Emails", len(df))
                with col2:
                    st.metric("👥 Unique Senders", df["sender"].nunique())
                with col3:
                    st.metric(
                        "✅ To-Do Emails",
                        int(
                            df["category"]
                            .str.contains("to-do", case=False, na=False)
                            .sum()
                        ),
                    )
                with col4:
                    st.metric(
                        "🔴 High Priority", int((df["priority_label"] == "HIGH").sum())
                    )

                st.markdown("---")

                # Category Chart
                st.markdown("### 📊 Category Distribution")
                cat_df = df["category"].value_counts().reset_index()
                cat_df.columns = ["category", "count"]
                fig = px.bar(
                    cat_df,
                    x="category",
                    y="count",
                    color="count",
                    color_continuous_scale="purples",
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

                # Top Senders
                st.markdown("### 👥 Top Senders")
                snd_df = df["sender"].value_counts().reset_index()
                snd_df.columns = ["sender", "count"]
                fig2 = px.bar(
                    snd_df.head(10),
                    x="sender",
                    y="count",
                    color="count",
                    color_continuous_scale="blues",
                )
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

                # Timeline
                st.markdown("### 📅 Email Timeline")
                if "timestamp" in df.columns:
                    df2 = df.copy()
                    df2["date"] = pd.to_datetime(df2["timestamp"]).dt.date
                    vol = df2.groupby("date")["id"].count().reset_index()
                    vol.columns = ["date", "email_count"]
                    fig3 = px.line(vol, x="date", y="email_count", markers=True)
                    fig3.update_traces(line_color="#667eea", line_width=3)
                    st.plotly_chart(fig3, use_container_width=True)

                # Keywords
                st.markdown("### 🔤 Keyword Frequency")
                kws = get_keyword_counts(df, top_n=20)
                if kws:
                    kw_df = pd.DataFrame(kws, columns=["keyword", "count"])
                    fig4 = px.bar(
                        kw_df,
                        x="keyword",
                        y="count",
                        color="count",
                        color_continuous_scale="greens",
                    )
                    fig4.update_layout(showlegend=False)
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Not enough text for keyword analysis")

    # Show drafts section
    st.markdown("---")
    st.markdown("### 📝 Saved Drafts")
    drafts = load_drafts()
    if drafts:
        draft_data = []
        for d in drafts:
            draft_data.append(
                {
                    "📌 Email ID": d["email_id"],
                    "📧 Subject": d["draft_subject"],
                    "📋 Follow-ups": ", ".join(d.get("suggested_followups", []))
                    or "None",
                    "🏷️ Category": d.get("metadata", {}).get("category", "N/A"),
                }
            )
        st.dataframe(draft_data, use_container_width=True)
    else:
        st.info("📭 No drafts saved yet")
