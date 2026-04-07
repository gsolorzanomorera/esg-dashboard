"""
ESG Analytics Lab 3 — Module 3
Interactive Dashboard: NordPetro AS & VerdeMart Group plc
Run with: streamlit run esg_dashboard.py
"""

import streamlit as st        ## lets you build the web app interface (buttons, text, layout, etc.)
import pandas as pd           ## used for loading and working with data tables (DataFrames)
import plotly.graph_objects as go   ## low‑level Plotly tools for fully customized charts
import plotly.express as px          ## high‑level Plotly tools for quick, easy charts
from plotly.subplots import make_subplots   ## allows you to place multiple charts in one figure

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ESG Dashboard — Lab 3",   ## sets the browser tab title shown at the top
    page_icon="🌿",                      ## sets the small icon (favicon) in the browser tab
    layout="wide",                       ## makes the app use the full width of the screen
    initial_sidebar_state="expanded",    ## makes the sidebar open by default when the app loads
)

# ── Custom CSS Cascading Style Sheets It is a language used to style web pages. If Streamlit components are the structure, CSS is the makeup, colors, layout, and design─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }  
  ## adjusts the top/bottom spacing of the main page container

  .metric-card {
    background: #ffffff; border: 1px solid #e5e7eb;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 8px;
  }  
  ## styles a custom “metric card” box (white background, border, rounded corners)

  .metric-card.red   { border-left: 4px solid #E24B4A; }  
  ## adds a red accent bar on the left side

  .metric-card.amber { border-left: 4px solid #EF9F27; }  
  ## adds an amber/orange accent bar

  .metric-card.green { border-left: 4px solid #1D9E75; }  
  ## adds a green accent bar

  .metric-card.blue  { border-left: 4px solid #185FA5; }  
  ## adds a blue accent bar

  .metric-label { 
    font-size: 11px; font-weight: 600; color: #9ca3af;
    text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px;
  }  
  ## styles the small label text inside metric cards

  .metric-value { 
    font-size: 26px; font-weight: 700; color: #111; line-height: 1;
  }  
  ## styles the main number/value in the metric card

  .metric-sub { 
    font-size: 11px; color: #6b7280; margin-top: 4px;
  }  
  ## styles the small subtext under the metric value

  .badge {
    display: inline-block; font-size: 11px; padding: 3px 10px;
    border-radius: 20px; font-weight: 600; margin: 2px 2px 0 0;
  }  
  ## base style for small rounded “badge” labels

  .badge-red    { background: #FCEBEB; color: #791F1F; }  
  ## red badge color scheme

  .badge-amber  { background: #FAEEDA; color: #633806; }  
  ## amber badge color scheme

  .badge-green  { background: #EAF3DE; color: #27500A; }  
  ## green badge color scheme

  .badge-blue   { background: #E6F1FB; color: #0C447C; }  
  ## blue badge color scheme

  .section-header {
    font-size: 13px; font-weight: 700; color: #9ca3af;
    text-transform: uppercase; letter-spacing: .07em;
    border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin: 18px 0 10px;
  }  
  ## styles section titles with a thin bottom border

  .flag-box {
    background: #FCEBEB; border-left: 4px solid #E24B4A;
    border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 6px 0;
    font-size: 12px; color: #4b1515;
  }  
  ## red warning box for alerts or issues

  .warn-box {
    background: #FFF8EC; border-left: 4px solid #EF9F27;
    border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 6px 0;
    font-size: 12px; color: #4b3000;
  }  
  ## amber warning box for softer alerts

  div[data-testid="stMetric"] { 
    background: #f9fafb; border-radius: 8px; padding: 10px 14px;
  }  
  ## custom styling for Streamlit’s built‑in st.metric widget

  div[data-testid="stMetric"] label { 
    font-size: 11px !important;
  }  
  ## makes the metric label text smaller
</style>
""", unsafe_allow_html=True)   ## tells Streamlit to allow raw HTML/CSS


## A list of years that will likely be used for analysis, filtering,
## reporting, or looping over specific time periods
YEARS = [2019, 2021, 2022, 2023]

## A dictionary that maps color names to their hexadecimal color codes
## These hex values are commonly used in web design and data visualization
COLORS = {
    "blue": "#185FA5",    ## Blue color in hex format
    "red": "#E24B4A",     ## Red color in hex format
    "amber": "#EF9F27",   ## Amber/orange color in hex format
    "green": "#1D9E75",   ## Green color in hex format
    "gray": "#9ca3af",    ## Gray color in hex format
    "light": "#f3f4f6"    ## Light gray (almost white) color in hex format
}

# ── Data loader ───────────────────────────────────────────────────────────────
## Cache the result of this function so the data is only loaded once
## This improves performance in Streamlit apps
@st.cache_data
def load_data(path: str):
    ## Open the Excel file located at the given path
    xl = pd.ExcelFile(path)

    ## Helper function to parse and clean each worksheet
    def parse(sheet):
        ## Read the sheet without headers so we can manually define them
        raw = pd.read_excel(xl, sheet_name=sheet, header=None)

        ## The actual header row is row 7 (0-based index),
        ## so we set the column names from that row
        raw.columns = raw.iloc[7]

        ## Remove all rows above the header and reset the index
        raw = raw.iloc[8:].reset_index(drop=True)

        ## Rename columns to standardized, meaningful names
        raw.columns = ["Metric", "2019", "2021", "2022", "2023", "Unit", "Notes"]

        ## Drop any rows where the Metric column is missing
        raw = raw.dropna(subset=["Metric"])

        ## Ensure Metric values are strings and remove extra whitespace
        raw["Metric"] = raw["Metric"].astype(str).str.strip()

        ## Return the cleaned DataFrame for this sheet
        return raw

    ## Parse the first two sheets and return them as a dictionary
    ## Keys represent dataset or company names
    return {
        "nordpetro": parse(xl.sheet_names[0]),
        "verdemart":  parse(xl.sheet_names[1]),
    }


## Retrieve the first row where the Metric column contains the given keyword
def get_row(df, keyword):
    ## Create a boolean mask for case-insensitive partial matching
    mask = df["Metric"].str.contains(keyword, case=False, na=False)

    ## If at least one match is found, return the first matching row
    if mask.any():
        return df[mask].iloc[0]

    ## Return None if no matching row exists
    return None


## Safely extract a numeric value for a given year from a row
def num(row, year):
    try:
        ## Access the value for the specified year
        val = row[str(year)]

        ## Convert to float if the value exists, otherwise return None
        return float(val) if pd.notna(val) else None
    except Exception:
        ## Return None if any error occurs (missing column, conversion error, etc.)
        return None


## Generate a list of numeric values across multiple years for a metric
def series(row, years=None):
    ## Default to the predefined YEARS list if none is provided
    if years is None:
        years = YEARS

    ## Return a list of numeric values for each year
    return [num(row, y) for y in years]
# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 ESG Lab 3 — Module 3")
    st.markdown("---")

    uploaded = st.file_uploader("Upload your Excel dataset", type=["xlsx"],
                                 help="Upload a new version of the dataset to refresh all charts")
    if uploaded:
        data_path = uploaded
    else:
        data_path = "Lab3_Minicases_data_ecercise_canvas.xlsx"

    company = st.radio("Select company", ["🛢 NordPetro AS", "🛒 VerdeMart Group plc"])
    st.markdown("---")
    st.markdown("**Critique rubric**")
    st.markdown("""
- **Audience fit** — 25 pts
- **Metric relevance** — 25 pts
- **Visual clarity** — 25 pts
- **Data integrity** — 25 pts
    """)
    st.markdown("---")
    st.caption("Data: Lab3_Minicases_data_ecercise_canvas.xlsx")

# ── Load ──────────────────────────────────────────────────────────────────────
try:
    ## Attempt to load and parse the data from the specified file path
    data = load_data(data_path)

except Exception as e:
    ## Display a user-friendly error message in the Streamlit app
    ## showing the exception that caused the failure
    st.error(f"Could not load data: {e}")

    ## Immediately stop execution of the Streamlit app
    ## to prevent further errors or invalid state
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  NORDPETRO
# ══════════════════════════════════════════════════════════════════════════════
## Check if the selected company corresponds to NordPetro
if "NordPetro" in company:
    ## Select the NordPetro dataset from the loaded data
    df = data["nordpetro"]

    ## Pull specific metric rows from the DataFrame using keyword matching
    r_s12       = get_row(df, "Scope 1.2 combined")
    r_s1        = get_row(df, "Scope 1 emissions")
    r_s2mkt     = get_row(df, "market-based")
    r_s3c11     = get_row(df, "Cat.11")
    r_total     = get_row(df, "Total footprint")
    r_meth      = get_row(df, "Methane intensity")
    r_meth_a    = get_row(df, "Methane absolute")
    r_capex     = get_row(df, "Green capex .absolute.")
    r_capex_pct = get_row(df, "Green capex as %")
    r_re        = get_row(df, "Renewable electricity")
    r_flare     = get_row(df, "Flaring intensity")
    r_water     = get_row(df, "Total water")
    r_spills    = get_row(df, "Oil spills")
    r_rnd       = get_row(df, "R.D spend")

    ## Convert selected rows into time series lists across predefined years
    s12_vals   = series(r_s12)
    s3c11_vals = series(r_s3c11)

    ## Extract the most recent (2023) values from each series
    s12_2023 = s12_vals[-1]
    s3_2023  = s3c11_vals[-1]

    ## Calculate total emissions for 2023, treating missing values as zero
    total_2023 = (s12_2023 or 0) + (s3_2023 or 0)

    ## Calculate percentage contribution of Scope 1+2 emissions
    ## Guard against division by zero
    s12_pct = round(s12_2023 / total_2023 * 100, 1) if total_2023 else 0

    ## Assign the remaining percentage to Scope 3
    s3_pct = round(100 - s12_pct, 1)

    ## Define a fixed benchmark or reduction target value
    target_35 = 10.75

    ## Calculate percent change from a baseline value (21.5) to 2023
    pct_change = round((s12_2023 - 21.5) / 21.5 * 100, 1)

    # ── Header ─────────────────────────────────────────────────────────────────
## Render a custom HTML block using Streamlit's markdown support
## unsafe_allow_html=True allows raw HTML and inline CSS to be rendered
st.markdown(f"""
    ## Outer container card with white background, light gray border,
    ## rounded corners, padding, and bottom margin
    <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                padding:14px 18px;margin-bottom:16px;'>

      ## Title section with larger, bold text and dark color
      <div style='font-size:20px;font-weight:700;color:#111;'>
        🛢 NordPetro AS — ESG Transition Dashboard
      </div>

      ## Subtitle / metadata row with smaller, muted text
      ## Provides company description, scale, geography, and data coverage
      <div style='font-size:12px;color:#6b7280;margin-top:4px;'>
        Norwegian integrated oil &amp; gas &nbsp;·&nbsp; 18,000 employees
        &nbsp;·&nbsp; 12 countries &nbsp;·&nbsp; Data: 2019–2023
      </div>

      ## Badge row highlighting audience, key question, and data caveat
      <div style='margin-top:8px;'>
        ## Target audience identification
        {badge("Audience: ESG pension fund investor","blue")}

        ## Primary analytical question the dashboard aims to answer
        {badge("Primary Q: Is the 2035 transition target on track?","blue")}

        ## Warning callout for partial assurance of the most recent data
        {badge("⚠ 2023 data partially unassured","amber")}
      </div>

    </div>
""", unsafe_allow_html=True)
``

    # ── Row 1: Framing + Milestones ────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="section-header">FOOTPRINT REALITY CHECK</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div class='metric-card red'>
          <div class='metric-label'>The framing problem</div>
          <div style='font-size:13px;color:#4b5563;margin-bottom:10px;'>
            The 50% reduction target covers only <strong>{s12_pct}%</strong> of NordPetro's
            total 2023 footprint. There is <strong>no published pathway</strong> for
            the remaining <strong>{s3_pct}%</strong>.
          </div>
          {progress_bar_html(s12_pct, "#185FA5", f"Scope 1+2 target boundary: {s12_2023} Mt", f"of {total_2023:.0f} Mt total")}
          <div style='background:#E24B4A;border-radius:0 6px 6px 0;padding:6px 12px;
                      font-size:11px;color:#fff;font-weight:600;margin-top:4px;'>
            Scope 3 Cat.11: {s3_2023} Mt — {s3_pct}% of footprint — NO target, NO pathway
          </div>
          {badge("Net-zero 2050 pledge — no Scope 3 pathway published as of 2023","red")}
        </div>""", unsafe_allow_html=True)

        # Footprint breakdown donut
        fig_foot = go.Figure(go.Pie(
            values=[s12_2023, s3_2023],
            labels=["Scope 1+2 (target)", "Scope 3 Cat.11 (no pathway)"],
            hole=0.55,
            marker_colors=[COLORS["blue"], COLORS["red"]],
            textinfo="percent+label",
            textfont_size=11,
            hovertemplate="%{label}: %{value} Mt (%{percent})<extra></extra>",
        ))
        fig_foot.update_layout(
            **{k: v for k, v in PLOT_LAYOUT.items() if k != "xaxis" and k != "yaxis"},
            height=220,
            showlegend=False,
            annotations=[dict(text=f"<b>{total_2023:.0f} Mt</b><br>total",
                              x=0.5, y=0.5, font_size=13, showarrow=False)]
        )
        st.plotly_chart(fig_foot, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">ACCOUNTABILITY STRUCTURE</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='metric-card red'>
          <div class='metric-label'>Interim milestones published?</div>
          <div style='display:flex;gap:6px;margin:10px 0;'>
            <div style='flex:1;text-align:center;padding:10px 4px;background:#FCEBEB;border-radius:8px;'>
              <div style='font-size:14px;font-weight:700;color:#791F1F;'>2025</div>
              <div style='font-size:11px;color:#A32D2D;'>✕ none</div>
            </div>
            <div style='flex:1;text-align:center;padding:10px 4px;background:#FCEBEB;border-radius:8px;'>
              <div style='font-size:14px;font-weight:700;color:#791F1F;'>2027</div>
              <div style='font-size:11px;color:#A32D2D;'>✕ none</div>
            </div>
            <div style='flex:1;text-align:center;padding:10px 4px;background:#FCEBEB;border-radius:8px;'>
              <div style='font-size:14px;font-weight:700;color:#791F1F;'>2030</div>
              <div style='font-size:11px;color:#A32D2D;'>✕ none</div>
            </div>
            <div style='flex:1;text-align:center;padding:10px 4px;background:#E6F1FB;border-radius:8px;'>
              <div style='font-size:14px;font-weight:700;color:#0C447C;'>2035</div>
              <div style='font-size:11px;color:#185FA5;'>−50%</div>
            </div>
          </div>
          <div style='font-size:11px;color:#6b7280;line-height:1.5;'>
            No checkpoint until 2035. Slippage structurally undetectable for 12 years.
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">DATA ASSURANCE</div>',
                    unsafe_allow_html=True)
        for yr, status, kind in [
            (2019, "EY assured ✓", "green"), (2021, "EY assured ✓", "green"),
            (2022, "EY assured ✓", "green"), (2023, "Partial only ⚠", "amber"),
        ]:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"padding:5px 0;border-bottom:0.5px solid #f3f4f6;'>"
                f"<span style='font-size:12px;color:#6b7280;'>{yr}</span>"
                f"{badge(status, kind)}</div>",
                unsafe_allow_html=True)

    # ── Row 2: Charts ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">EMISSIONS TRAJECTORY & TARGETS</div>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        fig = line_chart([
            go.Scatter(
                x=YEARS, y=s12_vals,
                name="Actual Scope 1+2", mode="lines+markers",
                line=dict(color=COLORS["blue"], width=3),
                marker=dict(size=7),
                hovertemplate="%{x}: %{y:.2f} Mt<extra></extra>",
            ),
            go.Scatter(
                x=[2019, 2023, 2027, 2031, 2035],
                y=[21.5, 18.0, 16.17, 14.33, target_35],
                name="Required path → 10.75 Mt",
                mode="lines", line=dict(color=COLORS["red"], dash="dash", width=2),
                hovertemplate="%{x}: %{y:.2f} Mt<extra></extra>",
            ),
        ], title="Scope 1+2 vs 2035 target")
        fig.add_hline(y=target_35, line_dash="dot", line_color=COLORS["red"],
                      annotation_text=f"Target: {target_35} Mt", annotation_position="right")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            f"{badge(f'Change vs 2019: {pct_change}%', 'green' if pct_change < 0 else 'red')}"
            f"{badge('⚠ Scope 2 mkt-based: 0.90 Mt lower than location-based','amber')}",
            unsafe_allow_html=True)

    with c2:
        meth_vals = [v * 100 if v and v < 1 else v for v in series(r_meth)]
        fig2 = line_chart([
            go.Scatter(
                x=YEARS, y=meth_vals,
                name="Methane intensity (% gas produced)",
                mode="lines+markers",
                line=dict(color=COLORS["amber"], width=3),
                marker=dict(size=7),
                hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
            ),
        ], title="Methane intensity (% of gas produced)")
        st.plotly_chart(fig2, use_container_width=True)
        # OGMP pips
        st.markdown("""
        <div style='font-size:11px;color:#6b7280;margin-bottom:4px;'>OGMP 2.0 level (stagnant since joining)</div>
        <div style='display:flex;gap:4px;'>
          <div style='flex:1;height:10px;border-radius:3px;background:#378ADD;'></div>
          <div style='flex:1;height:10px;border-radius:3px;background:#378ADD;'></div>
          <div style='flex:1;height:10px;border-radius:3px;background:#378ADD;'></div>
          <div style='flex:1;height:10px;border-radius:3px;background:#e5e7eb;border:1px solid #d1d5db;'></div>
          <div style='flex:1;height:10px;border-radius:3px;background:#e5e7eb;border:1px solid #d1d5db;'></div>
        </div>
        <div style='display:flex;justify-content:space-between;font-size:10px;color:#9ca3af;margin-top:3px;'>
          <span>L1</span><span>L2</span><span style='color:#185FA5;font-weight:700;'>L3 ▲ stagnant</span><span>L4</span><span>L5 gold</span>
        </div>""", unsafe_allow_html=True)
        st.markdown(badge("⚠ Engineering estimates — not direct measurement", "amber"),
                    unsafe_allow_html=True)

    with c3:
        capex_vals = series(r_capex)
        capex_pct  = [v * 100 if v and v < 1 else v for v in series(r_capex_pct)]
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(
            go.Bar(x=YEARS, y=capex_vals, name="Green capex ($M)",
                   marker_color=[f"rgba(24,95,165,{a})" for a in [0.3,0.5,0.7,0.9]],
                   hovertemplate="%{x}: $%{y:,}M<extra></extra>"),
            secondary_y=False)
        fig3.add_trace(
            go.Scatter(x=YEARS, y=capex_pct, name="% of total capex",
                       mode="lines+markers", line=dict(color=COLORS["amber"], width=2),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
            secondary_y=True)
        fig3.update_layout(**{k: v for k, v in PLOT_LAYOUT.items()
                               if k not in ("xaxis","yaxis")},
                           height=260, title=dict(text="Green capex", font_size=12, x=0))
        fig3.update_yaxes(title_text="USD M", secondary_y=False, gridcolor="#f3f4f6")
        fig3.update_yaxes(title_text="% of total capex", secondary_y=True, showgrid=False)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown(badge("⚠ Internal taxonomy — not EU Taxonomy. Unverifiable.", "amber"),
                    unsafe_allow_html=True)

    # ── Row 3: Scope 3 + Integrity ─────────────────────────────────────────────
    st.markdown('<div class="section-header">SCOPE 3 DISCLOSURE & DATA INTEGRITY</div>',
                unsafe_allow_html=True)
    c4, c5 = st.columns([3, 2])

    with c4:
        total_vals = series(r_total)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=YEARS, y=s12_vals, name="Scope 1+2",
            marker_color=COLORS["blue"],
            hovertemplate="%{x}: %{y:.2f} Mt S1+2<extra></extra>",
        ))
        fig4.add_trace(go.Bar(
            x=YEARS, y=s3c11_vals, name="Scope 3 Cat.11 (no pathway)",
            marker_color=COLORS["red"],
            hovertemplate="%{x}: %{y:.0f} Mt S3 (est.)<extra></extra>",
        ))
        fig4.update_layout(
            **{k: v for k, v in PLOT_LAYOUT.items()},
            barmode="stack", height=280,
            title=dict(text="Total footprint — Scope 1+2 + Scope 3 Cat.11 (stacked)", font_size=12, x=0),
        )
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown(
            badge("⚠ Scope 3 estimated via IEA factors — not measured", "amber") +
            badge("No Scope 3 net-zero pathway published", "red"),
            unsafe_allow_html=True)

    with c5:
        st.markdown('<div style="margin-top:10px;">', unsafe_allow_html=True)
        scorecard = [
            ("Target scope", f"{s12_pct}% of footprint", "Only Scope 1+2", "red"),
            ("Interim milestones", "None published", "End-target only: 2035", "red"),
            ("2023 assurance", "Partial (EY)", "2019–2022 fully assured", "amber"),
            ("Green capex taxonomy", "Internal only", "Not EU Taxonomy aligned", "amber"),
            ("OGMP level", "L3 / stagnant", "No upgrade timeline", "amber"),
        ]
        for label, val, sub, kind in scorecard:
            st.markdown(f"""
            <div class='metric-card {kind}' style='padding:10px 14px;margin-bottom:6px;'>
              <div class='metric-label'>{label}</div>
              <div style='font-size:16px;font-weight:700;color:#{"791F1F" if kind=="red" else "633806"};'>
                {val}</div>
              <div class='metric-sub'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    # ── Row 4: Secondary metrics ───────────────────────────────────────────────
    st.markdown('<div class="section-header">SECONDARY METRICS</div>',
                unsafe_allow_html=True)
    c6, c7, c8, c9 = st.columns(4)

    re_vals = [v * 100 if v and v < 1 else v for v in series(r_re)]
    spill_vals = series(r_spills)
    water_vals = series(r_water)
    rnd_vals   = series(r_rnd)

    with c6:
        fig = bar_chart(YEARS, re_vals, COLORS["green"],
                        "Renewable electricity %", height=200,
                        text=[f"{v:.0f}%" for v in re_vals])
        st.plotly_chart(fig, use_container_width=True)

    with c7:
        fig = bar_chart(YEARS, spill_vals, COLORS["amber"],
                        "Oil spills (>1 bbl)", height=200,
                        text=[str(int(v)) for v in spill_vals])
        st.plotly_chart(fig, use_container_width=True)

    with c8:
        fig = bar_chart(YEARS, water_vals, "#378ADD",
                        "Total water withdrawal (Mm³)", height=200,
                        text=[f"{v:.1f}" for v in water_vals])
        st.plotly_chart(fig, use_container_width=True)

    with c9:
        fig = bar_chart(YEARS, rnd_vals, COLORS["blue"],
                        "R&D: low-carbon tech ($M)", height=200,
                        text=[f"${v:.0f}M" for v in rnd_vals])
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  VERDEMART
# ══════════════════════════════════════════════════════════════════════════════
else:
    df = data["verdemart"]

    r_s3tot  = get_row(df, "Total Scope 3")
    r_s3c1   = get_row(df, "Cat.1 .purchased")
    r_s1     = get_row(df, "Scope 1 .refrigerants")
    r_s2mkt  = get_row(df, "Scope 2 . market")
    r_pricov = get_row(df, "Supplier coverage")
    r_sbti   = get_row(df, "SBTi")
    r_enrol  = get_row(df, "enrolled")
    r_hfc_a  = get_row(df, "HFC refrigerant leakage .absolute")
    r_hfc_r  = get_row(df, "HFC leakage rate")
    r_natref = get_row(df, "natural refrigerants")
    r_plast  = get_row(df, "plastic packaging .absolute")
    r_recycle = get_row(df, "recyclable share")
    r_sku    = get_row(df, "Single-use plastic SKUs")
    r_foodw  = get_row(df, "Food waste intensity")
    r_re     = get_row(df, "Renewable electricity")
    r_energy = get_row(df, "Total energy consumption")

    s3_vals   = series(r_s3tot)
    s3c1_vals = series(r_s3c1)
    s3_target = 14.6
    s3_2019   = s3_vals[0]
    s3_2023   = s3_vals[-1]

    pace_actual = (s3_2019 - s3_2023) / 4
    proj_2035   = round(s3_2023 - pace_actual * 12, 1)
    gap_pct     = round((proj_2035 - s3_target) / s3_target * 100, 1)

    pricov_vals = [v * 100 if v and v < 1 else v for v in series(r_pricov)]
    sbti_vals   = [v * 100 if v and v < 1 else v for v in series(r_sbti)]
    enrol_vals  = [v * 100 if v and v < 1 else v for v in series(r_enrol)]
    hfc_vals    = [v * 100 if v and v < 1 else v for v in series(r_hfc_r)]
    plast_vals  = series(r_plast)
    foodw_vals  = series(r_foodw)
    re_vals     = [v * 100 if v and v < 1 else v for v in series(r_re)]
    sbti_gap    = enrol_vals[-1] - sbti_vals[-1]

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                padding:14px 18px;margin-bottom:16px;'>
      <div style='font-size:20px;font-weight:700;color:#111;'>
        🛒 VerdeMart Group plc — ESG Supply Chain Dashboard</div>
      <div style='font-size:12px;color:#6b7280;margin-top:4px;'>
        UK grocery retailer &nbsp;·&nbsp; 2,400 stores &nbsp;·&nbsp;
        18 markets &nbsp;·&nbsp; 310,000 employees &nbsp;·&nbsp; Data: 2019–2023
      </div>
      <div style='margin-top:8px;'>
        {badge("Audience: Head of Sustainability, FMCG Supplier","green")}
        {badge("Primary Q: What Scope 3 reduction will VerdeMart demand by 2027?","green")}
        {badge("⚠ Cat.1 methodology frozen since 2020","amber")}
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Row 1: Data validity + commitment gap ──────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">DATA VALIDITY</div>',
                    unsafe_allow_html=True)
        pricov_now = pricov_vals[-1] if pricov_vals[-1] else 0
        st.markdown(f"""
        <div class='metric-card red'>
          <div class='metric-label'>Can we trust the Scope 3 numbers?</div>
          <div style='font-size:13px;color:#4b5563;margin-bottom:8px;'>
            <strong>{100-pricov_now:.0f}%</strong> of Scope 3 Cat.1 (71% of total S3)
            is still spend-based estimation. Methodology frozen since <strong>2020</strong>.
          </div>
          {progress_bar_html(pricov_now, "#1D9E75", f"Primary data: {pricov_now:.0f}%",
                             f"Estimated: {100-pricov_now:.0f}%")}
          {badge("Reported Scope 3 reductions may be a modelling artefact, not real decarbonisation","red")}
        </div>""", unsafe_allow_html=True)

        # Primary data coverage trend
        fig_cov = line_chart([
            go.Bar(x=YEARS, y=pricov_vals, name="Primary data coverage",
                   marker_color=COLORS["green"],
                   hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
        ], title="Scope 3 Cat.1 — primary data coverage (%)", height=220)
        st.plotly_chart(fig_cov, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">THE COMMERCIAL SIGNAL</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div class='metric-card red'>
          <div class='metric-label'>What VerdeMart will demand from suppliers</div>
          <div style='display:flex;gap:10px;margin:10px 0;align-items:stretch;'>
            <div style='flex:1;text-align:center;padding:14px 8px;background:#E6F1FB;border-radius:8px;'>
              <div style='font-size:30px;font-weight:700;color:#0C447C;'>{enrol_vals[-1]:.0f}%</div>
              <div style='font-size:11px;color:#185FA5;margin-top:4px;'>Enrolled in programme</div>
            </div>
            <div style='display:flex;align-items:center;flex-direction:column;
                        justify-content:center;padding:0 6px;'>
              <span style='font-size:20px;color:#9ca3af;'>→</span>
              <span style='font-size:10px;color:#A32D2D;font-weight:700;
                           margin-top:2px;text-align:center;'>
                {sbti_gap:.0f}pp gap<br>widening</span>
            </div>
            <div style='flex:1;text-align:center;padding:14px 8px;background:#FCEBEB;border-radius:8px;'>
              <div style='font-size:30px;font-weight:700;color:#791F1F;'>{sbti_vals[-1]:.0f}%</div>
              <div style='font-size:11px;color:#A32D2D;margin-top:4px;'>SBTi validated targets</div>
            </div>
          </div>
          <div style='font-size:11px;color:#6b7280;line-height:1.5;'>
            {100-sbti_vals[-1]:.0f}% of supplier spend has made zero verified commitment.
            Formal SBTi supply conditions expected by 2025–2027.
          </div>
          {badge("Enrolment is activity. SBTi is the only outcome that matters.","red")}
        </div>""", unsafe_allow_html=True)

        # Enrolment vs SBTi trend
        fig_sup = line_chart([
            go.Scatter(x=YEARS, y=enrol_vals, name="Enrolled (%)", mode="lines+markers",
                       line=dict(color=COLORS["blue"], width=2),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
            go.Scatter(x=YEARS, y=sbti_vals, name="SBTi validated (%)", mode="lines+markers",
                       line=dict(color=COLORS["green"], width=2, dash="dot"),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
        ], title="Supplier engagement — enrolled vs SBTi validated (%)", height=220)
        st.plotly_chart(fig_sup, use_container_width=True)

    # ── Row 2: Scope 3 chart ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">SCOPE 3 TRAJECTORY VS 2035 TARGET</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])

    with c1:
        proj_years = [2019, 2021, 2022, 2023, 2027, 2031, 2035]
        req_path   = [s3_2019, None, None, s3_2023,
                      round(s3_2023 - (s3_2023-s3_target)/12*4, 2),
                      round(s3_2023 - (s3_2023-s3_target)/12*8, 2),
                      s3_target]
        pace_path  = [s3_2019, None, None, s3_2023,
                      round(s3_2023 - pace_actual*4, 2),
                      round(s3_2023 - pace_actual*8, 2),
                      proj_2035]

        fig_s3 = line_chart([
            go.Scatter(x=YEARS, y=s3_vals, name="Actual Scope 3", mode="lines+markers",
                       line=dict(color=COLORS["green"], width=3), marker=dict(size=8),
                       hovertemplate="%{x}: %{y:.2f} Mt<extra></extra>"),
            go.Scatter(x=proj_years, y=req_path, name=f"Required path → {s3_target} Mt",
                       mode="lines", line=dict(color=COLORS["red"], dash="dash", width=2),
                       hovertemplate="%{x}: %{y:.2f} Mt<extra></extra>"),
            go.Scatter(x=proj_years, y=pace_path,
                       name=f"Current pace → {proj_2035} Mt",
                       mode="lines", line=dict(color=COLORS["amber"], dash="dot", width=2),
                       hovertemplate="%{x}: %{y:.2f} Mt<extra></extra>"),
        ], title="Total Scope 3 (Mt CO₂e) — actual vs required path vs current pace", height=300)
        fig_s3.add_hline(y=s3_target, line_dash="dot", line_color=COLORS["red"],
                         annotation_text=f"2035 target: {s3_target} Mt",
                         annotation_position="right")
        st.plotly_chart(fig_s3, use_container_width=True)
        st.markdown(
            badge(f"⚠ At current pace: ~{proj_2035} Mt by 2035 — missing target by ~{gap_pct}%", "amber") +
            badge("Cat.1 methodology not refreshed since 2020 — progress may not be real", "red"),
            unsafe_allow_html=True)

    with c2:
        st.markdown('<div style="margin-top:10px;">', unsafe_allow_html=True)
        kpis = [
            ("2035 Scope 3 target", f"{s3_target} Mt", f"−50% vs 2019 ({s3_2019} Mt)", "blue"),
            ("Progress to date (2023)", f"{s3_2023} Mt", "−12.8% achieved; need −50%", "amber"),
            ("At current pace (2035)", f"~{proj_2035} Mt", f"Miss by ~{gap_pct}%", "red"),
            ("Pace needed vs achieved", f"+{round((((s3_2023-s3_target)/12)/pace_actual-1)*100)}% faster", "Acceleration needed", "red"),
        ]
        for label, val, sub, kind in kpis:
            st.markdown(f"""
            <div class='metric-card {kind}' style='padding:10px 14px;margin-bottom:6px;'>
              <div class='metric-label'>{label}</div>
              <div style='font-size:18px;font-weight:700;
                color:#{"791F1F" if kind=="red" else "633806" if kind=="amber" else "0C447C"};'>
                {val}</div>
              <div class='metric-sub'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    # ── Row 3: HFC + Packaging + Food ─────────────────────────────────────────
    st.markdown('<div class="section-header">SECONDARY METRICS</div>',
                unsafe_allow_html=True)
    c3, c4, c5 = st.columns(3)

    with c3:
        fig_hfc = line_chart([
            go.Scatter(x=YEARS, y=hfc_vals, name="HFC leakage rate (%)",
                       mode="lines+markers",
                       line=dict(color=COLORS["amber"], width=3), marker=dict(size=8),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
        ], title="HFC refrigerant leakage rate (%)", height=230)
        fig_hfc.add_hline(y=15, line_dash="dot", line_color=COLORS["green"],
                          annotation_text="Industry benchmark 15%",
                          annotation_position="right")
        st.plotly_chart(fig_hfc, use_container_width=True)
        st.markdown(
            badge("Now at industry benchmark (~15%) ✓", "green") +
            badge("⚠ Franchise stores (18%) excluded", "amber"),
            unsafe_allow_html=True)

    with c4:
        fig_pl = bar_chart(YEARS, plast_vals, COLORS["blue"],
                           "Own-brand plastic packaging (kt)", height=230,
                           text=[f"{v:.0f} kt" for v in plast_vals])
        st.plotly_chart(fig_pl, use_container_width=True)
        st.markdown(
            badge("⚠ Definition changed 2022 — pre-2022 NOT comparable", "red"),
            unsafe_allow_html=True)

    with c5:
        fig_fw = line_chart([
            go.Scatter(x=YEARS, y=foodw_vals,
                       name="Food waste intensity (kg/m²)",
                       mode="lines+markers",
                       line=dict(color="#9333ea", width=3), marker=dict(size=8),
                       hovertemplate="%{x}: %{y:.2f} kg/m²<extra></extra>"),
        ], title="Food waste intensity (kg/m² selling space)", height=230)
        st.plotly_chart(fig_fw, use_container_width=True)
        st.markdown(
            badge("⚠ Absolute tonnage undisclosed — estate expanding", "amber") +
            badge("⚠ Intensity ≠ absolute", "amber"),
            unsafe_allow_html=True)

    # ── Row 4: Energy + RE ────────────────────────────────────────────────────
    c6, c7 = st.columns(2)
    with c6:
        energy_vals = series(r_energy)
        fig_en = bar_chart(YEARS, energy_vals, COLORS["gray"],
                           "Total energy consumption (PJ)", height=220,
                           text=[f"{v:.0f} PJ" for v in energy_vals])
        st.plotly_chart(fig_en, use_container_width=True)
    with c7:
        fig_re = line_chart([
            go.Scatter(x=YEARS, y=re_vals, name="Renewable electricity %",
                       mode="lines+markers", fill="tozeroy",
                       fillcolor="rgba(29,158,117,0.1)",
                       line=dict(color=COLORS["green"], width=3), marker=dict(size=8),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
        ], title="Renewable electricity share (%)", height=220)
        st.plotly_chart(fig_re, use_container_width=True)
        st.markdown(
            badge("⚠ 38% backed by RECs — additionality not verified", "amber"),
            unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("ESG Analytics Lab 3 — Module 3 · Data: Lab3_Minicases_data_ecercise_canvas.xlsx · "
           "Built with Streamlit + Plotly")
