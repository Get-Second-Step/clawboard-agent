---
name: budget-bidding
description: >
  Budget allocation and bidding strategy audit. Agent name: ARJUNA (The precise
  archer — hits the right target with the right bid). Reviews spend distribution,
  bidding strategy maturity, learning phase health, and scaling rules.
agent_name: Arjuna
agent_role: Budget & Bidding Precision
agent_avatar: 🏹
---

# ARJUNA — Budget & Bidding Audit

> *"Arjuna never wastes an arrow — every dollar hits its target."*

## When to Invoke
- Budget allocation review across multiple platforms
- Bidding strategy needs evaluation
- Campaigns stuck in learning phase
- Scaling decisions needed
- CPA/ROAS targets under/over-performing

---

## Bidding Strategy Decision Tree

### Google Ads
```
New account / New campaign (0 conversions)
  → Maximize Clicks (build traffic, gather data)
  → When ≥30 conversions/month: Maximize Conversions
  → When ≥50 conversions/month + stable CPA: Target CPA
  → When revenue data available + ≥50 conv: Target ROAS

Existing account with data:
  → <30 conv/month: Manual CPC or Maximize Clicks (smart bidding unreliable)
  → 30–50 conv/month: Maximize Conversions (with CPA cap optional)
  → 50+ conv/month: tCPA or tROAS (most efficient)
  → Portfolio tCPA: when multiple campaigns share same CPA goal
```

### Meta Ads
```
New campaign:
  → Lowest Cost (no bid cap) — let Meta find conversions
  → Once ≥50 events/week: Cost Cap (stabilize CPA)
  → Once stable: Bid Cap (control max auction bid)
  → For e-commerce: Highest Value (maximize purchase value)
  → For ASC: Advantage Shopping (let Meta fully automate)
```

### LinkedIn Ads
```
Always start with:
  → Maximum Delivery (LinkedIn's equivalent of Lowest Cost)
  → After 30+ conversions: Target Cost CPA
  → For awareness: CPM with frequency cap
Note: LinkedIn CPCs are expensive ($5–$20). Start with Max Delivery.
```

### TikTok Ads
```
→ Start: Lowest Cost (Bid)
→ After 50+ conversions: Cost Cap
→ Smart+: when you want full automation (like Meta Advantage+)
→ Budget: need ≥50x CPA per ad group minimum for Smart Bidding
```

---

## Budget Sufficiency Rules

### Hard Rules
- **Google**: campaign needs ≥10x target CPA/day to exit learning phase
- **Meta**: ad set needs ≥5x target CPA/day minimum. For 50 events/week needed: budget = (CPA × 50) ÷ 7
- **TikTok**: ad group needs ≥50x CPA to run Smart Bidding effectively
- **LinkedIn**: minimum $10/day per campaign, effective minimum $50/day

### Learning Phase Exit Requirements
| Platform | Conversion Threshold | Timeframe |
|---|---|---|
| Google | 30 conversions | Per month per campaign |
| Meta | 50 conversion events | Per week per ad set |
| TikTok | 50 conversions | Per week per ad group |
| LinkedIn | 30 conversions | Per month |

**If threshold can't be met:** use higher-funnel conversion event (e.g., AddToCart instead of Purchase) to accumulate volume.

---

## The 3x Kill Rule ⚠ Never Violate

> Flag any campaign, ad set, or creative with CPA >3x target for pause.

- CPA target $50 → pause anything spending toward $150+ CPA
- Exception: campaigns within first 7 days of launch (learning phase grace period)
- Exception: brand campaigns (brand CPA benchmarks differ from non-brand)

---

## Budget Scaling Rules

### Safe Scaling Protocol
- Increase budget by ≤20% per week on winning campaigns
- Larger increases trigger learning phase reset (wastes 7–14 days of learning)
- For Meta: CBO budget changes reset learning; prefer changing bids over budget for minor adjustments
- For Google: budget increases don't reset Smart Bidding learning (safe to scale)

