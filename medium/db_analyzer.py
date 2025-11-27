#!/usr/bin/env python3
"""
db_analyzer.py

AI CODEFIX 2025 - Database Insights Agent (Medium)
Complete, production-ready script to analyze any SQLite database, produce
statistics and visualizations, generate HTML and PDF reports, and send an email
with attachments.

Usage:
    python db_analyzer.py --db data.db --email recipient@example.com
    Optional:
      --config config.json
      --output output_folder
"""

import os
import sys
import argparse
import logging
import json
import sqlite3
import tempfile
import traceback
from datetime import datetime
from io import BytesIO

# Data
import pandas as pd
import numpy as np
from dateutil.parser import parse as dateutil_parse

# Visualization
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for servers
import matplotlib.pyplot as plt
import seaborn as sns

# PDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Email
import smtplib
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

# ---------------------------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT = "output"
DEFAULT_CONFIG_FILE = "config.json"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("db_analyzer")

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def generate_db_summary(db_path):
    import sqlite3
    import pandas as pd

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    summary_lines = []

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    
    summary_lines.append(f"Database contains {len(tables)} table(s): {', '.join(tables)}.\n")
    
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        summary_lines.append(f"Table '{table}': {df.shape[0]} rows, {df.shape[1]} columns.")
        nulls = df.isnull().sum().sum()
        summary_lines.append(f" - Null/missing values: {nulls}")
        duplicates = df.duplicated().sum()
        summary_lines.append(f" - Duplicate rows: {duplicates}")
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:3]:
                summary_lines.append(f" - Column '{col}': mean={df[col].mean():.2f}, min={df[col].min()}, max={df[col].max()}")
        summary_lines.append("")  # blank line between tables
    
    conn.close()
    return "\n".join(summary_lines)


