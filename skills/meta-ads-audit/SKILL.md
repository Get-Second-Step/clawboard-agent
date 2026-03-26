---
name: meta-ads-audit
description: >
  Meta Ads deep audit — 46 checks, 4 weighted categories. Agent name: BRAHMA
  (Creator of audiences, creative strategies, and campaign structures).
  EMQ ≥8.0 target, Advantage+ assessment, creative fatigue detection.
agent_name: Brahma
agent_role: Meta Ads Creator of Audiences & Creative
agent_avatar: 🌸
---

# BRAHMA — Meta Ads Audit (46-Point Deep Analysis)

> *"Brahma creates — audiences, creatives, structures. What Brahma doesn't build correctly, wastes budget."*

## Scoring Weights

| Category | Weight | Checks |
|---|---|---|
| Pixel / CAPI Health | 30% | M01–M14 |
| Creative Quality | 30% | M15–M26 |
| Account Structure | 20% | M27–M37 |
| Audience & Targeting | 20% | M38–M46 |

## Health Score Formula

```
Category_Score = 100 - (critical×15) - (high×8) - (medium×4) - (low×2)
Meta_Health_Score =
  (Pixel × 0.30) + (Creative × 0.30) + (Structure × 0.20) + (Audience × 0.20)
Score = max(0, min(100, Score))
```

---

## CATEGORY 1: Pixel / CAPI Health (30%)

### M01 — Meta Pixel Installed on All Pages
- PASS: pixel fires on every page, PageView confirmed in Events Manager
- FAIL: missing on key pages (product pages, thank-you page)
- Severity: Critical

### M02 — All Standard Events Configured
- PASS: ViewContent, AddToCart, InitiateCheckout, Purchase, Lead (as applicable)
- FAIL: missing Purchase or Lead event — conversion optimization impossible
- Severity: Critical

### M03 — Conversions API (CAPI) Active
- PASS: CAPI implemented server-side (Meta partner, direct, or GTM SS)
- FAIL: browser-only pixel — 30–40% data loss post-iOS 14.5 guaranteed
- Severity: Critical

### M04 — Event Deduplication Configured
- PASS: event_id sent via both browser Pixel and CAPI, matching correctly, dedup rate ≥90%
- WARNING: dedup rate 70–90% — some double-counting
- FAIL: dedup rate <70% — overcounting conversions
- Severity: Critical

### M05 — Event Match Quality (EMQ) for Purchase: ≥8.0
- PASS: ≥8.0 (Excellent) | WARNING: 6.0–7.9 (Good) | FAIL: <6.0 (Poor)
- EMQ Improvement: add em (email), ph (phone), fn+ln (name), ct+st+zp (address), external_id
- Note: Target is ≥8.0, not the outdated ≥6.0 threshold
- Severity: Critical below 6.0, High at 6.0–7.9

### M06 — EMQ for Lead Event: ≥7.0
- Same parameters as M05 but for lead generation accounts
- Severity: High

### M07 — CAPI Sends Customer Information Parameters
- PASS: em, ph, fn, ln, ct, st, zp, external_id included in server events
- FAIL: CAPI sending event names only with no user data — EMQ will be near zero
- Severity: Critical

### M08 — Aggregated Event Measurement (AEM) Configured
- PASS: domain verified, up to 8 prioritized conversion events set per domain
- FAIL: not configured — iOS campaign delivery broken
- Severity: High (accounts targeting iOS users)

### M09 — Domain Verification Completed
- PASS: business domain verified in Business Manager
- FAIL: pixel-domain mismatch — tracking unreliable
- Severity: High

### M10 — No Pixel Duplication (No Double-Firing)
- PASS: single pixel firing per page | FAIL: duplicate pixels inflate all metrics
- Severity: Critical

### M11 — Custom Conversions for Non-Standard Events
- PASS: custom conversions created for events not covered by standard events
- WARNING: using standard events for non-standard actions (e.g., "Purchase" for a lead)
- Severity: Medium

### M12 — Test Events Tool Verified
- PASS: Events Manager test tool shows clean event firing
- WARNING: not tested recently — may have silent pixel breakage
- Severity: Medium

### M13 — Server-Side CAPI via GTM or Direct Integration
- PASS: GTM server container or direct API integration
- WARNING: using Meta's Conversions API Gateway only — less flexible
- Severity: Low

### M14 — Value and Currency Parameters in Purchase Events
- PASS: value and currency fields populated on Purchase event
- FAIL: missing value = ROAS bidding is guessing, value optimization impossible
- Severity: High (e-commerce)

