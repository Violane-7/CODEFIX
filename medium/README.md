# AI CODEFIX 2025 - Database Insights Agent (Medium)

An end-to-end, production-ready agent that analyzes any SQLite database and produces:
- Schema auto-discovery
- Table statistics and data-quality checks
- 5+ high-resolution visualizations (PNG)
- Complete HTML report (styled) and a structured PDF (ReportLab)
- Optional email delivery with attachments (HTML + PDF + charts)

This repository contains a single runnable CLI: `db_analyzer.py`

---

## Project Structure
medium/
├── README.md
├── db_analyzer.py
├── requirements.txt
├── config.example.json
└── output/
├── chart1.png
├── chart2.png
├── chart3.png
├── chart4.png
├── chart5.png
├── report.html
└── report.pdf















# 🟡 MEDIUM Challenge: Database Insights Agent

## AI CODEFIX 2025 - Data Analysis & Automation

---

## 🎯 Challenge Overview

Build an intelligent agent that analyzes a database and automatically sends a comprehensive insights report via email.

**Time**: 60 minutes
**Difficulty**: Medium
**Skills**: Database Analysis, Data Visualization, Email Automation, Report Generation

---

## 📋 Problem Statement

You are given a SQLite database file (`data.db`) containing business data. Your task is to:

1. **Analyze the database** - Understand schema, relationships, and data patterns
2. **Generate insights** - Extract meaningful statistics and trends
3. **Create visualizations** - Generate charts and graphs (like Power BI)
4. **Build a report** - Compile analysis into a professional report
5. **Send via email** - Automatically email the report to specified recipients

---

## 🗂️ What You'll Receive

- `data.db` - SQLite database file (will be provided)
- Email credentials/configuration (will be provided during event)
- This README with requirements

---

## 📊 Your Task

### Required Deliverables

Create a Python script (`db_analyzer.py`) that:

1. **Connects to database**
   - Read `data.db` file
   - Explore tables and schema
   - Handle any database structure

2. **Performs analysis**
   - Row counts per table
   - Key statistics (min, max, avg, etc.)
   - Data quality checks (nulls, duplicates)
   - Interesting patterns or insights

3. **Generates visualizations**
   - At least 3 different charts/graphs
   - Professional appearance
   - Save as PNG/JPG files

4. **Creates report**
   - Text summary of findings
   - Embedded visualizations
   - Professional formatting (can be HTML or PDF)

5. **Sends email**
   - Attach report and visualizations
   - Professional email body
   - Send to provided email address

---

## 🔨 Implementation Requirements

### Core Functionality

```python
# Your script should be runnable like this:
python db_analyzer.py --db data.db --email recipient@example.com
```

### Suggested Libraries

```python
import sqlite3           # Database connection
import pandas as pd      # Data analysis
import matplotlib.pyplot as plt  # Visualizations
import seaborn as sns    # Advanced visualizations
import smtplib           # Email sending
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
```

### Database Analysis Steps

1. **Discover Schema**
```python
# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# Get column info for each table
cursor.execute(f"PRAGMA table_info({table_name});")
```

2. **Extract Data**
```python
# Use pandas for easy analysis
df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
```

3. **Generate Statistics**
```python
# Basic stats
df.describe()
df.info()
df.isnull().sum()
```

4. **Create Visualizations**
```python
# Examples:
- Bar chart of counts
- Line chart of trends
- Pie chart of distributions
- Heatmap of correlations
```

---

## 📧 Email Format

Your task is to build a Sales Analysis Email Agent that:

1. Reads data from the provided SQLite . db file

2. Performs sales analytics

3. Generates a PDF report with charts

4. Sends an email summary + PDF attachment in the required format.

### Subject
```
Database Analysis Report - [Your Team Name]
```

### Body Template
```
Dear Recipient,

Please find the automated database analysis report below.

=== DATABASE SUMMARY ===
- Total Tables: X
- Total Records: Y
- Analysis Date: [timestamp]

=== KEY INSIGHTS ===
1. [Insight 1]
2. [Insight 2]
3. [Insight 3]

 PDF( report with charts  Proffesional  business report with visualization and chart ) 
[Attached: chart1.png, chart2.png, chart3.png]

Best regards,
[Your Team Name]
AI CODEFIX 2025
```

---

## 📊 Visualization Requirements

### Minimum Required Charts (3)

1. **Chart 1**: Distribution/Count Chart
   - Bar chart or pie chart
   - Show counts or distributions

2. **Chart 2**: Trend/Time Series (if applicable)
   - Line chart or area chart
   - Show changes over time

3. **Chart 3**: Relationship/Correlation
   - Scatter plot or heatmap
   - Show relationships between variables

### Quality Guidelines

- Clear titles and labels
- Proper legends
- Readable fonts
- Professional color schemes
- Save as high-resolution images

---

## ⚙️ Email Configuration

