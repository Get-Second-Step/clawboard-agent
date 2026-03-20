---
name: report-generation
description: Use this skill when generating the final branded PDF audit report from collected findings.
---

# Report Generation Skill

## When to Use
After all platform audits are complete and findings are aggregated. Generates the final branded HTML that gets converted to PDF.

## Report Sections

1. **Cover Page** — Client name, audit date, Second Step logo, platforms audited
2. **Executive Summary** — Overall score, platforms audited, critical issue count, top 3 findings
3. **Score Dashboard** — Visual score cards for each platform (color-coded)
4. **Google Ads Findings** — Sorted by severity, with actions
5. **Meta Ads Findings** — Sorted by severity, with actions
6. **GA4 Findings** — Sorted by severity, with actions
7. **Action Plan** — Top 10 prioritized actions with effort estimates
8. **Footer** — Second Step branding, contact info, generation date

## Branding Rules

- Background: #1b1b1b (dark)
- Accent: #E87811 (orange)
- Text: #ffffff (white), #b0b0b0 (secondary)
- Font: Inter (headings), system sans-serif (body)
- Score colors: ≥75 green (#4caf50), 50-74 orange (#ff9800), <50 red (#f44336)
- Severity colors: Critical (#f44336), High (#ff9800), Medium (#2196f3), Low (#4caf50)

## PDF Generation

Use Chrome headless to convert HTML to PDF:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --print-to-pdf="reports/output.pdf" \
  --no-margins --print-background \
  "reports/output.html"
```

## File Naming

`reports/{client_slug}_audit_{YYYYMMDD}_{HHMMSS}.{pdf|html|json}`