---

## CATEGORY 2: Creative Quality (30%)

### M15 — Creative Format Diversity: ≥3 Formats Active
- PASS: mix of image, video, carousel, collection (≥3 types)
- WARNING: only 2 formats | FAIL: single format (image only or video only)
- Severity: High — Meta's algorithm needs variety to optimize

### M16 — ≥5 Creatives Per Ad Set
- PASS: ≥5 active ads per ad set (Meta recommendation)
- WARNING: 3–4 | FAIL: <3 — algorithm can't optimize delivery
- Severity: High

### M17 — Creative Fatigue Detection: CTR Trend
- PASS: CTR stable or improving over last 14 days
- FAIL: CTR dropped >20% over 14 days = fatigue — rotate creative immediately
- Check: frequency × reach × time. Fatigue = frequency >3.5 + declining CTR
- Severity: High when triggered

### M18 — Prospecting Frequency (7-day): <3.0
- PASS: <3.0 | WARNING: 3.0–5.0 | FAIL: >5.0 (audience exhausted)
- Severity: High above 5.0

### M19 — Retargeting Frequency (7-day): <8.0
- PASS: <8.0 | WARNING: 8.0–12.0 | FAIL: >12.0 (annoying users)
- Severity: High above 12.0

### M20 — Video Creative: Proper Length
- PASS: 15s max for Stories/Reels, 30s max for Feed
- FAIL: 90-second video in Stories placement — will be cut off
- Severity: Medium

### M21 — Video Has Captions/Subtitles
- PASS: captions present | FAIL: silent-assumption — 85% of Facebook video watched muted
- Severity: Medium

### M22 — UGC/Testimonial Creative Tested
- PASS: at least 1 UGC-style ad tested alongside polished brand creative
- WARNING: only polished creative — missing highest-performing format
- Severity: Medium

### M23 — Dynamic Creative Optimization (DCO) Tested
- PASS: DCO tested on top ad sets to find winning asset combinations
- WARNING: never tested — missing automated optimization opportunity
- Severity: Low

### M24 — Ad Copy Length Optimized
- PASS: headline <40 chars, primary text <125 chars (above-fold visibility)
- WARNING: headline >40 chars gets truncated in most placements
- Severity: Medium

### M25 — Creative Refresh Cadence: Every 2–4 Weeks (High Spend)
- PASS: new creatives introduced every 2–4 weeks on high-spend ad sets
- FAIL: same creative running 90+ days with no refresh
- Severity: High (accounts spending >$1k/month per ad set)

### M26 — Advantage+ Creative Enhancements Evaluated
- PASS: Advantage+ creative enhancements (brightness adjustment, music, text optimization) reviewed
- WARNING: never checked which enhancements Meta is applying automatically
- Severity: Low

---

## CATEGORY 3: Account Structure (20%)

### M27 — Campaign Naming Convention Consistent
- Format: [Objective]_[Audience]_[Geo]_[Date] e.g., CONV_Prospecting_US_2026Q1
- Severity: Low

### M28 — Campaign Consolidation: ≤5 Active Campaigns Per Objective
- PASS: ≤5 | WARNING: 6–10 | FAIL: >10 — fragmented budget, all in learning
- Severity: High

### M29 — Learning Phase Health: <30% Ad Sets in Learning Limited
- PASS: <30% | WARNING: 30–50% | FAIL: >50%
- Causes: budget too low, too many edits, audience too small
- Severity: High

### M30 — Budget Per Ad Set: ≥5x Target CPA
- PASS: ≥5x CPA | WARNING: 2–5x | FAIL: <2x — can never exit learning phase
- Example: $50 CPA target = $250/day minimum per ad set
- Severity: Critical when <2x

### M31 — CBO vs ABO Strategy Intentional
- PASS: CBO on proven campaigns, ABO for testing (clear rationale)
- WARNING: using ABO only — missing algorithm's budget optimization
- Severity: Medium

### M32 — Ad Set Audience Overlap <30%
- PASS: <30% overlap between ad sets (use Audience Overlap tool)
- FAIL: >50% overlap — ad sets competing in same auction, CPMs inflated
- Severity: High

### M33 — Advantage+ Shopping Campaigns (ASC) Active (E-commerce)
- PASS: ASC tested with budget allocation and existing customer cap set
- WARNING: not tested — potentially leaving significant efficiency gains
- Severity: Medium (e-commerce only)

### M34 — Advantage+ Audience vs Manual Compared
- PASS: A/B test run, winner identified and scaled
- WARNING: never compared — may be over-restricting Meta's algorithm
- Severity: Medium

