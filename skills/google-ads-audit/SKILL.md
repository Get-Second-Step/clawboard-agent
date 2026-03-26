---
name: google-ads-audit
description: >
  Google Ads deep audit — 74 checks, 6 weighted categories. Agent name: SHIVA
  (Destroyer of waste, optimizer of spend). Outputs Health Score 0-100 with
  wasted spend estimate in $.
agent_name: Shiva
agent_role: Google Ads Destroyer of Waste
agent_avatar: 🔱
---

# SHIVA — Google Ads Audit (74-Point Deep Analysis)

> *"Shiva destroys what no longer serves — wasted spend, broken tracking, poor structure."*

## Scoring Weights

| Category | Weight | Checks |
|---|---|---|
| Conversion Tracking | 25% | G01–G16 |
| Wasted Spend | 20% | G17–G31 |
| Account Structure | 15% | G32–G43 |
| Keywords & Quality Score | 15% | G44–G55 |
| Ads & Assets | 15% | G56–G67 |
| Campaign Settings | 10% | G68–G74 |

## Health Score Formula

```
Category_Score = 100 - (critical×15) - (high×8) - (medium×4) - (low×2)
Google_Health_Score =
  (Conv × 0.25) + (Waste × 0.20) + (Struct × 0.15) +
  (KW × 0.15) + (Ads × 0.15) + (Settings × 0.10)
Score = max(0, min(100, Score))
```

| Grade | Score | Action |
|---|---|---|
| A | 90–100 | Minor polish only |
| B | 75–89 | Improvement opportunities |
| C | 60–74 | Notable issues |
| D | 40–59 | Significant problems |
| F | <40 | Urgent intervention required |

---

## CATEGORY 1: Conversion Tracking (25%)

### G01 — Google Tag / gtag.js Installed
- PASS: tag on all pages, fires every PageView | FAIL: missing or homepage only
- Severity: Critical

### G02 — Auto-Tagging Enabled
- PASS: ON in account settings | FAIL: manual UTM only — GCLID not passed, data-driven attribution breaks
- Severity: High

### G03 — Primary Conversion Actions Defined
- PASS: ≥1 primary conversion per campaign objective | FAIL: secondary only or none
- Severity: Critical

### G04 — Conversion Values Assigned
- PASS: all primary conversions have value or value rules
- WARNING: some lacking values — ROAS bidding unreliable
- Severity: High (ROAS) / Medium (CPA)

### G05 — Enhanced Conversions for Web (EC4W)
- PASS: active on purchase events | FAIL: losing 15–30% post-cookie data
- Severity: High (e-com) / Medium (lead gen)

### G06 — Enhanced Conversions for Leads (EC4L)
- PASS: EC4L active — hashed email/phone matched to Google sign-in
- FAIL: lead gen without EC4L — bidding optimizes for form fills, not revenue
- Severity: Critical for lead gen accounts

### G07 — Offline Conversion Import (OCI)
- PASS: CRM-qualified leads / closed deals imported back to Google Ads
- WARNING: not configured — bidding optimizes for form fills not revenue
- Severity: High for B2B and high-ticket

### G08 — Consent Mode v2 (EU/EEA Accounts)
- PASS: ad_storage, analytics_storage, ad_user_data, ad_personalization all managed
- FAIL: EU account without Consent Mode — violates DMA, guaranteed data loss
- Severity: Critical EU / Not applicable US-only

### G09 — Attribution Model: Data-Driven
- PASS: data-driven on all primary conversions
- WARNING: last-click still active — credit misattributed, budgets skewed
- Severity: Medium

### G10 — Conversion Window Appropriate for Sales Cycle
- PASS: window matches cycle (30d lead gen, 90d e-commerce)
- WARNING: 7-day window on 60-day sales cycle — missing late conversions
- Severity: Medium

### G11 — Conversion Lag Analysis
- CHECK: pull conversion delay report — conversions still trickling 14+ days out?
- FAIL: window too short = smart bidding under-reports recent performance
- Severity: Medium

### G12 — GA4 Linked and Importing Conversions
- PASS: GA4 linked, key conversions imported as Google Ads goals
- FAIL: losing cross-channel attribution, audience data
- Severity: High

### G13 — Server-Side Tagging via GTM SS
- PASS: GTM server container active, first-party proxying enabled
- WARNING: client-side only — ad blockers causing 10–20% data loss
- Severity: Medium

