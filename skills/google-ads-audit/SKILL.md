---
name: google-ads-audit
description: Use this skill when auditing a Google Ads account. Runs 46 checks across 8 categories.
---

# Google Ads Audit Skill

## When to Use
When the user asks to audit a Google Ads account, or when the main audit agent delegates Google Ads analysis.

## 46-Point Audit Checklist

### 1. Account Structure (6 checks)
- [ ] Account properly organized with logical campaign hierarchy
- [ ] Campaigns separated by match type or theme
- [ ] Ad groups contain tightly themed keywords (≤20 per group)
- [ ] Manager account linked if applicable
- [ ] Conversion tracking enabled at account level
- [ ] Auto-tagging enabled for Google Analytics

### 2. Campaign Settings (7 checks)
- [ ] Campaign type appropriate for business goals (Search, PMax, Display, Shopping)
- [ ] Campaign budget set and not limited (IS Lost to Budget < 10%)
- [ ] Ad schedule configured (not running 24/7 without reason)
- [ ] Location targeting set to "Presence" only (not "Presence or Interest")
- [ ] Language targeting appropriate for market
- [ ] Device bid adjustments reviewed and set
- [ ] Network settings reviewed (Search Partners, Display expansion off for Search)

### 3. Bidding Strategy (6 checks)
- [ ] Bidding strategy aligned with campaign goals
- [ ] Smart bidding configured with sufficient conversion data (≥30 conv/month)
- [ ] Target CPA or ROAS set and realistic
- [ ] Portfolio bidding used where appropriate
- [ ] Bid adjustments for devices reviewed
- [ ] Bid adjustments for locations reviewed

### 4. Quality Score (5 checks)
- [ ] Average Quality Score ≥ 7
- [ ] Keywords with QS < 5 identified and actioned
- [ ] Ad relevance rated "Above Average" for majority of keywords
- [ ] Landing page experience rated "Above Average"
- [ ] Expected CTR rated "Average" or better

### 5. Keywords (7 checks)
- [ ] Negative keyword lists implemented at campaign and account level
- [ ] Search term report reviewed (last 30 days)
- [ ] Keyword match types appropriate (not all broad without smart bidding)
- [ ] Low-performing keywords paused (high spend, zero conversions)
- [ ] Keyword organization logical (themed ad groups)
- [ ] Duplicate keywords across campaigns identified
- [ ] Keyword cannibalization checked

### 6. Ad Copy & Assets (6 checks)
- [ ] Responsive Search Ads with 15 headlines and 4 descriptions
- [ ] Ad copy includes primary keywords
- [ ] Unique value proposition in headlines
- [ ] Call-to-action in descriptions
- [ ] Sitelink extensions (≥4) added
- [ ] Callout, structured snippet, and image extensions added

### 7. Conversion Tracking (5 checks)
- [ ] Primary conversion actions defined and tracked
- [ ] Enhanced Conversions enabled (EC for Web or EC for Leads)
- [ ] Conversion values assigned (or value rules configured)
- [ ] Attribution model set to data-driven (not last-click)
- [ ] Conversion window appropriate for sales cycle

### 8. Budget & Spend Efficiency (4 checks)
- [ ] Budget sufficient to exit learning phase
- [ ] High-performing campaigns adequately funded
- [ ] Wasted spend identified (spend on non-converting keywords)
- [ ] Budget pacing reviewed (not consistently limited)

## Scoring Formula

```
score = 100 - (critical_count × 15) - (high_count × 8) - (medium_count × 4) - (low_count × 2)
score = max(0, min(100, score))
```

## Output Format

Return findings as JSON:
```json
{
  "platform": "google_ads",
  "score": 72,
  "findings": [
    {
      "id": "GA-001",
      "category": "conversion_tracking",
      "title": "Enhanced Conversions Not Enabled",
      "severity": "critical",
      "description": "Enhanced Conversions for Leads not configured...",
      "action": "Enable EC4L in Google Ads settings...",
      "effort": "1-2 hours",
      "impact": "high"
    }
  ]
}
```