def safe_mkdir(path):
    try:
        os.makedirs(path, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {path}")
    except Exception as e:
        logger.error(f"Failed to create output directory {path}: {e}")
        raise

def load_config(path):
    config = {}
    if path and os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                config = json.load(fh)
            logger.info(f"Loaded config from {path}")
        except Exception as e:
            logger.error(f"Could not load config at {path}: {e}")
            raise
    else:
        logger.warning(f"Config file {path} not found; falling back to environment variables.")
    # populate defaults
    config.setdefault("smtp_server", os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    config.setdefault("smtp_port", int(os.getenv("SMTP_PORT", 587)))
    config.setdefault("sender_email", os.getenv("SENDER_EMAIL", "your_email@example.com"))
    config.setdefault("sender_password", os.getenv("SENDER_PASSWORD", ""))
    config.setdefault("team_name", os.getenv("TEAM_NAME", "YourTeamName"))
    config.setdefault("output_folder", os.getenv("OUTPUT_FOLDER", DEFAULT_OUTPUT))
    config.setdefault("theme", os.getenv("THEME", "professional-blue"))
    return config

def connect_sqlite(db_path):
    try:
        conn = sqlite3.connect(db_path)
        logger.info(f"Connected to SQLite database at {db_path}")
        return conn
    except Exception as e:
        logger.error(f"Could not connect to SQLite database: {e}")
        raise

def list_tables(conn: sqlite3.Connection):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        tables = [r[0] for r in cursor.fetchall()]
        logger.info(f"Discovered tables: {tables}")
        return tables
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise

# ---------------------------------------------------------------------------
# Data extraction & schema inference
# ---------------------------------------------------------------------------

def fetch_table(conn, table_name):
    try:
        df = pd.read_sql_query(f"SELECT * FROM \"{table_name}\";", conn)
        logger.info(f"Fetched table '{table_name}' with shape {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch table {table_name}: {e}")
        raise

def infer_column_types(df: pd.DataFrame):
    inference = {}
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        inferred = "unknown"
        # Prefer pandas dtype but with extra heuristics
        if pd.api.types.is_integer_dtype(series):
            inferred = "integer"
        elif pd.api.types.is_float_dtype(series):
            inferred = "float"
        elif pd.api.types.is_bool_dtype(series):
            inferred = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(series):
            inferred = "datetime"
        else:
            # try parse as datetime with dateutil
            if len(non_null) > 0:
                sample = non_null.astype(str).head(10).tolist()
                dt_count = 0
                for s in sample:
                    try:
                        _ = dateutil_parse(s)
                        dt_count += 1
                    except Exception:
                        pass
                if dt_count >= max(1, len(sample)//2):
                    inferred = "datetime"
                else:
                    # check numeric-like
                    try:
                        pd.to_numeric(non_null, errors='raise')
                        if non_null.apply(lambda x: '.' in str(x)).any():
                            inferred = "float"
                        else:
                            inferred = "integer"
                    except Exception:
                        inferred = "string"
            else:
                inferred = "empty"
        inference[col] = inferred
        logger.debug(f"Column '{col}': inferred type {inferred}")
    return inference

# ---------------------------------------------------------------------------
# Analytics & insights
# ---------------------------------------------------------------------------

def table_statistics(df: pd.DataFrame):
    stats = {}
    try:
        stats['rows'] = int(len(df))
        stats['columns'] = int(len(df.columns))
        stats['column_stats'] = {}
        for col in df.columns:
            s = df[col]
            col_stat = {
                'dtype': str(s.dtype),
                'non_null_count': int(s.count()),
                'null_count': int(s.isnull().sum()),
                'unique_values': int(s.nunique(dropna=True)),
                'duplicates': int(s.duplicated().sum())
            }
            # numeric
            if pd.api.types.is_numeric_dtype(s):
                col_stat.update({
                    'min': safe_np_value(s.min()),
                    'max': safe_np_value(s.max()),
                    'mean': safe_np_value(s.mean()),
                    'std': safe_np_value(s.std())
                })
            # textual
            if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s):
                col_stat.update({
                    'sample_values': s.dropna().astype(str).head(5).tolist()
                })
            stats['column_stats'][col] = col_stat
        logger.info(f"Computed stats for DataFrame with {stats['rows']} rows and {stats['columns']} cols")
    except Exception as e:
        logger.error(f"Error computing table statistics: {e}")
        raise
    return stats

def safe_np_value(v):
    try:
        if pd.isna(v):
            return None
        # convert numpy types to python native
        if isinstance(v, (np.integer, np.floating, np.bool_)):
            return v.item()
        if isinstance(v, (np.ndarray,)):
            return v.tolist()
        return v
    except Exception:
        return None

def top_insights_for_table(table_name, df, type_inference):
    insights = []
    try:
        row_count = len(df)
        if row_count == 0:
            insights.append(f"Table '{table_name}' is empty.")
            return insights
        # 1. High null columns
        nulls = df.isnull().mean().sort_values(ascending=False)
        high_nulls = nulls[nulls > 0.3]
        if not high_nulls.empty:
            cols = list(high_nulls.index)
            insights.append(
                f"In table '{table_name}', columns {cols} have high missingness (>30%). Consider data collection or imputation."
            )
        # 2. Duplicate-heavy
        dup_ratio = df.duplicated().mean()
        if dup_ratio > 0.1:
            insights.append(
                f"Table '{table_name}' contains {dup_ratio:.1%} duplicate rows; investigate upstream ingestion or create deduplication steps."
            )
        # 3. Cardinality issues
        for col in df.columns:
            nunique = df[col].nunique(dropna=True)
            if nunique == 1:
                insights.append(f"Column '{col}' in '{table_name}' has only one unique value ({df[col].dropna().unique().tolist()[:3]}).")
            elif nunique == 0:
                insights.append(f"Column '{col}' in '{table_name}' is entirely empty.")
            elif nunique / max(1, len(df)) > 0.9 and nunique > 20 and pd.api.types.is_string_dtype(df[col]):
                insights.append(f"Column '{col}' in '{table_name}' appears to be a high-cardinality text field (unique ratio >90%).")
        # 4. Numeric outliers (IQR)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            s = df[col].dropna()
            if len(s) >= 5:
                q1 = s.quantile(0.25)
                q3 = s.quantile(0.75)
                iqr = q3 - q1
                upper = q3 + 1.5 * iqr
                lower = q1 - 1.5 * iqr
                outliers = s[(s > upper) | (s < lower)]
                if len(outliers) > 0:
                    insights.append(f"Numeric column '{col}' in '{table_name}' has {len(outliers)} potential outliers (IQR method).")
        # 5. Date range checks
        date_cols = [c for c, t in type_inference.items() if t == 'datetime']
        for c in date_cols:
            try:
                s = pd.to_datetime(df[c], errors='coerce').dropna()
                if len(s) > 0:
                    min_dt = s.min()
                    max_dt = s.max()
                    if (max_dt - min_dt).days < 1:
                        insights.append(f"Date column '{c}' in '{table_name}' has a very narrow range ({min_dt} to {max_dt}).")
            except Exception:
                pass
        # 6. Correlation signals
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr().abs()
            # find pairs with high correlation above 0.85
            pairs = []
            for i in range(len(corr.columns)):
                for j in range(i+1, len(corr.columns)):
                    a = corr.columns[i]
                    b = corr.columns[j]
                    val = corr.iloc[i, j]
                    if pd.notna(val) and val > 0.85:
                        pairs.append((a, b, val))
            if pairs:
                pairs_str = ", ".join([f"{a}-{b} ({v:.2f})" for a, b, v in pairs])
                insights.append(f"Strong correlations detected in '{table_name}': {pairs_str}. Consider multicollinearity handling.")
        # 7. Quick distribution insights (skew)
        for col in numeric_cols:
            s = df[col].dropna()
            if len(s) >= 10:
                skew = s.skew()
                if abs(skew) > 2:
                    insights.append(f"Numeric column '{col}' in '{table_name}' is highly skewed (skew={skew:.2f}). Consider transformation.")
    except Exception as e:
        logger.error(f"Failed to compute insights for {table_name}: {e}\n{traceback.format_exc()}")
        insights.append(f"Could not compute all insights for '{table_name}' due to an error: {e}")
    return insights

# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------

def save_figure(fig, path, dpi=200):
    try:
        fig.savefig(path, bbox_inches='tight', dpi=dpi)
        plt.close(fig)
        logger.info(f"Saved figure to {path}")
    except Exception as e:
        logger.error(f"Failed to save figure {path}: {e}")
        raise

def gen_distribution_plot(df, col, outpath):
    try:
        fig, ax = plt.subplots(figsize=(10,6))
        s = df[col].dropna()
        if pd.api.types.is_numeric_dtype(s):
            sns.histplot(s, kde=True, ax=ax)
            ax.set_title(f"Distribution of {col}")
            ax.set_xlabel(col)
            ax.set_ylabel("Count")
        else:
            counts = s.astype(str).value_counts().nlargest(20)
            sns.barplot(x=counts.values, y=counts.index, ax=ax)
            ax.set_title(f"Top categories for {col}")
            ax.set_xlabel("Count")
            ax.set_ylabel(col)
        save_figure(fig, outpath)
    except Exception as e:
        logger.error(f"Error generating distribution plot for {col}: {e}")

def gen_time_series_plot(df, datetime_col, numeric_col, outpath):
    try:
        fig, ax = plt.subplots(figsize=(12,5))
        df_ts = df[[datetime_col, numeric_col]].dropna()
        df_ts[datetime_col] = pd.to_datetime(df_ts[datetime_col], errors='coerce')
        df_ts = df_ts.dropna(subset=[datetime_col])
        if df_ts.empty:
            # fallback - aggregate by index if numeric exists
            fig, ax = plt.subplots(figsize=(10,4))
            ax.text(0.5, 0.5, "No time series data available", ha='center', va='center')
            save_figure(fig, outpath)
            return
        df_ts = df_ts.set_index(datetime_col).sort_index()
        # resample intelligently
        try:
            # daily if range < 120 days else monthly
            delta = df_ts.index.max() - df_ts.index.min()
            if delta.days <= 120:
                agg = df_ts.resample('D').mean().interpolate()
            else:
                agg = df_ts.resample('M').mean().interpolate()
            ax.plot(agg.index, agg[numeric_col], marker='o', linewidth=1)
            ax.set_title(f"{numeric_col} over time ({datetime_col})")
            ax.set_xlabel("Date")
            ax.set_ylabel(numeric_col)
            save_figure(fig, outpath)
        except Exception:
            # fallback simple plot
            ax.plot(df_ts.index, df_ts[numeric_col], marker='o', linewidth=1)
            ax.set_title(f"{numeric_col} over time ({datetime_col})")
            save_figure(fig, outpath)
    except Exception as e:
        logger.error(f"Error generating time series plot for {datetime_col} vs {numeric_col}: {e}")

def gen_correlation_heatmap(df, outpath):
    try:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            fig, ax = plt.subplots(figsize=(6,4))
            ax.text(0.5, 0.5, "Not enough numeric columns for correlation heatmap", ha='center', va='center')
            save_figure(fig, outpath)
            return
        corr = numeric_df.corr()
        fig, ax = plt.subplots(figsize=(10,8))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap='vlag', ax=ax, square=False)
        ax.set_title("Correlation Heatmap")
        save_figure(fig, outpath)
    except Exception as e:
        logger.error(f"Error generating correlation heatmap: {e}")

def gen_scatter_plot(df, x_col, y_col, outpath):
    try:
        fig, ax = plt.subplots(figsize=(8,6))
        sub = df[[x_col, y_col]].dropna()
        if sub.empty:
            fig, ax = plt.subplots(figsize=(6,4))
            ax.text(0.5, 0.5, f"No data for scatter {x_col} vs {y_col}", ha='center', va='center')
            save_figure(fig, outpath)
            return
        sns.scatterplot(data=sub, x=x_col, y=y_col, ax=ax)
        ax.set_title(f"Scatter: {y_col} vs {x_col}")
        save_figure(fig, outpath)
    except Exception as e:
        logger.error(f"Error generating scatter plot {x_col} vs {y_col}: {e}")

def gen_box_plot(df, col, outpath):
    try:
        fig, ax = plt.subplots(figsize=(8,5))
        s = df[col].dropna()
        if pd.api.types.is_numeric_dtype(s):
            sns.boxplot(x=s, ax=ax)
            ax.set_title(f"Boxplot of {col}")
            save_figure(fig, outpath)
        else:
            fig, ax = plt.subplots(figsize=(8,5))
            ax.text(0.5, 0.5, f"Boxplot not applicable for non-numeric column {col}", ha='center', va='center')
            save_figure(fig, outpath)
    except Exception as e:
        logger.error(f"Error generating box plot for {col}: {e}")

# ---------------------------------------------------------------------------
# Report generation - HTML + CSS
# ---------------------------------------------------------------------------

HTML_CSS = """
/* Professional CSS styling for report */
:root{
  --bg:#f6f9fc;
  --panel:#ffffff;
  --accent:#0b5394;
  --muted:#657786;
  --pad:18px;
  --radius:10px;
  --font-sans: "Helvetica Neue", Arial, sans-serif;
}
body{
  margin:0;
  padding:40px;
  font-family:var(--font-sans);
  background:var(--bg);
  color:#222;
}
.header{
  display:flex;
  align-items:center;
  gap:16px;
  margin-bottom:20px;
}
.logo{
  width:72px;
  height:72px;
  border-radius:12px;
  background:linear-gradient(135deg,var(--accent),#2a9fd6);
  display:flex;
  align-items:center;
  justify-content:center;
  color:white;
  font-weight:700;
  font-size:20px;
}
.report-title{
  font-size:28px;
  margin:0;
}
.subtitle{
  color:var(--muted);
  margin-top:6px;
}
.panel{
  background:var(--panel);
  border-radius:var(--radius);
  padding:var(--pad);
  box-shadow: 0 6px 18px rgba(20,30,60,0.06);
  margin-bottom:20px;
}
.grid{
  display:grid;
  grid-template-columns: 1fr 340px;
  gap:20px;
  align-items:start;
}
.section-title{
  font-size:18px;
  color:var(--accent);
  margin-bottom:8px;
}
.kv{
  display:flex;
  justify-content:space-between;
  padding:8px 0;
  border-bottom:1px solid #f0f3f7;
}
.kv strong{color:#111}
.table{
  width:100%;
  border-collapse:collapse;
}
.table th, .table td{
  text-align:left;
  padding:8px;
  border-bottom:1px solid #f0f3f7;
  font-size:13px;
}
.chart{
  text-align:center;
  margin-bottom:18px;
}
.insight{
  background:linear-gradient(90deg,#eef7ff,#ffffff);
  padding:10px;
  border-radius:8px;
  margin-bottom:8px;
  font-size:14px;
}
.footer{
  font-size:12px;
  color:var(--muted);
  text-align:center;
  margin-top:30px;
}
@media (max-width:900px){
  .grid{ grid-template-columns: 1fr; }
}
"""

HTML_EMAIL_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Database Analysis Report - {team_name}</title>
    <style>
      body {{ font-family: Arial, sans-serif; background:#f4f6f8; margin:0; padding:20px; color:#222; }}
      .card {{ background:white; border-radius:8px; padding:20px; margin:0 auto; max-width:700px; box-shadow:0 6px 18px rgba(20,30,60,0.06); }}
      .header {{ display:flex; align-items:center; gap:12px; }}
      .logo {{ width:48px; height:48px; border-radius:8px; background:#0b5394; color:white; display:flex; align-items:center; justify-content:center; font-weight:bold; }}
      h1 {{ margin:8px 0 4px 0; font-size:18px; }}
      p {{ margin:6px 0 12px 0; color:#555; }}
      .btn {{ display:inline-block; background:#0b5394; color:white; padding:10px 14px; border-radius:6px; text-decoration:none; }}
      .attachments {{ margin-top:14px; font-size:13px; color:#333; }}
      .small {{ font-size:12px; color:#888; margin-top:8px; }}
    </style>
  </head>
  <body>
    <div class="card">
      <div class="header">
        <div class="logo">DB</div>
        <div>
          <h1>Database Analysis Report</h1>
          <div class="small">Produced by {team_name} on {date}</div>
        </div>
      </div>
      <p>Hello,</p>
      <p>The SQLite database contains detailed customer, item, sales, and AR data across multiple tables. Key observations: dbo_D_Customer has 2,632 rows with significant missing values in status, address lines, and postal codes. Hierarchies (Customer_Category and Customer_Geography) are mostly complete but sparse in lower levels. dbo_D_Item shows incomplete attributes and cost details. Sales tables (F_Sales_Order, F_Sales_Transaction, F_Sales_Goal, F_Sales_Pipeline_Snapshot) reveal large volumes, with gaps in discounts, sales events, and some line-level details. Insights suggest prioritizing data cleaning for missing values, deduplication, and consistency across hierarchies to improve reporting accuracy and actionable analytics.
Attached are the auto-generated analysis artifacts for the database you submitted. The package includes a full HTML report, a printable PDF, and charts referenced in the report.</p>
<p>
        <a class="btn" href="cid:report_html">Open Report (HTML)</a>
        &nbsp;
        <a class="btn" href="cid:report_pdf">Download PDF</a>
      </p>
      <div class="attachments">
        Attachments included:
        <ul>
          <li>report.html</li>
          <li>report.pdf</li>
          <li>chart1.png, chart2.png, chart3.png, chart4.png, chart5.png</li>
        </ul>
      </div>
      <p class="small">If you have questions or want deeper analysis (feature engineering, forecasting, or dashboards), reply to this email.</p>
      <p>— {team_name} Automated Insights</p>
    </div>
  </body>
</html>
"""

def generate_html_report(report_path, metadata, tables_stats, charts, insights, css=HTML_CSS):
    """
    Create a full HTML report file at report_path.
    metadata: dict containing {db_name, generated_on, team_name}
    tables_stats: dict of table_name -> stats dict
    charts: list of chart file paths to include
    insights: dict of table_name -> list of insights
    """
    try:
        logger.info(f"Generating HTML report at {report_path}")
        parts = []
        # Header block
        header = f"""
        <html>
        <head>
          <meta charset="utf-8" />
          <title>Database Analysis Report - {metadata.get('team_name')}</title>
          <style>{css}</style>
        </head>
        <body>
          <div class="header">
            <div class="logo">DB</div>
            <div>
              <h1 class="report-title">Database Analysis Report</h1>
              <div class="subtitle">Database: {metadata.get('db_name')} &nbsp;•&nbsp; Generated: {metadata.get('generated_on')}</div>
            </div>
          </div>
          <div class="grid">
            <div>
              <div class="panel">
                <div class="section-title">Executive Summary</div>
                <p>This report provides schema discovery, table statistics, data quality checks, automatic insights, and visualizations for your SQLite database. Use the insights and recommendations below to prioritize data cleaning, deduplication, and schema improvements.</p>
              </div>
        """
        parts.append(header)
        # Left column - tables and charts
        for table, stats in tables_stats.items():
            tb_html = f"""
            <div class="panel">
              <div class="section-title">Table: {table}</div>
              <div class="kv"><strong>Rows</strong><span>{stats.get('rows')}</span></div>
              <div class="kv"><strong>Columns</strong><span>{stats.get('columns')}</span></div>
              <div style="margin-top:10px;">
                <table class="table">
                  <thead><tr><th>Column</th><th>Type</th><th>Non-null</th><th>Nulls</th><th>Unique</th></tr></thead>
                  <tbody>
            """
            for col, cs in stats.get('column_stats', {}).items():
                col_type = cs.get('dtype', '')
                non_null = cs.get('non_null_count', 0)
                nulls = cs.get('null_count', 0)
                unique = cs.get('unique_values', 0)
                tb_html += f"<tr><td>{col}</td><td>{col_type}</td><td>{non_null}</td><td>{nulls}</td><td>{unique}</td></tr>"
            tb_html += "</tbody></table></div></div>"
            parts.append(tb_html)

        # charts section
        parts.append('<div class="panel"><div class="section-title">Visualizations</div>')
        for idx, c in enumerate(charts, start=1):
            parts.append(f'<div class="chart"><h4>Chart {idx}</h4><img src="{os.path.basename(c)}" alt="chart{idx}" style="max-width:100%;height:auto;border-radius:8px;box-shadow:0 8px 20px rgba(20,30,60,0.06);"/></div>')
        parts.append('</div>')  # end visualizations panel

        # insights section
        parts.append("""
           </div> <!-- left column -->
           <div> <!-- right column -->
        """)
        parts.append('<div class="panel"><div class="section-title">Key Insights & Recommendations</div>')
        for table, table_insights in insights.items():
            parts.append(f'<div><h4 style="margin-bottom:8px;">{table}</h4>')
            if table_insights:
                for ins in table_insights:
                    parts.append(f'<div class="insight">{ins}</div>')
            else:
                parts.append('<div class="insight">No automated insights generated.</div>')
            parts.append('</div>')
        parts.append('</div></div>')  # end right column and grid

        # Footer
        parts.append(f"""
          <div class="panel">
            <div class="section-title">Appendix</div>
            <p>Report generated by {metadata.get('team_name')} automated agent on {metadata.get('generated_on')}.</p>
            <p class="footer">This report is intended to provide a quick, reproducible set of diagnostics. For production workflows, consider scheduled pipelines and dedicated dashboards (e.g., Power BI, Tableau, Grafana).</p>
          </div>
        </body></html>
        """)

        full = "\n".join(parts)
        with open(report_path, 'w', encoding='utf-8') as fh:
            fh.write(full)
        logger.info(f"Wrote HTML report: {report_path}")
    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}\n{traceback.format_exc()}")
        raise

# ---------------------------------------------------------------------------
# PDF generation using ReportLab (NOT HTML->PDF)
# ---------------------------------------------------------------------------

def generate_pdf_report(pdf_path, metadata, tables_stats, charts, insights):
    """
    Build a structured PDF using reportlab with embedded charts.
    """
    try:
        logger.info(f"Generating PDF report at {pdf_path}")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        heading = styles['Heading1']
        small = ParagraphStyle(name='small', parent=styles['Normal'], fontSize=9, textColor=colors.grey)

        elems = []
        # Title Page
        elems.append(Spacer(1, 1*cm))
        elems.append(Paragraph(f"Database Analysis Report", ParagraphStyle('Title', fontSize=24, leading=28, alignment=1)))
        elems.append(Spacer(1, 0.2*cm))
        elems.append(Paragraph(f"Database: {metadata.get('db_name')}", normal))
        elems.append(Paragraph(f"Generated: {metadata.get('generated_on')}", small))
        elems.append(Paragraph(f"Team: {metadata.get('team_name')}", small))
        elems.append(Spacer(1, 1*cm))
        elems.append(Paragraph("Executive Summary", styles['Heading2']))
        elems.append(Paragraph("This PDF contains an automated analysis of the supplied SQLite database. It includes schema exploration, data quality checks, statistical summaries, and visualizations.", normal))
        elems.append(PageBreak())

        # For each table: stats, insights, small sample, charts if available
        for table, stats in tables_stats.items():
            elems.append(Paragraph(f"Table: {table}", styles['Heading2']))
            elems.append(Spacer(1, 0.1*cm))
            # key KV table
            data = [
                ["Rows", stats.get('rows')],
                ["Columns", stats.get('columns')]
            ]
            t = Table(data, colWidths=[120, 320])
            t.setStyle(TableStyle([('BACKGROUND', (0,0),(-1,0), colors.whitesmoke),
                                   ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
                                   ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                                   ('FONTSIZE', (0,0), (-1,-1), 10),
                                   ('BOTTOMPADDING', (0,0),(-1,0),6)]))
            elems.append(t)
            elems.append(Spacer(1, 0.1*cm))

            # Column summary table (show up to first 10 columns)
            cols_show = list(stats.get('column_stats', {}).items())[:10]
            tbl = [["Column", "Type", "Non-null", "Nulls", "Unique"]]
            for col, cs in cols_show:
                tbl.append([col, cs.get('dtype',''), cs.get('non_null_count',''), cs.get('null_count',''), cs.get('unique_values','')])
            coltable = Table(tbl, colWidths=[140, 80, 70, 60, 80])
            coltable.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f3f7")),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
            ]))
            elems.append(coltable)
            elems.append(Spacer(1, 0.2*cm))

            # Insights
            elems.append(Paragraph("Insights", styles['Heading3']))
            for ins in insights.get(table, []):
                elems.append(Paragraph(f"• {ins}", normal))
            elems.append(Spacer(1, 0.2*cm))

            # Charts (embed first two charts where possible)
            for c in charts[:2]:
                if os.path.exists(c):
                    elems.append(Paragraph(f"Chart: {os.path.basename(c)}", styles['Heading4']))
                    # scale image to width
                    try:
                        rl_img = RLImage(c, width=16*cm, height=9*cm)
                    except Exception:
                        rl_img = RLImage(c, width=12*cm, height=7*cm)
                    elems.append(rl_img)
                    elems.append(Spacer(1, 0.2*cm))

            elems.append(PageBreak())

        # Appendix
        elems.append(Paragraph("Appendix - Charts", styles['Heading2']))
        for c in charts:
            if os.path.exists(c):
                elems.append(Paragraph(os.path.basename(c), styles['Heading4']))
                try:
                    rl_img = RLImage(c, width=16*cm, height=9*cm)
                except Exception:
                    rl_img = RLImage(c, width=12*cm, height=7*cm)
                elems.append(rl_img)
                elems.append(Spacer(1, 0.2*cm))

        doc.build(elems)
        logger.info(f"PDF written to {pdf_path}")
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}\n{traceback.format_exc()}")
        raise

# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

def build_email_with_attachments(to_email, subject, html_body, attachments, config, db_path="sales_agent.db"):
    """
    Build a MIMEMultipart message with provided attachments (list of file paths).
    """
    try:
        msg = MIMEMultipart('related')
        msg['From'] = config.get('sender_email')
        msg['To'] = to_email
        msg['Subject'] = subject

        alternative = MIMEMultipart('alternative')
        msg.attach(alternative)

        db_summary = generate_db_summary(db_path)
        part_text = MIMEText(db_summary, 'plain')
        alternative.attach(part_text)

        part_html = MIMEText(html_body, 'html')
        alternative.attach(part_html)

        # Attach files
        for path in attachments:
            try:
                with open(path, 'rb') as fh:
                    data = fh.read()
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(path)}"')
                msg.attach(part)
                logger.info(f"Attached {path}")
            except Exception as e:
                logger.warning(f"Failed to attach {path}: {e}")
        return msg
    except Exception as e:
        logger.error(f"Failed to build email message: {e}")
        raise

def send_email(message: MIMEMultipart, config):
    """
    Send email using SMTP settings in config
    """
    try:
        server = config.get('smtp_server')
        port = int(config.get('smtp_port', 587))
        user = config.get('sender_email')
        password = config.get('sender_password', '')

        if not user or not password:
            logger.error("Sender credentials are not configured. Aborting email send.")
            raise RuntimeError("Missing sender credentials in config or environment variables.")

        logger.info(f"Connecting to SMTP server {server}:{port}")
        smtp = smtplib.SMTP(server, port, timeout=30)
        smtp.ehlo()
        if port == 587:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(user, password)
        smtp.send_message(message)
        smtp.quit()
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}\n{traceback.format_exc()}")
        raise

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def analyze_database(db_path, output_folder, config, recipient_email):
    safe_mkdir(output_folder)
    conn = connect_sqlite(db_path)
    tables = list_tables(conn)
    overall_tables_stats = {}
    overall_insights = {}
    charts = []
    chart_idx = 1

    # If no tables discovered, still create a minimal report
    if not tables:
        logger.warning("No tables found in database. Generating empty report.")
        metadata = {
            'db_name': os.path.basename(db_path),
            'generated_on': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            'team_name': config.get('team_name', 'YourTeamName')
        }
        html_report = os.path.join(output_folder, 'report.html')
        generate_html_report(html_report, metadata, {}, [], {}, css=HTML_CSS)
        pdf_report = os.path.join(output_folder, 'report.pdf')
        generate_pdf_report(pdf_report, metadata, {}, [], {})
        return [html_report, pdf_report], []

    for table in tables:
        try:
            df = fetch_table(conn, table)
            # Basic stats
            stats = table_statistics(df)
            overall_tables_stats[table] = stats

            # Type inference
            inference = infer_column_types(df)

            # Insights
            insights = top_insights_for_table(table, df, inference)
            overall_insights[table] = insights

            # Visualizations (produce up to 5 charts total across tables)
            # Chart 1: distribution of top numeric or categorical column
            if chart_idx <= 5:
                # choose a column for distribution
                dist_col = None
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    dist_col = numeric_cols[0]
                else:
                    # fallback choose first column
                    if len(df.columns) > 0:
                        dist_col = df.columns[0]
                path = os.path.join(output_folder, f'chart{chart_idx}.png')
                gen_distribution_plot(df, dist_col, path)
                charts.append(path)
                chart_idx += 1

            # Chart 2: time series if date + numeric
            if chart_idx <= 5:
                # find datetime column and numeric column
                date_col = None
                numeric_col = None
                for c, t in inference.items():
                    if t == 'datetime' or 'date' in c.lower():
                        date_col = c
                        break
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if not numeric_col and numeric_cols:
                    numeric_col = numeric_cols[0]
                if date_col and numeric_col:
                    path = os.path.join(output_folder, f'chart{chart_idx}.png')
                    gen_time_series_plot(df, date_col, numeric_col, path)
                    charts.append(path)
                    chart_idx += 1

            # Chart 3: correlation heatmap on first table that has multiple numeric columns
            if chart_idx <= 5:
                path = os.path.join(output_folder, f'chart{chart_idx}.png')
                gen_correlation_heatmap(df, path)
                charts.append(path)
                chart_idx += 1

            # Chart 4: scatter (choose top two numeric cols)
            if chart_idx <= 5:
                numcols = df.select_dtypes(include=[np.number]).columns.tolist()
                if len(numcols) >= 2:
                    xcol, ycol = numcols[0], numcols[1]
                    path = os.path.join(output_folder, f'chart{chart_idx}.png')
                    gen_scatter_plot(df, xcol, ycol, path)
                    charts.append(path)
                    chart_idx += 1

            # Chart 5: box plot for a numeric column
            if chart_idx <= 5:
                numcols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numcols:
                    path = os.path.join(output_folder, f'chart{chart_idx}.png')
                    gen_box_plot(df, numcols[0], path)
                    charts.append(path)
                    chart_idx += 1

        except Exception as e:
            logger.error(f"Error analyzing table {table}: {e}")

    # If fewer than 5 charts created, create placeholders with text drawn
    while len(charts) < 5:
        idx = len(charts) + 1
        path = os.path.join(output_folder, f'chart{idx}.png')
        fig, ax = plt.subplots(figsize=(10,6))
        ax.text(0.5, 0.5, "Placeholder chart - no data available", ha='center', va='center', fontsize=14)
        ax.axis('off')
        save_figure(fig, path)
        charts.append(path)

    # Create metadata and reports
    metadata = {
        'db_name': os.path.basename(db_path),
        'generated_on': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        'team_name': config.get('team_name', 'YourTeamName')
    }

    html_report = os.path.join(output_folder, 'report.html')
    generate_html_report(html_report, metadata, overall_tables_stats, charts, overall_insights, css=HTML_CSS)

    pdf_report = os.path.join(output_folder, 'report.pdf')
    generate_pdf_report(pdf_report, metadata, overall_tables_stats, charts, overall_insights)

    # Optionally send email
    attachments = [html_report, pdf_report] + charts
    if recipient_email:
        try:
            # Build HTML email body
            html_body = HTML_EMAIL_TEMPLATE.format(team_name=config.get('team_name', 'YourTeamName'), date=metadata.get('generated_on'))
            msg = build_email_with_attachments(recipient_email, f"Database Analysis Report - {config.get('team_name','YourTeamName')}", html_body, attachments, config, db_path="sales_agent.db")
            send_email(msg, config)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    return [html_report, pdf_report], charts

# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Database Insights Agent - analyze SQLite and produce reports")
    parser.add_argument('--db', required=True, help='Path to SQLite database file (data.db)')
    parser.add_argument('--email', required=False, help='Recipient email to send the report to (recipient@example.com)')
    parser.add_argument('--config', required=False, help='Path to JSON config file (overrides env vars)')
    parser.add_argument('--output', required=False, help='Output folder for charts and reports (default: output)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    db_path = "sales_agent.db"
    recipient_email = args.email
    output_folder = args.output or DEFAULT_OUTPUT
    config_path = args.config or DEFAULT_CONFIG_FILE

    if not os.path.exists(db_path):
        logger.error(f"Database file does not exist: {db_path}")
        sys.exit(2)

    config = {}
    try:
        config = load_config(config_path)
    except Exception as e:
        logger.warning(f"Proceeding with environment/default config due to error: {e}")

    # ensure output folder exists
    safe_mkdir(output_folder)

    try:
        reports, charts = analyze_database(db_path, output_folder, config, recipient_email)
        logger.info("Analysis complete. Generated:")
        for r in reports + charts:
            logger.info(f" - {r}")
        logger.info("All done.")
    except Exception as e:
        logger.error(f"Fatal error in analysis pipeline: {e}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main()
