---
name: ga4-audit
description: Use this skill when auditing a Google Analytics 4 property. Runs 30 checks across 5 categories.
---

# Google Analytics 4 Audit Skill

## When to Use
When the user asks to audit a GA4 property, or when the main audit agent delegates analytics analysis.

## 30-Point Audit Checklist

### 1. GA4 Implementation (6 checks)
- [ ] GA4 property created and receiving data
- [ ] Measurement ID correctly implemented on all pages
- [ ] Data stream configured (Web, iOS, Android as needed)
- [ ] Enhanced Measurement enabled (scrolls, outbound clicks, file downloads, video engagement)
- [ ] Google Signals enabled for cross-device reporting
- [ ] Data retention set to 14 months (not default 2 months)

### 2. Event Tracking (7 checks)
- [ ] Page_view events firing correctly on all pages
- [ ] Key interaction events tracked (button clicks, form submits, CTAs)
- [ ] E-commerce events configured if applicable (view_item, add_to_cart, purchase)
- [ ] Custom events properly named (snake_case, no spaces)
- [ ] Event parameters configured with useful dimensions
- [ ] No duplicate events firing (check for GTM + gtag.js conflicts)
- [ ] Debug mode tested in GA4 DebugView

### 3. Conversion Setup (6 checks)
- [ ] Key conversion events marked as conversions in GA4
- [ ] Conversion counting set correctly (once per event vs. every event)
- [ ] Conversion values assigned where applicable
- [ ] Google Ads linked and importing GA4 conversions
- [ ] Attribution model reviewed (data-driven recommended)
- [ ] Cross-domain tracking configured if multiple domains

### 4. Data Quality (6 checks)
- [ ] No significant data discrepancies vs. server logs or other tools
- [ ] Internal traffic filtered (office IP exclusions)
- [ ] Bot/spam traffic filtered
- [ ] UTM parameters consistent across marketing channels
- [ ] Referral exclusions configured (payment gateways, SSO)
- [ ] Sampling not significantly affecting reports

### 5. Reporting & Integration (5 checks)
- [ ] Google Ads account linked and active
- [ ] Google Search Console linked
- [ ] Custom audiences created for remarketing
- [ ] Key reports built (Acquisition, Engagement, Monetization)
- [ ] BigQuery export enabled for advanced analysis (recommended)

## Scoring Formula

```
score = 100 - (critical_count × 15) - (high_count × 8) - (medium_count × 4) - (low_count × 2)
score = max(0, min(100, score))
```

## Output Format

Return findings as JSON:
```json
{
  "platform": "google_analytics",
  "score": 82,
  "findings": [
    {
      "id": "GA4-001",
      "category": "data_quality",
      "title": "Data Retention Set to 2 Months",
      "severity": "medium",
      "description": "Default data retention is 2 months. Historical data is lost.",
      "action": "Change data retention to 14 months in Admin > Data Settings > Data Retention",
      "effort": "5 minutes",
      "impact": "medium"
    }
  ]
}
```