### G14 — No Duplicate Conversion Actions
- PASS: each conversion counted once | FAIL: double-counting inflates numbers
- Severity: Critical

### G15 — Conversion Status: Active
- PASS: all primary conversions show "Recording conversions"
- FAIL: inactive tracking = bidding against nothing
- Severity: Critical

### G16 — Remarketing Lists Populated (RLSA)
- PASS: website visitor lists ≥1,000 users
- WARNING: lists exist but <100 users — RLSA signals useless
- Severity: Medium

---

## CATEGORY 2: Wasted Spend (20%)

### G17 — Search Terms Report Reviewed (Last 30 Days)
- PASS: evidence of recent STR review, new negatives added
- FAIL: no new negatives added in 60+ days
- Severity: High

### G18 — Negative Keyword Lists Implemented
- PASS: shared list + campaign-level negatives
- FAIL: zero negatives — typically 20–40% wasted spend
- Severity: Critical

### G19 — Brand vs Non-Brand Separated
- PASS: dedicated brand campaign | FAIL: brand terms mixed with non-brand
- Severity: High

### G20 — Competitor Brand Bidding Evaluated
- CHECK: bidding on competitor terms without comparison landing page?
- Severity: Medium

### G21 — Broad Match ONLY with Smart Bidding ⚠ HARD RULE
- PASS: Broad + tCPA or tROAS | FAIL: Broad + Manual CPC = disaster
- Severity: Critical. NEVER recommend Broad Match without Smart Bidding.

### G22 — Low-Performing Keywords Paused
- PASS: keywords with ≥$50 spend, 0 conversions in 90 days paused
- FAIL: zombie keywords draining budget. Calculate: sum their cost = wasted spend.
- Severity: High

### G23 — Display Network Opt-Out on Search Campaigns
- PASS: "Search with Display Select" not enabled | FAIL: 60–80% Display budget wasted
- Severity: High

### G24 — Display Placement Exclusions Active
- PASS: mobile apps, parked domains, game apps excluded
- WARNING: no placement exclusions — budget leaking
- Severity: Medium

### G25 — Search Partners Reviewed
- PASS: segmented, performing or excluded
- WARNING: included with no review in 90 days
- Severity: Low

### G26 — Geographic Targeting Precision
- PASS: only relevant service areas | FAIL: "All countries" for local/national business
- Severity: High

### G27 — Location: "Presence" Only ⚠ Most Overlooked Setting
- PASS: "People in or regularly in your targeted locations"
- FAIL: "Presence or Interest" — ads shown to people interested in location but NOT there
- Severity: High

### G28 — Ad Schedule Based on Conversion Data
- PASS: schedule from conversion data by hour/day
- WARNING: 24/7 including 2–6am with no conversion history
- Severity: Medium

### G29 — Invalid Click Rate Within Norms
- PASS: <5% | WARNING: 5–10% | FAIL: >10% — implement IP exclusion/ClickCease
- Severity: High above 10%

### G30 — PMax URL Expansion Exclusions Set
- PASS: privacy policy, login, careers excluded | FAIL: PMax crawling irrelevant pages
- Severity: Medium (PMax only)

### G31 — Budget Sufficiency Check
- PASS: no "Limited by budget" badges | FAIL: calculate IS Lost to Budget × potential
- Formula: Budget needed = Current spend / (1 - IS_lost_to_budget)
- Severity: High

---

## CATEGORY 3: Account Structure (15%)

### G32 — Campaign Hierarchy Follows Business Logic
- Severity: Medium

### G33 — Ad Groups Tightly Themed (≤20 Keywords)
- FAIL: 100+ keywords/group — ad relevance suffers, QS drops
- Severity: High

### G34 — SKAGs Evaluated for Migration
- WARNING: SKAGs without exact match only = unnecessary fragmentation in 2026
- Severity: Low

### G35 — PMax: Separate Asset Groups per Product/Category
- FAIL: single mixed asset group — attribution broken
- Severity: High (PMax)

### G36 — PMax: Sufficient Assets per Asset Group
- PASS: ≥5 images, ≥5 headlines, ≥5 descriptions, ≥1 video
- WARNING: minimal assets — Google generates low-quality auto assets
- Severity: Medium (PMax)

