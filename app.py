# app.py
# ---------------------------------------------------------------
# Football Player Performance Analytics Dashboard
# All data loaded from football_players.csv is SYNTHETIC.
# It does not represent any real player, club, or match result.
# ---------------------------------------------------------------

import os
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ── Page config (must be first Streamlit call) ─────────────────
st.set_page_config(
    page_title="Football Analytics Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global theme constants ─────────────────────────────────────
BG_COLOR        = "#0d1b0e"
SURFACE_COLOR   = "#122614"
ACCENT_GREEN    = "#00c853"
ACCENT_YELLOW   = "#ffd600"
TEXT_COLOR      = "#e8f5e9"
MUTED_COLOR     = "#81c784"
PLOTLY_TEMPLATE = "plotly_dark"

CHART_LAYOUT = dict(
    paper_bgcolor=SURFACE_COLOR,
    plot_bgcolor=SURFACE_COLOR,
    font=dict(color=TEXT_COLOR, family="Segoe UI, Arial, sans-serif"),
    margin=dict(l=40, r=30, t=50, b=40),
)

POSITION_ORDER  = ["GK", "DEF", "MID", "FWD"]
POSITION_COLORS = {
    "GK":  "#ffd600",
    "DEF": "#00e676",
    "MID": "#40c4ff",
    "FWD": "#ff6d00",
}

# ── Custom CSS injection ───────────────────────────────────────
def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        /* Main background */
        .stApp {{
            background-color: {BG_COLOR};
            color: {TEXT_COLOR};
        }}
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {SURFACE_COLOR};
        }}
        /* Metric cards */
        [data-testid="metric-container"] {{
            background-color: {SURFACE_COLOR};
            border: 1px solid #1e4023;
            border-radius: 8px;
            padding: 12px;
        }}
        /* Headers */
        h1, h2, h3, h4 {{
            color: {ACCENT_GREEN} !important;
        }}
        /* Tabs */
        .stTabs [data-baseweb="tab"] {{
            color: {MUTED_COLOR};
        }}
        .stTabs [aria-selected="true"] {{
            color: {ACCENT_GREEN} !important;
            border-bottom-color: {ACCENT_GREEN} !important;
        }}
        /* Dataframe */
        [data-testid="stDataFrame"] {{
            border: 1px solid #1e4023;
            border-radius: 6px;
        }}
        /* Info / warning banners */
        .stAlert {{
            background-color: {SURFACE_COLOR};
        }}
        /* Divider */
        hr {{
            border-color: #1e4023;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Data loading ───────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = os.path.join(os.path.dirname(__file__), "football_players.csv")
    if not os.path.exists(csv_path):
        st.error(
            "**football_players.csv not found.**  \n"
            "Run `python generate_data.py` in the project directory to create it, "
            "then refresh this page."
        )
        st.stop()

    df = pd.read_csv(csv_path)

    # ── Basic validation ──────────────────────────────────────
    required_cols = {
        "player_id", "player_name", "team", "position", "season",
        "age", "goals", "assists", "shots", "shots_on_target",
        "minutes_played", "pass_accuracy", "dribbles_completed",
        "tackles", "yellow_cards", "red_cards", "player_rating",
        "nationality",
    }
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"CSV is missing expected columns: {missing}")
        st.stop()

    # Fill any accidental nulls with sensible defaults
    numeric_cols = df.select_dtypes(include="number").columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    df["player_name"] = df["player_name"].fillna("Unknown")
    df["team"]        = df["team"].fillna("Unknown")
    df["position"]    = df["position"].fillna("Unknown")
    df["season"]      = df["season"].fillna("Unknown")
    df["nationality"] = df["nationality"].fillna("Unknown")

    return df


# ── Sidebar filters ────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame):
    """
    Render sidebar filter widgets.
    Returns (filtered_df, selected_players_for_comparison).
    """
    st.sidebar.markdown(
        f"<h2 style='color:{ACCENT_GREEN};'>⚽ Filters</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<small style='color:#81c784;'>⚠️ All data is synthetic — "
        "not real-world football statistics.</small>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    # Season
    seasons     = ["All Seasons"] + sorted(df["season"].unique().tolist())
    sel_season  = st.sidebar.selectbox("Season", seasons, index=0)

    # Team
    all_teams   = sorted(df["team"].unique().tolist())
    sel_teams   = st.sidebar.multiselect("Team", all_teams, default=[])

    # Position
    all_pos     = [p for p in POSITION_ORDER if p in df["position"].unique()]
    sel_pos     = st.sidebar.multiselect("Position", all_pos, default=[])

    # ── Apply filters ─────────────────────────────────────────
    filtered = df.copy()
    if sel_season != "All Seasons":
        filtered = filtered[filtered["season"] == sel_season]
    if sel_teams:
        filtered = filtered[filtered["team"].isin(sel_teams)]
    if sel_pos:
        filtered = filtered[filtered["position"].isin(sel_pos)]

    # Player (cascades from above filters)
    all_players  = sorted(filtered["player_name"].unique().tolist())
    sel_players  = st.sidebar.multiselect(
        "Compare Players (Player Analysis)",
        all_players,
        default=[],
        help="Select 2–5 players to compare on the Player Analysis page.",
    )

    # Row count badge
    st.sidebar.markdown("---")
    st.sidebar.metric("Players shown", len(filtered))

    if filtered.empty:
        st.warning(
            "No players match the current filters. "
            "Please adjust the sidebar selections."
        )

    return filtered, sel_players


# ── CSV download button ────────────────────────────────────────
def render_download_button(df: pd.DataFrame) -> None:
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Download Filtered Data (CSV)",
        data=csv_bytes,
        file_name="football_players_filtered.csv",
        mime="text/csv",
        help="Downloads the currently filtered dataset as a CSV file.",
    )


# ── Helper: apply chart layout defaults ───────────────────────
def _style_fig(fig, title: str = "") -> go.Figure:
    updates = dict(**CHART_LAYOUT)
    if title:
        updates["title"] = dict(
            text=title,
            font=dict(size=16, color=TEXT_COLOR),
            x=0.01,
        )
    fig.update_layout(**updates)
    fig.update_xaxes(gridcolor="#1e4023", zerolinecolor="#1e4023")
    fig.update_yaxes(gridcolor="#1e4023", zerolinecolor="#1e4023")
    return fig


# ── Page: Overview ─────────────────────────────────────────────
def render_overview(df: pd.DataFrame) -> None:
    st.markdown("## Overview")
    st.info(
        "**Synthetic Data Notice** — All statistics are procedurally generated "
        "for demonstration purposes. They do not reflect any real football players, "
        "clubs, or competitions."
    )

    if df.empty:
        st.warning("No data to display. Adjust the sidebar filters.")
        return

    # ── KPI cards ─────────────────────────────────────────────
    total_players   = len(df)
    total_goals     = int(df["goals"].sum())
    total_assists   = int(df["assists"].sum())
    total_minutes   = int(df["minutes_played"].sum())
    avg_rating      = round(float(df["player_rating"].mean()), 2)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Players",      f"{total_players:,}")
    c2.metric("Total Goals",        f"{total_goals:,}")
    c3.metric("Total Assists",      f"{total_assists:,}")
    c4.metric("Total Minutes",      f"{total_minutes:,}")
    c5.metric("Avg Player Rating",  f"{avg_rating}")

    st.markdown("---")

    # ── Top 10 scorers ────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        top10 = (
            df.nlargest(10, "goals")[["player_name", "team", "position", "goals"]]
            .sort_values("goals")
        )
        fig_top = px.bar(
            top10,
            x="goals",
            y="player_name",
            orientation="h",
            color="position",
            color_discrete_map=POSITION_COLORS,
            hover_data=["team", "position"],
            labels={"goals": "Goals", "player_name": "Player"},
            template=PLOTLY_TEMPLATE,
        )
        _style_fig(fig_top, "Top 10 Goal Scorers")
        st.plotly_chart(fig_top, use_container_width=True)

    # ── Rating distribution ───────────────────────────────────
    with col_right:
        fig_hist = px.histogram(
            df,
            x="player_rating",
            nbins=20,
            color_discrete_sequence=[ACCENT_GREEN],
            labels={"player_rating": "Player Rating", "count": "Number of Players"},
            template=PLOTLY_TEMPLATE,
        )
        _style_fig(fig_hist, "Player Rating Distribution")
        fig_hist.update_layout(bargap=0.05)
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # ── Goals by team ─────────────────────────────────────────
    team_goals = (
        df.groupby("team", as_index=False)["goals"]
        .sum()
        .sort_values("goals", ascending=False)
    )
    fig_team = px.bar(
        team_goals,
        x="team",
        y="goals",
        color_discrete_sequence=[ACCENT_GREEN],
        labels={"team": "Team", "goals": "Total Goals"},
        template=PLOTLY_TEMPLATE,
    )
    _style_fig(fig_team, "Total Goals by Team")
    st.plotly_chart(fig_team, use_container_width=True)


