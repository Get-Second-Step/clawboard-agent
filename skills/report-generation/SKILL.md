---
name: report-generation
description: >
  Branded audit report generator. Agent name: LAKSHMI (Goddess of prosperity —
  turns audit findings into revenue-generating insights). Creates HTML → PDF
  with Second Step dark branding.
agent_name: Lakshmi
agent_role: Report Generator & Insights Synthesizer
agent_avatar: 💰
---

# LAKSHMI — Report Generation

> *"Lakshmi turns findings into fortune — every recommendation is a path to more revenue."*

## Report Sections

1. **Cover Page** — Client name, audit date, platforms audited, agent team roster
2. **Executive Summary** — Overall Ads Health Score, grade, top 3 critical findings
3. **Score Dashboard** — Visual score cards: Shiva / Brahma / Vishnu / Arjuna scores
4. **Critical Findings** — ALL critical severity items, sorted by revenue impact
5. **Platform Deep Dives** — Full findings per platform (Shiva / Brahma / Vishnu)
6. **Budget & Bidding Review** — Arjuna's findings
7. **Prioritized Action Plan** — Top 10 actions ranked by: Impact × Ease ÷ Effort
8. **Wasted Spend Summary** — Total estimated monthly waste with per-category breakdown
9. **Footer** — Agency branding, contact, generation date

---

## Score Aggregation Formula

```
Overall_Ads_Health_Score = weighted average by active platforms

If Google + Meta + GA4:
  = (Google × 0.40) + (Meta × 0.35) + (GA4 × 0.25)

If Google only:
  = Google Score

If Meta only:
  = Meta Score

Adjust weights based on which platforms are active and budget allocation.
```

## Grade → Action Language

| Grade | Score | Report Language |
|---|---|---|
| A | 90–100 | "Your account is performing at elite level. Focus on incremental gains." |
| B | 75–89 | "Strong foundation with clear optimization opportunities." |
| C | 60–74 | "Notable issues are costing you conversions and wasted spend." |
| D | 40–59 | "Significant problems requiring urgent attention within 7 days." |
| F | <40 | "Critical failures — immediate intervention required to stop revenue loss." |

---

## Branding Rules

```css
--bg: #1b1b1b;
--surface: #242424;
--accent: #E87811;
--text: #ffffff;
--text-secondary: #b0b0b0;
--font-heading: 'Inter', sans-serif;
--font-body: system-ui, sans-serif;

/* Score colors */
--score-a: #4caf50;   /* green */
--score-b: #8bc34a;   /* light green */
--score-c: #ff9800;   /* orange */
--score-d: #f44336;   /* red */
--score-f: #b71c1c;   /* dark red */

/* Severity colors */
--critical: #f44336;
--high: #ff9800;
--medium: #2196f3;
--low: #4caf50;
```

## Action Plan Scoring Formula

```
Priority_Score = (Impact × 3) + (Speed × 2) - (Effort × 1)

Impact: 1-5 (1=minor, 5=critical revenue impact)
Speed: 1-5 (1=months to see results, 5=immediate)
Effort: 1-5 (1=5 minutes, 5=weeks of dev work)

Sort by Priority_Score descending.
Quick Wins = top 5 actions where Effort ≤ 2
```

## Agent Team Roster (include in every report)

Show which agents ran the analysis:

| Agent | Domain | Avatar |
|---|---|---|
| Shiva | Google Ads (74 checks) | 🔱 |
| Brahma | Meta Ads (46 checks) | 🌸 |
| Vishnu | GA4 Analytics (30 checks) | 🌊 |
| Arjuna | Budget & Bidding (10 checks) | 🏹 |
| Saraswati | Campaign Strategy | 🎯 |
| Lakshmi | Report Generation | 💰 |

---

## PDF Generation Command

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --print-to-pdf="reports/{slug}_audit_{date}.pdf" \
  --no-margins \
  --print-background \
  "reports/{slug}_audit_{date}.html"
```

## File Naming Convention

```
reports/{client_slug}_audit_{YYYYMMDD}_{HHMMSS}.pdf
reports/{client_slug}_audit_{YYYYMMDD}_{HHMMSS}.html
reports/{client_slug}_audit_{YYYYMMDD}_{HHMMSS}.json
```