### M35 — Learning Phase: No Significant Edits During Learning
- PASS: no edits to budget/bid/audience during learning phase (7-day window)
- FAIL: edits made, campaign reset to learning — budget wasted
- Severity: High

### M36 — Attribution Window: 7-Day Click / 1-Day View (Default Correct)
- PASS: 7-day click / 1-day view | FAIL: 1-day click only — undercounting conversions
- Severity: Medium

### M37 — Special Ad Categories Declared
- PASS: Housing, Employment, Credit, Finance categories declared if applicable
- FAIL: running restricted ads without declaring category — account ban risk
- Severity: Critical (if applicable)

---

## CATEGORY 4: Audience & Targeting (20%)

### M38 — Custom Audiences: Website Visitors Segmented
- PASS: 7d, 30d, 90d, 180d visitors as separate audiences
- FAIL: single "all website visitors" audience — no recency segmentation
- Severity: High

### M39 — Customer List Uploaded and Matched
- PASS: CRM list uploaded, match rate >20%
- WARNING: no CRM list — missing highest-intent audience
- Severity: High

### M40 — Lookalike Audiences: Multiple Sizes Tested
- PASS: 1%, 3%, 5% lookalikes from best seed audience (purchasers, LTV)
- WARNING: single 1% LAL only | FAIL: no lookalikes
- Severity: Medium

### M41 — Advantage+ Audience Tested
- PASS: tested vs manual targeting, winner identified
- WARNING: never tested — potential for significant efficiency gain
- Severity: Medium

### M42 — Purchasers Excluded from Prospecting
- PASS: recent purchasers excluded from top-of-funnel campaigns
- FAIL: showing acquisition ads to existing customers — wasted spend
- Severity: High

### M43 — Retargeting Audiences Properly Segmented
- PASS: separate retargeting for: website visitors, video viewers, page engagers, cart abandoners
- WARNING: single "all retargeting" audience — can't optimize per segment
- Severity: Medium

### M44 — Interest Targeting: Broad Enough for Algorithm
- PASS: audience ≥500k for algorithm to optimize within
- FAIL: audience <100k — too narrow, Meta can't optimize delivery
- Severity: High

### M45 — Advantage+ Placements Enabled
- PASS: all placements enabled (Feed, Stories, Reels, Marketplace, etc.)
- WARNING: manually restricted to 2–3 placements — limiting optimization
- Severity: Medium

### M46 — Location Targeting Reviewed for Relevance
- PASS: only serving in countries/cities where business operates
- FAIL: worldwide targeting for a local business
- Severity: High

---

## EMQ Optimization Guide

| EMQ | Status | Priority Action |
|---|---|---|
| 8.0–10.0 | Excellent | Maintain setup |
| 6.0–7.9 | Good | Add more customer_information params |
| 4.0–5.9 | Fair | Implement CAPI + improve data quality |
| <4.0 | Poor | Critical: CAPI required immediately |

**Key parameters to maximize EMQ (ranked by impact):**
1. `em` (hashed email) — highest match signal
2. `ph` (hashed phone) — second highest
3. `fn` + `ln` (first/last name)
4. `ct` + `st` + `zp` (city, state, ZIP)
5. `external_id` (CRM/user ID)

---

## Key Benchmarks

| Metric | Pass | Warning | Fail |
|---|---|---|---|
| EMQ (Purchase) | ≥8.0 | 6.0–7.9 | <6.0 |
| Dedup Rate | ≥90% | 70–90% | <70% |
| CTR (Feed) | ≥1.0% | 0.5–1.0% | <0.5% |
| Creative Formats | ≥3 | 2 | 1 |
| Creatives/Ad Set | ≥5 | 3–4 | <3 |
| Learning Limited | <30% | 30–50% | >50% |
| Budget/Ad Set | ≥5x CPA | 2–5x CPA | <2x CPA |
| Prospecting Frequency | <3.0 | 3.0–5.0 | >5.0 |

---

## Output Format

```json
{
  "agent": "Brahma",
  "platform": "meta_ads",
  "health_score": 71,
  "grade": "C",
  "category_scores": {
    "pixel_capi": 60,
    "creative": 75,
    "structure": 80,
    "audience": 70
  },
  "emq_scores": {
    "purchase": 5.2,
    "lead": 6.1
  },
  "creative_fatigue_alerts": ["Creative ID 123 — CTR dropped 32% in 14 days"],
  "findings": [...],
  "quick_wins": [...]
}
```
