---
name: ga4-audit
description: >
  GA4 & Analytics deep audit — 30 checks, 5 categories. Agent name: VISHNU
  (Preserver of data, guardian of attribution truth).
agent_name: Vishnu
agent_role: Analytics & Attribution Preserver
agent_avatar: 🌊
---

# VISHNU — GA4 Audit (30-Point Deep Analysis)

> *"Vishnu preserves — data integrity, attribution accuracy, measurement truth."*

## Scoring Weights

| Category | Weight | Checks |
|---|---|---|
| Implementation | 20% | V01–V06 |
| Event Tracking | 25% | V07–V13 |
| Conversion Setup | 25% | V14–V19 |
| Data Quality | 20% | V20–V25 |
| Integrations | 10% | V26–V30 |

---

## CATEGORY 1: Implementation (20%)

### V01 — GA4 Property Created and Receiving Data
- PASS: data stream active, events flowing | FAIL: property exists but no data
- Severity: Critical

### V02 — Measurement ID on All Pages
- PASS: G-XXXXXXXX on every page, no missing pages
- FAIL: missing on key funnel pages — conversion gaps
- Severity: Critical

### V03 — Enhanced Measurement Enabled
- PASS: scrolls, outbound clicks, site search, video engagement, file downloads all ON
- WARNING: partially enabled — missing behavioral data
- Severity: Medium

### V04 — Google Signals Enabled
- PASS: ON — enables cross-device reporting, demographic data, remarketing
- WARNING: OFF — losing cross-device attribution, demo reports blank
- Severity: Medium

### V05 — Data Retention: 14 Months (Not Default 2 Months)
- PASS: 14 months | FAIL: 2 months (default) — historical data deleted every 60 days
- This is always a finding on new accounts.
- Severity: Medium (5-minute fix — never miss this)

### V06 — No GTM + gtag.js Conflict
- PASS: only one implementation method active
- FAIL: both GTM and hard-coded gtag.js on same pages — duplicate events
- Severity: Critical

---

## CATEGORY 2: Event Tracking (25%)

### V07 — page_view Firing on All Pages
- PASS: every URL gets page_view | FAIL: SPAs missing page_view on route changes
- Severity: High

### V08 — Key CTA Interactions Tracked
- PASS: form submissions, button clicks, CTA clicks tracked as events
- FAIL: no custom events — only auto-collected events
- Severity: High

### V09 — E-commerce Events (if applicable)
- PASS: view_item, add_to_cart, begin_checkout, purchase all firing
- FAIL: missing purchase event — revenue data gap
- Severity: Critical (e-commerce)

### V10 — Custom Events Properly Named
- PASS: snake_case, descriptive, consistent (e.g., `cta_click_hero`)
- FAIL: spaces in names, PascalCase, or generic names ("click")
- Severity: Medium

### V11 — Event Parameters Configured
- PASS: useful dimensions on events (page_category, user_type, form_name)
- WARNING: events firing with no parameters — can't segment
- Severity: Medium

### V12 — No Duplicate Events
- PASS: each event fires once per interaction
- FAIL: duplicate firings — inflates all engagement metrics
- Severity: High

### V13 — Debug Mode Tested in DebugView
- PASS: recently validated via GA4 DebugView
- WARNING: never validated — may have silent breakage
- Severity: Medium

---

## CATEGORY 3: Conversion Setup (25%)

### V14 — Key Events Marked as Conversions
- PASS: form_submit, purchase, demo_request, etc. marked as conversions
- FAIL: no conversions defined — can't optimize campaigns toward goals
- Severity: Critical

### V15 — Conversion Counting Set Correctly
- PASS: lead gen = "Once per session", e-com = "Once per event"
- FAIL: "Once per event" on lead gen = single user submitting twice = 2 conversions
- Severity: High

### V16 — Conversion Values Assigned
- PASS: revenue passed to purchase event, estimated values on leads
- WARNING: no values = can't calculate ROI or ROAS
- Severity: High

### V17 — Google Ads Linked and Importing Conversions
- PASS: linked, GA4 audiences and conversions available in Google Ads
- FAIL: not linked — Google Ads blind to GA4 data
- Severity: Critical

### V18 — Attribution Model: Data-Driven
- PASS: data-driven attribution selected
- WARNING: last-click — unfairly credits bottom-funnel, undercredits awareness
- Severity: Medium

### V19 — Cross-Domain Tracking Configured (if applicable)
- PASS: linked domains share user session (e.g., site.com ↔ checkout.site.com)
- FAIL: checkout on subdomain breaks sessions — conversion rate appears 0%
- Severity: Critical (when multiple domains used)

---

## CATEGORY 4: Data Quality (20%)

### V20 — Internal Traffic Filtered
- PASS: office IP(s) excluded via internal traffic definition
- FAIL: team browsing inflates sessions, lowers CVR
- Severity: Medium

### V21 — Bot/Spam Traffic Filtered
- PASS: "Enable all" filters active, known bot IPs excluded
- WARNING: no filters — distorted data in low-traffic accounts
- Severity: Medium

### V22 — UTM Parameters Consistent Across Channels
- PASS: `utm_source`, `utm_medium`, `utm_campaign` on all paid/email links
- FAIL: inconsistent UTMs — Direct traffic inflated, channel attribution broken
- Severity: High

### V23 — Referral Exclusions Configured
- PASS: payment gateways (Stripe, PayPal), SSO providers excluded from referral
- FAIL: Stripe shows as referral source — conversions attributed to payment processor
- Severity: High

### V24 — Sampling Not Affecting Key Reports
- PASS: date ranges set to minimize sampling, or reports exported unsampled
- WARNING: Google Analytics sampling >20% on key reports
- Severity: Medium

### V25 — Hostname Filters (Correct Property Only)
- PASS: only traffic from owned domains counted
- FAIL: scrapers and bots sending fake traffic to property
- Severity: Medium

---

## CATEGORY 5: Integrations (10%)

### V26 — Google Ads Linked (see V17)
### V27 — Google Search Console Linked
- PASS: linked — organic search data visible in GA4
- WARNING: not linked — missing keyword data
- Severity: Low

### V28 — BigQuery Export Enabled
- PASS: GA4 raw data streaming to BigQuery for advanced analysis
- WARNING: not enabled — relying on sampled aggregated data only
- Severity: Low (highly recommended for high-traffic sites)

### V29 — Custom Audiences Created for Remarketing
- PASS: audiences built for: cart abandoners, blog readers, high engagers
- WARNING: no custom audiences — paid channels missing retargeting fuel
- Severity: Medium

### V30 — Key Reports Built (Acquisition, Funnel, Monetization)
- PASS: custom funnel exploration and acquisition reports saved
- WARNING: only standard reports used — missing funnel visibility
- Severity: Low

---

## Output Format

```json
{
  "agent": "Vishnu",
  "platform": "google_analytics_4",
  "health_score": 78,
  "grade": "B",
  "category_scores": {
    "implementation": 85,
    "event_tracking": 75,
    "conversion_setup": 80,
    "data_quality": 70,
    "integrations": 60
  },
  "findings": [...],
  "quick_wins": [
    {
      "id": "V05",
      "title": "Data Retention: Change 2 Months → 14 Months",
      "effort": "5 minutes",
      "location": "Admin > Data Settings > Data Retention"
    }
  ]
}
```
