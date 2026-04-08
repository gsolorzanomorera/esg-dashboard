"""
ESG Analytics Lab 3 — Module 3
Interactive Dashboard: NordPetro AS & VerdeMart Group plc
Run with: streamlit run esg_dashboard.py
"""

# ── Imports ────────────────────────────────────────────────────────────────────
## streamlit: the web-app framework that turns Python scripts into interactive dashboards
## pandas: used for reading, cleaning, and querying the Excel data tables
## plotly.graph_objects: low-level Plotly API for building charts trace-by-trace
## plotly.express: high-level Plotly shorthand (used sparingly here)
## make_subplots: lets a single chart have two y-axes (e.g., bars + a line overlay)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Page config (must be the very first Streamlit call) ───────────────────────
## Any st.* call before set_page_config() raises an error, so this always goes first.
st.set_page_config(
    page_title="ESG Dashboard — Lab 3",  ## text shown in the browser tab
    page_icon="🌿",                       ## favicon shown in the browser tab
    layout="wide",                        ## use the full browser width instead of a centred column
    initial_sidebar_state="expanded",     ## sidebar is open when the app first loads
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
## st.markdown with unsafe_allow_html=True injects raw HTML/CSS into the page.
## The <style> block below defines reusable CSS classes that are applied throughout
## the dashboard via class="..." attributes in later HTML strings.
##
## Key classes defined here:
##   .metric-card          — white card with a thin left-border colour stripe (red/amber/green/blue)
##   .metric-label         — tiny ALL-CAPS grey label sitting above a value
##   .metric-value         — large bold number (the headline KPI)
##   .metric-sub           — small grey sub-text below the value
##   .badge / .badge-*     — pill-shaped coloured tags used as inline data-quality flags
##   .section-header       — thin uppercase divider line separating dashboard rows
##   .flag-box             — red highlighted alert block
##   .warn-box             — amber highlighted warning block
##   div[data-testid="stMetric"] — overrides Streamlit's built-in metric component styling
st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
  .metric-card {
    background: #ffffff; border: 1px solid #e5e7eb;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 8px;
  }
  .metric-card.red   { border-left: 4px solid #E24B4A; }
  .metric-card.amber { border-left: 4px solid #EF9F27; }
  .metric-card.green { border-left: 4px solid #1D9E75; }
  .metric-card.blue  { border-left: 4px solid #185FA5; }
  .metric-label { font-size: 11px; font-weight: 600; color: #9ca3af;
                  text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
  .metric-value { font-size: 26px; font-weight: 700; color: #111; line-height: 1; }
  .metric-sub   { font-size: 11px; color: #6b7280; margin-top: 4px; }
  .badge {
    display: inline-block; font-size: 11px; padding: 3px 10px;
    border-radius: 20px; font-weight: 600; margin: 2px 2px 0 0;
  }
  .badge-red    { background: #FCEBEB; color: #791F1F; }
  .badge-amber  { background: #FAEEDA; color: #633806; }
  .badge-green  { background: #EAF3DE; color: #27500A; }
  .badge-blue   { background: #E6F1FB; color: #0C447C; }
  .section-header {
    font-size: 13px; font-weight: 700; color: #9ca3af;
    text-transform: uppercase; letter-spacing: .07em;
    border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin: 18px 0 10px;
  }
  .flag-box {
    background: #FCEBEB; border-left: 4px solid #E24B4A;
    border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 6px 0; font-size: 12px; color: #4b1515;
  }
  .warn-box {
    background: #FFF8EC; border-left: 4px solid #EF9F27;
    border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 6px 0; font-size: 12px; color: #4b3000;
  }
  div[data-testid="stMetric"] { background: #f9fafb; border-radius: 8px; padding: 10px 14px; }
  div[data-testid="stMetric"] label { font-size: 11px !important; }
</style>
""", unsafe_allow_html=True)

# ── Global constants ───────────────────────────────────────────────────────────
## YEARS: the four reporting periods available in the Excel dataset.
## Used as x-axis tick values for every chart and as column keys when pulling data.
YEARS = [2019, 2021, 2022, 2023]

## COLORS: a central palette so every chart uses the same hex values.
## Changing a colour here updates it everywhere in the dashboard automatically.
COLORS = {"blue": "#185FA5", "red": "#E24B4A", "amber": "#EF9F27",
          "green": "#1D9E75", "gray": "#9ca3af", "light": "#f3f4f6"}

# ── Data loader ───────────────────────────────────────────────────────────────
## @st.cache_data tells Streamlit to run this function only once per unique
## argument value and reuse the result on subsequent reruns. Without caching,
## the Excel file would be re-read from disk every time the user interacts with
## any widget, making the app feel slow.
@st.cache_data
def load_data(path: str):
    """
    Reads the Excel workbook and returns a dict with two cleaned DataFrames:
      {"nordpetro": <DataFrame>, "verdemart": <DataFrame>}

    The Excel layout has the real header row at row index 7 (row 8 in Excel),
    so we skip the first 7 rows and rename columns to a consistent set of names.
    """
    xl = pd.ExcelFile(path)

    def parse(sheet):
        ## Read the raw sheet with no automatic header detection
        raw = pd.read_excel(xl, sheet_name=sheet, header=None)

        ## Row index 7 contains the true column headers in this workbook
        raw.columns = raw.iloc[7]

        ## Drop all rows above the header (rows 0-7), then reset the index to 0, 1, 2, ...
        raw = raw.iloc[8:].reset_index(drop=True)

        ## Rename columns to predictable names regardless of what the Excel header says
        raw.columns = ["Metric", "2019", "2021", "2022", "2023", "Unit", "Notes"]

        ## Remove any rows where the Metric column is blank (spacer / section rows in Excel)
        raw = raw.dropna(subset=["Metric"])

        ## Ensure Metric is a clean string so keyword searches work reliably
        raw["Metric"] = raw["Metric"].astype(str).str.strip()
        return raw

    return {
        "nordpetro": parse(xl.sheet_names[0]),  ## first sheet = NordPetro data
        "verdemart":  parse(xl.sheet_names[1]),  ## second sheet = VerdeMart data
    }

# ── Row lookup helpers ─────────────────────────────────────────────────────────
def get_row(df, keyword):
    """
    Case-insensitive substring search across the Metric column.
    Returns the first matching row as a pandas Series, or None if not found.
    This lets us locate rows by a recognisable keyword instead of a fragile
    hard-coded row number.
    """
    mask = df["Metric"].str.contains(keyword, case=False, na=False)
    if mask.any():
        return df[mask].iloc[0]
    return None

def num(row, year):
    """
    Safely extracts a single numeric value from a data row for a given year.
    Returns a Python float, or None if the cell is empty or cannot be converted.
    The try/except handles unexpected data types (strings, '#N/A', etc.) gracefully.
    """
    try:
        val = row[str(year)]
        return float(val) if pd.notna(val) else None
    except Exception:
        return None

def series(row, years=None):
    """
    Builds a list of numeric values for all years in YEARS (or a custom list).
    This is the main way we turn a single data row into a plottable y-axis array.
    Example: series(r_s12) → [21.5, 19.3, 18.7, 18.0]
    """
    if years is None:
        years = YEARS
    return [num(row, y) for y in years]

# ── Chart helpers ─────────────────────────────────────────────────────────────
## PLOT_LAYOUT: a shared dict of Plotly layout settings applied to every chart.
## Keeping these in one place ensures visual consistency (transparent background,
## no horizontal gridlines, compact margins, same font).
## We unpack it with **PLOT_LAYOUT inside each figure's update_layout() call.
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",   ## transparent outer canvas (blends with page background)
    plot_bgcolor="rgba(0,0,0,0)",    ## transparent inner plot area
    font=dict(family="Arial", size=11, color="#4b5563"),
    margin=dict(l=10, r=10, t=30, b=10),  ## tight margins to maximise chart area
    xaxis=dict(showgrid=False, color="#9ca3af"),  ## no vertical gridlines; light axis text
    yaxis=dict(gridcolor="#f3f4f6", color="#9ca3af"),  ## very faint horizontal gridlines
    legend=dict(orientation="h", y=-0.2, x=0, font_size=11),  ## legend below the chart
    hoverlabel=dict(bgcolor="white", font_size=12),  ## clean white tooltip
)

def line_chart(traces, title="", height=260):
    """
    Creates a Plotly Figure with one or more pre-built traces (Scatter/Bar objects).
    Applies the shared PLOT_LAYOUT and sets the chart title and height.
    Callers build the traces themselves so they can customise colour, dash, markers, etc.
    """
    fig = go.Figure()
    for t in traces:
        fig.add_trace(t)
    fig.update_layout(**PLOT_LAYOUT, title=dict(text=title, font_size=12, x=0), height=height)
    return fig

def bar_chart(x, y, color, title="", height=220, text=None):
    """
    Creates a simple vertical bar chart.
    'text' is an optional list of labels displayed above/outside each bar
    (e.g. ["18.0 Mt", "19.3 Mt", ...]).
    """
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=color, text=text,
        textposition="outside", textfont_size=11,
    ))
    fig.update_layout(**PLOT_LAYOUT, title=dict(text=title, font_size=12, x=0), height=height)
    return fig

def progress_bar_html(pct, color, label_l, label_r):
    """
    Returns an HTML string that renders a custom progress bar.
    Streamlit doesn't have a built-in styled progress bar with two labels,
    so we build it directly in HTML/CSS.
    - pct: fill percentage (clamped to 100 so the bar never overflows)
    - color: hex fill colour for the filled portion
    - label_l / label_r: text displayed above the left and right ends of the bar
    """
    return f"""
    <div style='margin:8px 0;'>
      <div style='display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:3px;'>
        <span>{label_l}</span><span>{label_r}</span>
      </div>
      <div style='background:#f3f4f6;border-radius:6px;overflow:hidden;height:18px;'>
        <div style='width:{min(pct,100):.1f}%;background:{color};height:100%;
                    display:flex;align-items:center;padding-left:6px;'>
          <span style='font-size:10px;font-weight:700;color:#fff;'>{pct:.0f}%</span>
        </div>
      </div>
    </div>"""

def badge(text, kind="amber"):
    """
    Returns an HTML <span> styled as a coloured pill badge.
    'kind' maps to one of the CSS classes defined in the <style> block above:
      "red", "amber", "green", or "blue".
    These badges are used as inline data-quality flags below charts.
    """
    return f'<span class="badge badge-{kind}">{text}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
## Everything inside the `with st.sidebar:` block is rendered in the left panel.
## The sidebar contains:
##   1. A file uploader so students can swap in their own dataset
##   2. A radio button to switch between the two companies
##   3. The marking rubric for quick reference during critique sessions
with st.sidebar:
    st.markdown("## 🌿 ESG Lab 3 — Module 3")
    st.markdown("---")

    ## File uploader: if a file is uploaded it becomes the data source;
    ## otherwise the bundled default file path is used.
    uploaded = st.file_uploader("Upload your Excel dataset", type=["xlsx"],
                                 help="Upload a new version of the dataset to refresh all charts")
    if uploaded:
        data_path = uploaded  ## use the in-memory file object from the uploader widget
    else:
        data_path = "/mnt/user-data/uploads/Lab3_Minicases_data_exercise_canvas.xlsx"  ## default path

    ## Radio widget: the selected string is checked later to decide which company section to render
    company = st.radio("Select company", ["🛢 NordPetro AS", "🛒 VerdeMart Group plc"])
    st.markdown("---")

    ## Static rubric text — purely informational, no interactivity
    st.markdown("**Critique rubric**")
    st.markdown("""
- **Audience fit** — 25 pts
- **Metric relevance** — 25 pts
- **Visual clarity** — 25 pts
- **Data integrity** — 25 pts
    """)
    st.markdown("---")
    st.caption("Data: Lab3_Minicases_data_ecercise_canvas.xlsx")

# ── Load data ─────────────────────────────────────────────────────────────────
## Attempt to load the Excel file. If it fails (wrong path, corrupt file, missing
## sheet) we show a user-friendly error and stop execution so no further code runs.
try:
    data = load_data(data_path)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  NORDPETRO SECTION
#  Rendered when the user selects "🛢 NordPetro AS" in the sidebar radio button.
# ══════════════════════════════════════════════════════════════════════════════
if "NordPetro" in company:
    ## Select the NordPetro sheet from the loaded data dict
    df = data["nordpetro"]

    # ── Pull data rows from the DataFrame ─────────────────────────────────────
    ## Each variable holds one row of the cleaned DataFrame, identified by a
    ## keyword that appears in the Metric column. These are then passed to
    ## series() / num() to extract numeric values for charting.
    r_s12    = get_row(df, "Scope 1.2 combined")      ## combined Scope 1 + 2 emissions (Mt CO₂e)
    r_s1     = get_row(df, "Scope 1 emissions")       ## Scope 1 only (direct combustion + flaring)
    r_s2mkt  = get_row(df, "market-based")            ## Scope 2 market-based (reflects RECs/PPAs)
    r_s3c11  = get_row(df, "Cat.11")                  ## Scope 3 Cat.11: use of sold products (largest category)
    r_total  = get_row(df, "Total footprint")         ## sum of all scopes reported
    r_meth   = get_row(df, "Methane intensity")       ## methane leakage as % of gas produced
    r_meth_a = get_row(df, "Methane absolute")        ## methane leakage in absolute tonnes
    r_capex  = get_row(df, "Green capex .absolute.")  ## green/transition capex in USD millions
    r_capex_pct = get_row(df, "Green capex as %")     ## green capex as a % of total capex
    r_re     = get_row(df, "Renewable electricity")   ## renewable electricity share (0–1 or 0–100)
    r_flare  = get_row(df, "Flaring intensity")       ## flaring per unit of production
    r_water  = get_row(df, "Total water")             ## total water withdrawal (Mm³)
    r_spills = get_row(df, "Oil spills")              ## number of oil spills >1 barrel
    r_rnd    = get_row(df, "R.D spend")               ## R&D spend on low-carbon technology ($M)

    # ── Pre-compute headline KPIs used in multiple places ─────────────────────
    s12_vals  = series(r_s12)       ## Scope 1+2 as a list across YEARS
    s3c11_vals = series(r_s3c11)   ## Scope 3 Cat.11 as a list across YEARS
    s12_2023  = s12_vals[-1]       ## most recent (2023) Scope 1+2 value
    s3_2023   = s3c11_vals[-1]     ## most recent (2023) Scope 3 Cat.11 value
    total_2023 = (s12_2023 or 0) + (s3_2023 or 0)  ## total footprint; 'or 0' guards against None

    ## % of total footprint covered by the 2035 target (only Scope 1+2 is in scope)
    s12_pct   = round(s12_2023 / total_2023 * 100, 1) if total_2023 else 0
    s3_pct    = round(100 - s12_pct, 1)  ## % of footprint with NO published pathway

    target_35 = 10.75  ## NordPetro's 2035 Scope 1+2 target in Mt CO₂e (−50% vs 2019 base of 21.5)
    pct_change = round((s12_2023 - 21.5) / 21.5 * 100, 1)  ## actual % change vs 2019 base

    # ── Header banner ─────────────────────────────────────────────────────────
    ## Renders a company identity card at the top of the page with key context
    ## (sector, headcount, geography) and audience/question badges.
    st.markdown(f"""
    <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                padding:14px 18px;margin-bottom:16px;'>
      <div style='font-size:20px;font-weight:700;color:#111;'>
        🛢 NordPetro AS — ESG Transition Dashboard</div>
      <div style='font-size:12px;color:#6b7280;margin-top:4px;'>
        Norwegian integrated oil &amp; gas &nbsp;·&nbsp; 18,000 employees
        &nbsp;·&nbsp; 12 countries &nbsp;·&nbsp; Data: 2019–2023
      </div>
      <div style='margin-top:8px;'>
        {badge("Audience: ESG pension fund investor","blue")}
        {badge("Primary Q: Is the 2035 transition target on track?","blue")}
        {badge("⚠ 2023 data partially unassured","amber")}
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Row 1: Framing + Accountability ───────────────────────────────────────
    ## Two columns: left shows the footprint reality check (how much of total
    ## emissions the target actually covers); right shows the accountability
    ## structure (are there interim milestones?) and data assurance status.
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="section-header">FOOTPRINT REALITY CHECK</div>',
                    unsafe_allow_html=True)
        ## The key framing insight: the 50% reduction target covers only s12_pct% of
        ## the total footprint. Scope 3 Cat.11 (product combustion) has no pathway.
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

        ## Donut chart: visualises the Scope 1+2 vs Scope 3 split of total emissions.
        ## hole=0.55 creates the donut gap; the annotation in the centre shows the total.
        ## We exclude xaxis/yaxis from PLOT_LAYOUT because a Pie chart doesn't use them.
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
        ## Four milestone boxes: 2025, 2027, 2030 all show "none" (red),
        ## only 2035 has a target (blue). Highlights the 12-year accountability gap.
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
        ## Loop over each reporting year and render its assurance status as a badge.
        ## 2023 is only partially assured (amber), earlier years are fully assured (green).
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

    # ── Row 2: Emissions Trajectory & Capex ───────────────────────────────────
    ## Three equal columns: Scope 1+2 vs target line chart, methane intensity chart
    ## with OGMP level indicator, and a dual-axis green capex chart.
    st.markdown('<div class="section-header">EMISSIONS TRAJECTORY & TARGETS</div>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        ## Line chart: actual Scope 1+2 vs the linear required reduction path to target.
        ## The required path is manually defined as straight-line interpolation between
        ## the 2019 base (21.5 Mt) and the 2035 target (10.75 Mt).
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
        ## add_hline draws a horizontal dashed reference line at the target value
        fig.add_hline(y=target_35, line_dash="dot", line_color=COLORS["red"],
                      annotation_text=f"Target: {target_35} Mt", annotation_position="right")
        st.plotly_chart(fig, use_container_width=True)
        ## Inline badges summarise the key takeaway and flag the Scope 2 methodology issue
        st.markdown(
            f"{badge(f'Change vs 2019: {pct_change}%', 'green' if pct_change < 0 else 'red')}"
            f"{badge('⚠ Scope 2 mkt-based: 0.90 Mt lower than location-based','amber')}",
            unsafe_allow_html=True)

    with c2:
        ## Methane intensity chart: values stored as decimals (e.g. 0.08) are
        ## multiplied ×100 to display as percentages. The list comprehension
        ## checks whether each value is <1 to determine if scaling is needed.
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

        ## OGMP 2.0 level visualisation: five coloured/grey divs act as a
        ## segmented progress bar showing NordPetro is at Level 3 (stagnant).
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
        ## Dual-axis chart: green capex bars (left y-axis, USD M) overlaid with
        ## a line showing green capex as a % of total capex (right y-axis).
        ## make_subplots(specs=[[{"secondary_y": True}]]) creates a single subplot
        ## with two independent y-axes sharing the same x-axis.
        capex_vals = series(r_capex)
        capex_pct  = [v * 100 if v and v < 1 else v for v in series(r_capex_pct)]
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(
            go.Bar(x=YEARS, y=capex_vals, name="Green capex ($M)",
                   marker_color=[f"rgba(24,95,165,{a})" for a in [0.3,0.5,0.7,0.9]],  ## increasing opacity = growing investment
                   hovertemplate="%{x}: $%{y:,}M<extra></extra>"),
            secondary_y=False)  ## bind to left y-axis
        fig3.add_trace(
            go.Scatter(x=YEARS, y=capex_pct, name="% of total capex",
                       mode="lines+markers", line=dict(color=COLORS["amber"], width=2),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
            secondary_y=True)  ## bind to right y-axis
        ## Exclude xaxis/yaxis from PLOT_LAYOUT because make_subplots uses
        ## update_xaxes / update_yaxes instead
        fig3.update_layout(**{k: v for k, v in PLOT_LAYOUT.items()
                               if k not in ("xaxis","yaxis")},
                           height=260, title=dict(text="Green capex", font_size=12, x=0))
        fig3.update_yaxes(title_text="USD M", secondary_y=False, gridcolor="#f3f4f6")
        fig3.update_yaxes(title_text="% of total capex", secondary_y=True, showgrid=False)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown(badge("⚠ Internal taxonomy — not EU Taxonomy. Unverifiable.", "amber"),
                    unsafe_allow_html=True)

    # ── Row 3: Scope 3 + Integrity Scorecard ──────────────────────────────────
    ## Left column (wider): stacked bar chart showing the full footprint split.
    ## Right column: a scorecard of five governance/integrity flags.
    st.markdown('<div class="section-header">SCOPE 3 DISCLOSURE & DATA INTEGRITY</div>',
                unsafe_allow_html=True)
    c4, c5 = st.columns([3, 2])

    with c4:
        total_vals = series(r_total)
        ## Stacked bar: Scope 1+2 (blue) + Scope 3 Cat.11 (red) per year.
        ## barmode="stack" stacks traces vertically rather than placing them side by side.
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
        ## Scorecard: a list of tuples (label, value, sub-text, colour).
        ## Rendered as metric cards with a left-border colour indicating risk level.
        scorecard = [
            ("Target scope", f"{s12_pct}% of footprint", "Only Scope 1+2", "red"),
            ("Interim milestones", "None published", "End-target only: 2035", "red"),
            ("2023 assurance", "Partial (EY)", "2019–2022 fully assured", "amber"),
            ("Green capex taxonomy", "Internal only", "Not EU Taxonomy aligned", "amber"),
            ("OGMP level", "L3 / stagnant", "No upgrade timeline", "amber"),
        ]
        for label, val, sub, kind in scorecard:
            ## Ternary expression picks font colour based on risk level
            st.markdown(f"""
            <div class='metric-card {kind}' style='padding:10px 14px;margin-bottom:6px;'>
              <div class='metric-label'>{label}</div>
              <div style='font-size:16px;font-weight:700;color:#{"791F1F" if kind=="red" else "633806"};'>
                {val}</div>
              <div class='metric-sub'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    # ── Row 4: Secondary Metrics ───────────────────────────────────────────────
    ## Four equal columns for operational/contextual metrics:
    ## renewable electricity %, oil spill count, water withdrawal, and R&D spend.
    st.markdown('<div class="section-header">SECONDARY METRICS</div>',
                unsafe_allow_html=True)
    c6, c7, c8, c9 = st.columns(4)

    ## Convert any decimal fractions (e.g. 0.12) to percentages (12.0) before plotting.
    ## The condition `v < 1` assumes values stored as proportions rather than percentages.
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
#  VERDEMART SECTION
#  Rendered when the user selects "🛒 VerdeMart Group plc" in the sidebar.
# ══════════════════════════════════════════════════════════════════════════════
else:
    ## Select the VerdeMart sheet from the loaded data dict
    df = data["verdemart"]

    # ── Pull data rows ─────────────────────────────────────────────────────────
    r_s3tot  = get_row(df, "Total Scope 3")              ## total Scope 3 emissions (Mt CO₂e)
    r_s3c1   = get_row(df, "Cat.1 .purchased")           ## Scope 3 Cat.1: purchased goods & services
    r_s1     = get_row(df, "Scope 1 .refrigerants")      ## Scope 1 from refrigerant leakage (HFCs)
    r_s2mkt  = get_row(df, "Scope 2 . market")           ## Scope 2 market-based
    r_pricov = get_row(df, "Supplier coverage")          ## % of Cat.1 spend backed by primary supplier data
    r_sbti   = get_row(df, "SBTi")                       ## % of supplier spend with SBTi-validated targets
    r_enrol  = get_row(df, "enrolled")                   ## % of suppliers enrolled in engagement programme
    r_hfc_a  = get_row(df, "HFC refrigerant leakage .absolute")  ## HFC leakage in tonnes CO₂e
    r_hfc_r  = get_row(df, "HFC leakage rate")           ## HFC leakage as % of total refrigerant charge
    r_natref = get_row(df, "natural refrigerants")       ## % of stores using natural refrigerants
    r_plast  = get_row(df, "plastic packaging .absolute") ## own-brand plastic packaging (kt)
    r_recycle = get_row(df, "recyclable share")          ## % of own-brand plastic that is recyclable
    r_sku    = get_row(df, "Single-use plastic SKUs")    ## number of single-use plastic product lines
    r_foodw  = get_row(df, "Food waste intensity")       ## food waste kg per m² of selling space
    r_re     = get_row(df, "Renewable electricity")      ## renewable electricity share
    r_energy = get_row(df, "Total energy consumption")  ## total energy in PJ

    # ── Pre-compute KPIs ───────────────────────────────────────────────────────
    s3_vals   = series(r_s3tot)   ## Scope 3 total across YEARS
    s3c1_vals = series(r_s3c1)   ## Scope 3 Cat.1 across YEARS
    s3_target = 14.6             ## VerdeMart's 2035 Scope 3 target (Mt CO₂e, −50% vs 2019)
    s3_2019   = s3_vals[0]       ## 2019 baseline
    s3_2023   = s3_vals[-1]      ## most recent value

    ## Linear pace: average annual reduction from 2019 to 2023 over 4 years
    pace_actual = (s3_2019 - s3_2023) / 4

    ## Projected 2035 value if current pace continues (12 years from 2023)
    proj_2035   = round(s3_2023 - pace_actual * 12, 1)

    ## Gap: how far above target the current-pace projection lands (as a %)
    gap_pct     = round((proj_2035 - s3_target) / s3_target * 100, 1)

    ## Convert decimal fractions → percentages for all engagement/coverage metrics
    pricov_vals = [v * 100 if v and v < 1 else v for v in series(r_pricov)]
    sbti_vals   = [v * 100 if v and v < 1 else v for v in series(r_sbti)]
    enrol_vals  = [v * 100 if v and v < 1 else v for v in series(r_enrol)]
    hfc_vals    = [v * 100 if v and v < 1 else v for v in series(r_hfc_r)]
    plast_vals  = series(r_plast)
    foodw_vals  = series(r_foodw)
    re_vals     = [v * 100 if v and v < 1 else v for v in series(r_re)]

    ## Gap between enrolment (activity) and SBTi validation (outcome) in 2023
    sbti_gap    = enrol_vals[-1] - sbti_vals[-1]

    # ── Header banner ─────────────────────────────────────────────────────────
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

    # ── Row 1: Data validity + Commitment gap ─────────────────────────────────
    ## Two columns: left interrogates the reliability of the Scope 3 data;
    ## right shows the gap between supplier enrolment and verified SBTi targets.
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">DATA VALIDITY</div>',
                    unsafe_allow_html=True)
        pricov_now = pricov_vals[-1] if pricov_vals[-1] else 0

        ## Key integrity flag: most of Scope 3 Cat.1 (the biggest category) is still
        ## spend-based estimation, and the methodology has not been refreshed since 2020.
        ## This means reported reductions could be artefacts of the model, not real cuts.
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

        ## Bar chart showing how primary data coverage (supplier-provided activity data)
        ## has changed over time. Higher = more credible Scope 3 reporting.
        fig_cov = line_chart([
            go.Bar(x=YEARS, y=pricov_vals, name="Primary data coverage",
                   marker_color=COLORS["green"],
                   hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
        ], title="Scope 3 Cat.1 — primary data coverage (%)", height=220)
        st.plotly_chart(fig_cov, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">THE COMMERCIAL SIGNAL</div>',
                    unsafe_allow_html=True)
        ## Side-by-side comparison of enrolment (easy, low-bar activity) vs
        ## SBTi validation (hard, verified outcome). The gap (sbti_gap) is the key number
        ## because it shows how many suppliers have committed in name only.
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

        ## Dual-line chart: enrolled % (blue) vs SBTi validated % (green dashed).
        ## The widening gap between the two lines is the key visual story.
        fig_sup = line_chart([
            go.Scatter(x=YEARS, y=enrol_vals, name="Enrolled (%)", mode="lines+markers",
                       line=dict(color=COLORS["blue"], width=2),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
            go.Scatter(x=YEARS, y=sbti_vals, name="SBTi validated (%)", mode="lines+markers",
                       line=dict(color=COLORS["green"], width=2, dash="dot"),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
        ], title="Supplier engagement — enrolled vs SBTi validated (%)", height=220)
        st.plotly_chart(fig_sup, use_container_width=True)

    # ── Row 2: Scope 3 trajectory vs 2035 target ──────────────────────────────
    ## Wide left column: three-line chart (actual, required path, current pace projection).
    ## Narrow right column: four KPI cards summarising the trajectory numbers.
    st.markdown('<div class="section-header">SCOPE 3 TRAJECTORY VS 2035 TARGET</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])

    with c1:
        ## Build projected year arrays extending to 2035 for both the required path
        ## and the current-pace path. Years 2027, 2031, 2035 are projected, not observed.
        proj_years = [2019, 2021, 2022, 2023, 2027, 2031, 2035]

        ## Required path: linear interpolation from 2023 actual to 2035 target
        req_path   = [s3_2019, None, None, s3_2023,
                      round(s3_2023 - (s3_2023-s3_target)/12*4, 2),
                      round(s3_2023 - (s3_2023-s3_target)/12*8, 2),
                      s3_target]

        ## Current pace path: extrapolate the 2019→2023 average annual reduction forward
        pace_path  = [s3_2019, None, None, s3_2023,
                      round(s3_2023 - pace_actual*4, 2),
                      round(s3_2023 - pace_actual*8, 2),
                      proj_2035]

        ## Three traces: actual (solid green), required (red dashed), current pace (amber dotted)
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

        ## Horizontal reference line at the 2035 target for visual anchoring
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
        ## Four KPI cards: target, current progress, projected 2035 at current pace,
        ## and the acceleration factor needed to hit the target.
        kpis = [
            ("2035 Scope 3 target", f"{s3_target} Mt", f"−50% vs 2019 ({s3_2019} Mt)", "blue"),
            ("Progress to date (2023)", f"{s3_2023} Mt", "−12.8% achieved; need −50%", "amber"),
            ("At current pace (2035)", f"~{proj_2035} Mt", f"Miss by ~{gap_pct}%", "red"),
            ## Computes how many times faster than current pace is needed to hit target
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

    # ── Row 3: Secondary Metrics ───────────────────────────────────────────────
    ## Three columns covering HFC refrigerant leakage, own-brand plastic packaging,
    ## and food waste intensity — each with a chart and data-quality badges.
    st.markdown('<div class="section-header">SECONDARY METRICS</div>',
                unsafe_allow_html=True)
    c3, c4, c5 = st.columns(3)

    with c3:
        ## HFC leakage rate chart with an industry benchmark reference line at 15%.
        ## add_hline draws a dotted green horizontal line so viewers can judge performance.
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
        ## Plastic packaging bar chart — note the definition change in 2022 which
        ## makes pre-2022 data non-comparable. This is flagged with a red badge.
        fig_pl = bar_chart(YEARS, plast_vals, COLORS["blue"],
                           "Own-brand plastic packaging (kt)", height=230,
                           text=[f"{v:.0f} kt" for v in plast_vals])
        st.plotly_chart(fig_pl, use_container_width=True)
        st.markdown(
            badge("⚠ Definition changed 2022 — pre-2022 NOT comparable", "red"),
            unsafe_allow_html=True)

    with c5:
        ## Food waste intensity chart uses purple (#9333ea) to distinguish it
        ## visually from the other charts. The key limitation: this is intensity
        ## per m² (improves as stores expand), not absolute tonnage — so a falling
        ## line may mask rising total food waste if the estate is growing.
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

    # ── Row 4: Energy + Renewable electricity ─────────────────────────────────
    ## Two columns: total energy consumption (bar) and renewable electricity share (area line).
    c6, c7 = st.columns(2)
    with c6:
        energy_vals = series(r_energy)
        fig_en = bar_chart(YEARS, energy_vals, COLORS["gray"],
                           "Total energy consumption (PJ)", height=220,
                           text=[f"{v:.0f} PJ" for v in energy_vals])
        st.plotly_chart(fig_en, use_container_width=True)
    with c7:
        ## fill="tozeroy" shades the area between the line and the x-axis,
        ## making the growth in renewable share more visually impactful.
        ## fillcolor uses rgba() for a semi-transparent green fill.
        fig_re = line_chart([
            go.Scatter(x=YEARS, y=re_vals, name="Renewable electricity %",
                       mode="lines+markers", fill="tozeroy",
                       fillcolor="rgba(29,158,117,0.1)",
                       line=dict(color=COLORS["green"], width=3), marker=dict(size=8),
                       hovertemplate="%{x}: %{y:.0f}%<extra></extra>"),
        ], title="Renewable electricity share (%)", height=220)
        st.plotly_chart(fig_re, use_container_width=True)
        ## Additionality flag: RECs (Renewable Energy Certificates) allow companies
        ## to claim renewable electricity without necessarily procuring new generation.
        st.markdown(
            badge("⚠ 38% backed by RECs — additionality not verified", "amber"),
            unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
## A simple horizontal rule and caption at the very bottom of the page,
## visible regardless of which company is selected.
st.markdown("---")
st.caption("ESG Analytics Lab 3 — Module 3 · Data: Lab3_Minicases_data_exercise_canvas.xlsx · Built with Streamlit + Plotly")