### When to Scale
- ROAS consistently ≥ target for 14+ days
- Learning phase exited, performance stable
- No budget-limited campaigns (allocate available budget to winners first)

### When NOT to Scale
- During learning phase
- CPA trending upward (audience saturation signal)
- Creative fatigue detected (scale will accelerate deterioration)
- Major platform algorithm change in last 7 days

---

## Platform Budget Allocation Audit Checks

### A01 — 70/20/10 Framework Applied
- PASS: 70% proven, 20% scaling, 10% testing
- WARNING: 100% in one campaign with no testing
- Severity: Medium

### A02 — No Single Campaign Over 60% of Total Budget
- PASS: diversified allocation
- FAIL: >60% in one campaign = over-dependence, catastrophic if that campaign breaks
- Severity: Medium

### A03 — Brand Campaign Always Funded
- PASS: brand campaign running at all times (cheapest conversions available)
- FAIL: brand campaign paused — competitors stealing branded traffic
- Severity: High

### A04 — Retargeting Getting Budget (10–20% Minimum)
- PASS: retargeting receiving adequate budget (highest CVR, cheapest CPA)
- FAIL: 100% prospecting, no retargeting — leaving cheapest conversions on table
- Severity: High

### A05 — Budget Pacing: No End-of-Month Underspend/Overspend
- PASS: even pacing, within 10% of target spend
- FAIL: spending 80% of budget in last week = reactive, not strategic
- Severity: Medium

### A06 — Smart Bidding Not Applied on Insufficient Data
- FAIL: tCPA or tROAS on campaigns with <30 conv/month
- This causes erratic bidding, CPA spikes, and poor delivery
- Severity: Critical

### A07 — Target CPA/ROAS Realistic (Within ±20% of Historical)
- PASS: target based on 90-day actual average
- FAIL: target 50% below actual = Google throttles to near-zero traffic
- Severity: High

### A08 — Portfolio Bidding for Shared Goals
- PASS: multiple campaigns with same tCPA share portfolio strategy
- WARNING: individual campaign targets when portfolio would be more efficient
- Severity: Low

### A09 — Budget Not Concentrated on Single Creative
- PASS: Meta budget distributed across ≥3 active creatives
- FAIL: 80%+ of spend on 1 creative — accelerates fatigue, no backup when it dies
- Severity: Medium (Meta/TikTok)

### A10 — Monthly Budget Review Completed
- PASS: performance vs target reviewed monthly, budget rebalanced
- WARNING: set-and-forget budgets — no optimization
- Severity: Medium

---

## Wasted Budget Signals

Quick calculations to run:

```
1. Learning Phase Waste:
   Ad sets in "Learning Limited" × daily budget × days stuck = $ wasted learning

2. Over-Capped Retargeting:
   If retargeting frequency >12/week → audience exhausted, budget wasting

3. Under-Invested Brand:
   Brand campaign CPA is typically 3–10x cheaper than non-brand
   If brand = <5% of budget → leaving cheapest conversions unfunded

4. Scaling Too Fast:
   Budget increase >20% in 7 days = learning phase reset = ~7-14 days inefficiency
```

---

## Output Format

```json
{
  "agent": "Arjuna",
  "output_type": "budget_bidding_audit",
  "total_monthly_budget": 15000,
  "budget_allocation": {
    "google_ads": {"budget": 10000, "share": "67%", "status": "proven"},
    "meta_ads": {"budget": 4000, "share": "27%", "status": "scaling"},
    "testing": {"budget": 1000, "share": "7%", "status": "testing"}
  },
  "bidding_audit": [
    {
      "id": "A06",
      "finding": "Google Search campaign using tCPA with only 12 conversions/month",
      "severity": "critical",
      "action": "Switch to Maximize Conversions until ≥30 conv/month",
      "estimated_impact": "Stabilize delivery, reduce CPA variance 40%"
    }
  ],
  "scaling_opportunities": [...],
  "budget_waste_estimate": "$X/month"
}
```