# ── Page: Player Analysis ──────────────────────────────────────
def render_player_analysis(df: pd.DataFrame, selected_players: list) -> None:
    st.markdown("## Player Analysis")

    if df.empty:
        st.warning("No data to display. Adjust the sidebar filters.")
        return

    # ── Goals vs Assists scatter ───────────────────────────────
    st.markdown("### Goals vs Assists")
    fig_ga = px.scatter(
        df,
        x="assists",
        y="goals",
        color="position",
        color_discrete_map=POSITION_COLORS,
        size="minutes_played",
        size_max=18,
        hover_name="player_name",
        hover_data={
            "team": True,
            "player_rating": True,
            "minutes_played": True,
            "position": True,
        },
        labels={
            "assists": "Assists",
            "goals": "Goals",
            "minutes_played": "Minutes Played",
            "player_rating": "Rating",
        },
        template=PLOTLY_TEMPLATE,
    )
    _style_fig(fig_ga, "Goals vs Assists (bubble size = minutes played)")
    st.plotly_chart(fig_ga, use_container_width=True)

    st.markdown("---")

    # ── Shots vs Goals scatter with trendline ─────────────────
    st.markdown("### Shots vs Goals — Shot Conversion")
    fig_sg = px.scatter(
        df,
        x="shots",
        y="goals",
        color="team",
        trendline="ols",
        hover_name="player_name",
        hover_data={"position": True, "shots_on_target": True},
        labels={"shots": "Total Shots", "goals": "Goals Scored"},
        template=PLOTLY_TEMPLATE,
    )
    _style_fig(fig_sg, "Shots vs Goals with OLS Trendline")
    st.plotly_chart(fig_sg, use_container_width=True)

    st.markdown("---")

    # ── Multi-player comparison ────────────────────────────────
    st.markdown("### Player Comparison")

    if len(selected_players) < 2:
        st.info(
            "Select **2 to 5 players** in the sidebar 'Compare Players' filter "
            "to see a side-by-side comparison."
        )
    else:
        comp_df = df[df["player_name"].isin(selected_players[:5])].copy()
        stat_cols = [
            "goals", "assists", "shots_on_target",
            "pass_accuracy", "dribbles_completed", "tackles", "player_rating",
        ]
        # Normalise 0–1 per column for fair comparison
        norm_df = comp_df[["player_name"] + stat_cols].copy()
        for col in stat_cols:
            col_min = norm_df[col].min()
            col_max = norm_df[col].max()
            denom = col_max - col_min if col_max != col_min else 1
            norm_df[col] = (norm_df[col] - col_min) / denom

        melted = norm_df.melt(
            id_vars="player_name",
            value_vars=stat_cols,
            var_name="Stat",
            value_name="Normalised Value",
        )

        fig_comp = px.bar(
            melted,
            x="Stat",
            y="Normalised Value",
            color="player_name",
            barmode="group",
            labels={
                "Stat": "Attribute",
                "Normalised Value": "Normalised Score (0-1)",
                "player_name": "Player",
            },
            template=PLOTLY_TEMPLATE,
        )
        _style_fig(fig_comp, "Player Attribute Comparison (Normalised 0–1)")
        st.plotly_chart(fig_comp, use_container_width=True)

        # Raw stats table for selected players
        st.markdown("**Raw statistics for selected players**")
        st.dataframe(
            comp_df[["player_name", "team", "position", "season"] + stat_cols]
            .set_index("player_name")
            .style.format(precision=1),
            use_container_width=True,
        )

    st.markdown("---")

    # ── Searchable player statistics table ────────────────────
    st.markdown("### Player Statistics Table")
    search = st.text_input("Search player by name", placeholder="e.g. Marco Silva")
    display_df = df.copy()
    if search.strip():
        display_df = display_df[
            display_df["player_name"].str.contains(search.strip(), case=False, na=False)
        ]
        if display_df.empty:
            st.warning(f"No players found matching '{search}'.")

    show_cols = [
        "player_name", "team", "position", "season", "age",
        "goals", "assists", "shots", "shots_on_target", "minutes_played",
        "pass_accuracy", "player_rating", "nationality",
    ]
    st.dataframe(
        display_df[show_cols].sort_values("player_rating", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


# ── Page: Team Analysis ────────────────────────────────────────
def render_team_analysis(df: pd.DataFrame) -> None:
    st.markdown("## Team Analysis")

    if df.empty:
        st.warning("No data to display. Adjust the sidebar filters.")
        return

    # ── Goals + Assists grouped bar ────────────────────────────
    team_agg = (
        df.groupby("team", as_index=False)[["goals", "assists"]]
        .sum()
        .sort_values("goals", ascending=False)
    )
    fig_ta = px.bar(
        team_agg,
        x="team",
        y=["goals", "assists"],
        barmode="group",
        color_discrete_sequence=[ACCENT_GREEN, ACCENT_YELLOW],
        labels={"team": "Team", "value": "Count", "variable": "Stat"},
        template=PLOTLY_TEMPLATE,
    )
    _style_fig(fig_ta, "Total Goals and Assists by Team")
    st.plotly_chart(fig_ta, use_container_width=True)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    # ── Squad size ────────────────────────────────────────────
    with col_left:
        squad = (
            df.groupby("team", as_index=False)["player_id"]
            .count()
            .rename(columns={"player_id": "squad_size"})
            .sort_values("squad_size", ascending=False)
        )
        fig_sq = px.bar(
            squad,
            x="team",
            y="squad_size",
            color_discrete_sequence=[MUTED_COLOR],
            labels={"team": "Team", "squad_size": "Number of Players"},
            template=PLOTLY_TEMPLATE,
        )
        _style_fig(fig_sq, "Squad Size by Team")
        st.plotly_chart(fig_sq, use_container_width=True)

    # ── Average rating per team ───────────────────────────────
    with col_right:
        avg_rat = (
            df.groupby("team", as_index=False)["player_rating"]
            .mean()
            .round(2)
            .sort_values("player_rating", ascending=False)
        )
        fig_rat = px.bar(
            avg_rat,
            x="team",
            y="player_rating",
            color_discrete_sequence=[ACCENT_YELLOW],
            labels={"team": "Team", "player_rating": "Avg Player Rating"},
            template=PLOTLY_TEMPLATE,
        )
        _style_fig(fig_rat, "Average Player Rating by Team")
        st.plotly_chart(fig_rat, use_container_width=True)

    st.markdown("---")

    # ── Top players per team ──────────────────────────────────
    st.markdown("### Top Scorer per Team")
    top_per_team = (
        df.sort_values("goals", ascending=False)
        .groupby("team", as_index=False)
        .first()[["team", "player_name", "position", "goals", "assists", "player_rating"]]
        .sort_values("goals", ascending=False)
    )
    st.dataframe(top_per_team, use_container_width=True, hide_index=True)


# ── Page: Position Analysis ────────────────────────────────────
def render_position_analysis(df: pd.DataFrame) -> None:
    st.markdown("## Position Analysis")

    if df.empty:
        st.warning("No data to display. Adjust the sidebar filters.")
        return

    # Ensure position order
    positions_present = [p for p in POSITION_ORDER if p in df["position"].values]

    col_left, col_right = st.columns(2)

    # ── Avg goals per position ────────────────────────────────
    with col_left:
        avg_goals = (
            df.groupby("position", as_index=False)["goals"]
            .mean()
            .round(2)
        )
        avg_goals["position"] = pd.Categorical(
            avg_goals["position"], categories=positions_present, ordered=True
        )
        avg_goals = avg_goals.sort_values("position")

        fig_ag = px.bar(
            avg_goals,
            x="position",
            y="goals",
            color="position",
            color_discrete_map=POSITION_COLORS,
            labels={"position": "Position", "goals": "Avg Goals per Player"},
            template=PLOTLY_TEMPLATE,
            category_orders={"position": positions_present},
        )
        _style_fig(fig_ag, "Average Goals by Position")
        st.plotly_chart(fig_ag, use_container_width=True)

    # ── Avg assists per position ──────────────────────────────
    with col_right:
        avg_ast = (
            df.groupby("position", as_index=False)["assists"]
            .mean()
            .round(2)
        )
        avg_ast["position"] = pd.Categorical(
            avg_ast["position"], categories=positions_present, ordered=True
        )
        avg_ast = avg_ast.sort_values("position")

        fig_aa = px.bar(
            avg_ast,
            x="position",
            y="assists",
            color="position",
            color_discrete_map=POSITION_COLORS,
            labels={"position": "Position", "assists": "Avg Assists per Player"},
            template=PLOTLY_TEMPLATE,
            category_orders={"position": positions_present},
        )
        _style_fig(fig_aa, "Average Assists by Position")
        st.plotly_chart(fig_aa, use_container_width=True)

    st.markdown("---")

    # ── Rating box plot ────────────────────────────────────────
    fig_box = px.box(
        df,
        x="position",
        y="player_rating",
        color="position",
        color_discrete_map=POSITION_COLORS,
        labels={"position": "Position", "player_rating": "Player Rating"},
        template=PLOTLY_TEMPLATE,
        category_orders={"position": positions_present},
        points="all",
    )
    _style_fig(fig_box, "Player Rating Distribution by Position")
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")

    # ── Avg key stats table per position ──────────────────────
    st.markdown("### Average Statistics by Position")
    pos_stats = (
        df.groupby("position")[
            ["goals", "assists", "shots", "pass_accuracy",
             "tackles", "minutes_played", "player_rating"]
        ]
        .mean()
        .round(2)
        .reindex(positions_present)
    )
    st.dataframe(pos_stats, use_container_width=True)


# ── Main router ────────────────────────────────────────────────
def main() -> None:
    inject_css()

    # Dashboard header
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {SURFACE_COLOR} 0%, #0a1f0b 100%);
            border: 1px solid #1e4023;
            border-radius: 10px;
            padding: 20px 28px;
            margin-bottom: 16px;
        ">
            <h1 style="color:{ACCENT_GREEN}; margin:0; font-size:2rem;">
                ⚽ Football Analytics Dashboard
            </h1>
            <p style="color:{MUTED_COLOR}; margin:4px 0 0 0; font-size:0.9rem;">
                Synthetic player performance data · 8 clubs · 4 positions · 2 seasons
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load data
    df = load_data()

    # Sidebar
    filtered_df, selected_players = render_sidebar(df)

    # Download button (top of main area)
    render_download_button(filtered_df)

    # Page navigation via tabs
    tabs = st.tabs(["Overview", "Player Analysis", "Team Analysis", "Position Analysis"])

    with tabs[0]:
        render_overview(filtered_df)

    with tabs[1]:
        render_player_analysis(filtered_df, selected_players)

    with tabs[2]:
        render_team_analysis(filtered_df)

    with tabs[3]:
        render_position_analysis(filtered_df)


if __name__ == "__main__":
    main()
