---
name: meta-ads-audit
description: Use this skill when auditing a Meta Ads (Facebook/Instagram) account. Runs 46 checks across 7 categories.
---

# Meta Ads Audit Skill

## When to Use
When the user asks to audit a Meta Ads account, or when the main audit agent delegates Meta Ads analysis.

## 46-Point Audit Checklist

### 1. Pixel & Tracking Health (7 checks)
- [ ] Meta Pixel correctly installed on all pages
- [ ] PageView event firing on every page load
- [ ] Standard events configured (ViewContent, AddToCart, Purchase, Lead)
- [ ] Event Match Quality (EMQ) score ≥ 6.0 for key events
- [ ] Pixel not duplicated (no double-firing)
- [ ] Domain verification completed
- [ ] Aggregated Event Measurement configured (iOS 14.5+)

### 2. Conversions API (CAPI) Health (6 checks)
- [ ] CAPI implemented (server-side tracking active)
- [ ] CAPI events match browser Pixel events (deduplication working)
- [ ] Event deduplication IDs properly configured
- [ ] CAPI sending user data parameters (email, phone, IP, UA)
- [ ] CAPI event quality score rated "Good" or "Great"
- [ ] Server events visible in Events Manager test tool

### 3. Campaign Structure (7 checks)
- [ ] Campaign naming convention followed (Brand_Objective_Audience_Date)
- [ ] Campaign objectives aligned with business goals
- [ ] Campaign Budget Optimization (CBO) enabled where appropriate
- [ ] Not more than 3-5 active campaigns per objective
- [ ] Ad set organization logical (audience-based separation)
- [ ] Ad variant A/B testing active (≥3 ads per ad set)
- [ ] Advantage+ campaigns tested for e-commerce

### 4. Audience Targeting (7 checks)
- [ ] Custom audiences created from CRM/website data
- [ ] Lookalike audiences tested (1%, 3%, 5% tiers)
- [ ] Retargeting audiences segmented (7d, 30d, 90d)
- [ ] Exclusion audiences preventing ad fatigue
- [ ] Audience overlap < 20% between ad sets
- [ ] Broad targeting tested with Advantage+ optimization
- [ ] Detailed targeting expansion reviewed

### 5. Creative Performance (8 checks)
- [ ] Creative diversity: mix of image, video, carousel formats
- [ ] Video creative includes captions/subtitles
- [ ] Image specs followed (1:1 for feed, 9:16 for Stories/Reels)
- [ ] Creative refresh cycle < 4 weeks (fighting fatigue)
- [ ] Frequency < 3.0 per week per ad set
- [ ] CTR > 1% for link click campaigns
- [ ] Thumb-stop rate tracked for video ads
- [ ] UGC-style creative tested alongside polished creative

### 6. Learning Phase Management (5 checks)
- [ ] Budget sufficient to exit learning phase (50 conversions/week)
- [ ] Not making significant edits during learning phase
- [ ] Conversion window appropriate (7-day click, 1-day view default)
- [ ] Bid strategy matches volume requirements
- [ ] Ad sets not stuck in "Learning Limited"

### 7. Budget & Efficiency (6 checks)
- [ ] ROAS/CPA targets set and monitored
- [ ] Budget pacing even throughout the day
- [ ] High-performing ad sets receiving adequate budget
- [ ] Spend not concentrated on single creative
- [ ] Cost per result trending stable or improving
- [ ] Attribution window appropriate for product/service

## Scoring Formula

```
score = 100 - (critical_count × 15) - (high_count × 8) - (medium_count × 4) - (low_count × 2)
score = max(0, min(100, score))
```

## Output Format

Return findings as JSON:
```json
{
  "platform": "meta_ads",
  "score": 68,
  "findings": [
    {
      "id": "MA-001",
      "category": "pixel_health",
      "title": "Event Match Quality Below Threshold",
      "severity": "high",
      "description": "EMQ score for Purchase event is 4.2 (target ≥ 6.0)...",
      "action": "Add more customer information parameters to Pixel events...",
      "effort": "3-4 hours",
      "impact": "high"
    }
  ]
}
```