**SMTP Settings** (will be provided during event):
```python
SMTP_SERVER = "smtp.gmail.com"  # Example
SMTP_PORT = 587
SENDER_EMAIL = "provided@event.com"
SENDER_PASSWORD = "will_be_provided"
```

**Important**:
- Email credentials will be shared during the event
- Use environment variables or config file (not hardcode)
- Test with your own email first

---

## 🚀 Getting Started

### Step 1: Setup Environment

```bash
cd medium
pip install pandas matplotlib seaborn sqlite3
```

### Step 2: Explore Database

```bash
# Open database in SQLite browser or Python
sqlite3 data.db
.tables
.schema table_name
```

### Step 3: Plan Your Analysis

1. What tables exist?
2. What relationships are there?
3. What questions can the data answer?
4. What visualizations make sense?

### Step 4: Build and Test

1. Write database exploration code
2. Generate sample visualizations
3. Format report
4. Test email sending (to yourself first)

---

## 📊 Evaluation Criteria

### Database Analysis (30%)
- [ ] Successfully connects to database
- [ ] Explores all tables
- [ ] Generates meaningful statistics
- [ ] Identifies data patterns

### Visualizations (25%)
- [ ] Creates 3+ charts
- [ ] Professional appearance
- [ ] Appropriate chart types
- [ ] Clear and informative

### Report Quality (25%)
- [ ] Well-structured
- [ ] Clear insights
- [ ] Professional formatting
- [ ] Complete information

### Email Automation (20%)
- [ ] Successfully sends email
- [ ] Proper formatting
- [ ] Attachments included
- [ ] Professional content

---

## 💡 Tips & Hints

### Database Tips
- Use `PRAGMA table_info(table_name)` to get column details
- Check for foreign keys: `PRAGMA foreign_key_list(table_name)`
- Use pandas for easy data manipulation

### Visualization Tips
- Use `plt.tight_layout()` to prevent label cutoff
- Save with `dpi=300` for high quality
- Use seaborn themes for professional look

### Email Tips
- Test with your own email first
- Use MIMEMultipart for attachments
- HTML emails look more professional than plain text

### Common Pitfalls
- Don't hardcode credentials
- Handle missing data gracefully
- Check email size limits (attachments)
- Test database connection error handling

---

## 🔍 Example Analysis Outline

```
1. EXECUTIVE SUMMARY
   - Database overview
   - Key findings (3-5 bullet points)

2. DATA OVERVIEW
   - Number of tables
   - Total records
   - Data types present

3. DETAILED ANALYSIS
   - Per-table statistics
   - Data quality observations
   - Interesting patterns

4. VISUALIZATIONS
   - Chart 1: [Description]
   - Chart 2: [Description]
   - Chart 3: [Description]

5. RECOMMENDATIONS
   - Insights for decision making
   - Data quality improvements
```

---

## 📁 Expected Deliverables

```
medium/
├── README.md              # This file
├── db_analyzer.py         # Your main script
├── data.db               # Database (provided)
├── requirements.txt       # Dependencies
└── output/               # Generated files (optional)
    ├── report.html or report.pdf
    ├── chart1.png
    ├── chart2.png
    └── chart3.png
```

---

## ⚠️ Important Notes

1. **Database will be provided** - Structure is unknown until event
2. **Email credentials provided on event day** - Don't use your personal accounts
3. **Automatic analysis** - Your code should work on ANY database structure
4. **Time limit** - 60 minutes, plan accordingly
5. **Test thoroughly** - Send test email to yourself first

---

## 🎓 Skills Tested

- SQL queries and database navigation
- Data analysis with pandas
- Visualization with matplotlib/seaborn
- Report generation
- Email automation
- Code organization
- Error handling

---

## ❓ FAQs

**Q: What if I don't know the database structure?**
A: Your code should automatically discover it using SQL queries.

**Q: Can I use libraries like plotly or other viz tools?**
A: Yes! Any Python visualization library is allowed.

**Q: What format should the report be?**
A: HTML or PDF recommended, but plain text with attached images is acceptable.

**Q: What if email sending fails?**
A: Make sure your code saves the report locally as backup.

**Q: How many insights should I include?**
A: At least 3-5 meaningful insights from the data.

**Q: Can I use AI tools to help?**
A: Yes, but understand the code you're submitting.

---

## 🏆 Bonus Points

- Generate PDF report (not just HTML)
- Interactive visualizations
- Advanced statistical analysis
- Beautiful email HTML template
- Comprehensive error handling
- Logging and progress indicators

---

## 📚 Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/index.html)
- [Email MIME Guide](https://docs.python.org/3/library/email.examples.html)

---

## 🎯 Success Criteria

Your solution should:
1. Run without errors on the provided database
2. Generate meaningful insights automatically
3. Create professional visualizations
4. Successfully send formatted email
5. Complete within 60 minutes

---

**Good luck! Show us your data analysis and automation skills!** 📊✉️

---

*AI CODEFIX 2025 - Medium Challenge*
