# ⚽ Football Player Performance Analytics Dashboard

> **Note — Synthetic Data:** All player statistics in this project are
> procedurally generated with `numpy.random.seed(42)`. They do not
> represent any real football player, club, or competition result.

An interactive, portfolio-quality football analytics dashboard built with
**Python**, **Streamlit**, **Pandas**, and **Plotly**. Explore synthetic
player performance data across 8 clubs, 4 positions, and 2 seasons through
a dark, pitch-inspired UI.

---

## Features

| Page | What you get |
|---|---|
| **Overview** | 5 KPI cards, top-10 scorers bar chart, rating histogram, goals-by-team bar |
| **Player Analysis** | Goals vs Assists scatter, Shots vs Goals with OLS trendline, multi-player comparison, searchable stats table |
| **Team Analysis** | Goals + Assists grouped bar, squad size, average rating, top scorer per team |
| **Position Analysis** | Avg goals & assists by position, rating box-plot, position stats table |

- Sidebar filters: Season · Team · Position · Compare Players  
- CSV download button (exports currently filtered data)  
- Dark green pitch theme throughout  
- Input validation and empty-state messages on every page  

---

## Project Structure

```
Football Analytics Dashboard/
├── app.py                  # Main Streamlit application
├── football_players.csv    # Synthetic dataset (320 rows, 18 columns)
├── generate_data.py        # Script that produces the CSV
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## Dataset Schema

| Column | Type | Description |
|---|---|---|
| player_id | int | Unique row identifier |
| player_name | str | Generated full name |
| team | str | One of 8 synthetic clubs |
| position | str | GK / DEF / MID / FWD |
| season | str | 2022-23 or 2023-24 |
| age | int | 18–36 |
| goals | int | Goals scored (≤ shots_on_target) |
| assists | int | Assists |
| shots | int | Total shots |
| shots_on_target | int | Shots on target (≤ shots) |
| minutes_played | int | Minutes played |
| pass_accuracy | float | Pass accuracy 0–100 % |
| dribbles_completed | int | Successful dribbles |
| tackles | int | Tackles |
| yellow_cards | int | Yellow cards |
| red_cards | int | Red cards |
| player_rating | float | Weighted composite rating 1.0–10.0 |
| nationality | str | Synthetic nationality |

`player_rating` is computed as a position-weighted composite of goals, assists,
pass accuracy, and tackles — not assigned randomly.

---

## Prerequisites

- Python **3.10+**
- pip

---

## Local Setup

```bash
# 1. Clone / download the repository
git clone https://github.com/your-username/football-analytics-dashboard.git
cd football-analytics-dashboard

# 2. (Recommended) Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate the dataset (already included — only needed to regenerate)
python generate_data.py

# 5. Run the dashboard
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**.

---

## Deploy to Streamlit Community Cloud

1. Push this repository to a public GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo → set **Main file path** to `app.py`.
4. Click **Deploy**. Streamlit Cloud installs `requirements.txt` automatically.

> `football_players.csv` must be committed to the repo. It is already included.

---

## KPI Calculations

All KPIs are computed at runtime from the **filtered** DataFrame:

| KPI | Calculation |
|---|---|
| Total Players | `len(filtered_df)` |
| Total Goals | `filtered_df["goals"].sum()` |
| Total Assists | `filtered_df["assists"].sum()` |
| Total Minutes | `filtered_df["minutes_played"].sum()` |
| Avg Rating | `filtered_df["player_rating"].mean()` |

---

## Regenerating the Dataset

```bash
python generate_data.py
```

Uses `numpy.random.seed(42)` — output is always identical.
Positional stat constraints are enforced:

| Position | Goals | Shots | Tackles |
|---|---|---|---|
| GK | 0–1 | 0–3 | 20–60 |
| DEF | 0–5 | 2–24 | 15–50 |
| MID | 2–12 | 10–54 | 5–34 |
| FWD | 5–30 | 20–80 | 2–19 |

---

## Dependencies

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.26.0
plotly>=5.20.0
statsmodels>=0.14.0
```

`statsmodels` is used exclusively for the OLS trendline in the
Shots vs Goals scatter chart.

---

## License

MIT — free to use, adapt, and share.