### G37 — PMax: Audience Signals Configured
- PASS: custom segments, customer lists, in-market added
- FAIL: no signals — PMax burns learning budget
- Severity: High (PMax)

### G38 — PMax: Brand Exclusions Applied
- FAIL: PMax stealing brand traffic, inflating PMax attribution
- Severity: High (PMax)

### G39 — PMax: Search Themes Set
- WARNING: not set — PMax has no keyword guidance
- Severity: Medium (PMax)

### G40 — Shopping Feed Quality (E-commerce)
- PASS: Merchant Center active, feed errors <5%, approvals >95%
- FAIL: feed errors preventing products from serving
- Severity: Critical (e-com)

### G41 — Campaign Naming Convention Consistent
- Format: [Platform]_[Type]_[Audience]_[Geo]_[Date]
- Severity: Low

### G42 — No Duplicate Campaigns on Same Traffic
- FAIL: identical campaigns competing — raises CPC
- Severity: High

### G43 — Google Merchant Center Linked (E-commerce)
- Severity: Critical (e-com)

---

## CATEGORY 4: Keywords & Quality Score (15%)

| Metric | PASS | WARNING | FAIL |
|---|---|---|---|
| Avg Quality Score | ≥7 | 5–6 | <5 |
| CTR (Search) | ≥6.66% | 3–6.66% | <3% |
| CVR (Search) | ≥7.52% | 3–7.52% | <3% |

### G44 — G55 Keyword Health Matrix
For each check: G44=Avg QS ≥7, G45=Ad Relevance Above Avg, G46=Landing Page Above Avg,
G47=Expected CTR Avg+, G48=Match Type Strategy, G49=No Cannibalization, G50=IS Tracked,
G51=Search Term Expansion Reviewed, G52=Long-Tail Coverage, G53=Device Bid Adjustments,
G54=Location Bid Adjustments, G55=RLSA Bid Adjustments

---

## CATEGORY 5: Ads & Assets (15%)

### G56–G67 Checklist
- G56: RSA in every ad group (Critical if missing)
- G57: ≥8 headlines, ≥3 descriptions per RSA (High)
- G58: Ad Strength Good or Excellent (High=Poor, Medium=Average)
- G59: Pin usage minimal — FAIL if majority pinned (High)
- G60: ≥4 sitelinks with descriptions (Medium)
- G61: ≥4 callout extensions (Medium)
- G62: Structured snippets active (Low)
- G63: ≥3 image extensions (Medium — major CTR impact mobile)
- G64: Lead form extensions for lead gen accounts (Medium)
- G65: Call extensions + call reporting for local/service (High)
- G66: DKI used appropriately with fallback text (Low)
- G67: Ad copy has CTA + value prop + differentiator (Medium)

---

## CATEGORY 6: Campaign Settings (10%)

### G68 — Bid Strategy Matches Maturity
- Decision Tree: Maximize Clicks → Maximize Conversions → tCPA/tROAS
- PASS: Smart Bidding on ≥30 conv/month campaigns
- FAIL: Smart Bidding on <30 conv/month — insufficient data
- Severity: High

### G69 — Target CPA/ROAS Realistic
- PASS: within ±20% of 90-day historical average
- FAIL: 50% below historical — Google throttles traffic to near-zero
- Severity: High

### G70–G74 Settings Checks
- G70: Portfolio bidding for shared goals (Low)
- G71: AI Max for Search evaluated (Medium — 2026 feature, can shift spend)
- G72: Language targeting appropriate (Medium)
- G73: Demographic bid adjustments (Low)
- G74: No campaigns limited by budget (High)

---

## Wasted Spend Estimation

```
Wasted Spend =
  + Sum of zombie keyword costs (≥$50 spend, 0 conv, 90 days)
  + 20% of Display budget if no placement exclusions
  + Broad Match spend without Smart Bidding (100% of this = waste)
```
Report as: **Estimated Wasted Spend: $X/month**

---

## Output Format

```json
{
  "agent": "Shiva",
  "platform": "google_ads",
  "health_score": 72,
  "grade": "C",
  "wasted_spend_estimate_monthly": 1840,
  "category_scores": {
    "conversion_tracking": 85,
    "wasted_spend": 55,
    "account_structure": 78,
    "keywords": 70,
    "ads_assets": 80,
    "settings": 90
  },
  "findings": [...],
  "quick_wins": [...]
}
```
