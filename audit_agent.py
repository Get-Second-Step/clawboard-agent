#!/usr/bin/env python3
"""
Performance Marketing Audit Agent — ClawBoard

A DeepAgents-powered audit agent that:
1. Plans audit tasks using write_todos
2. Delegates platform audits to specialized subagents (in parallel)
3. Aggregates findings and calculates scores
4. Generates branded PDF reports

Usage:
    # Basic audit (all platforms)
    uv run python audit_agent.py "Audit Example Client"

    # Specific platform
    uv run python audit_agent.py "Audit Example Client Google Ads only"

    # With Windsor.ai data
    WINDSOR_API_KEY=... uv run python audit_agent.py "Audit Example Client"
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

# Load credentials.env if present
from dotenv import load_dotenv
_env_path = Path(__file__).parent / "config" / "credentials.env"
if _env_path.exists():
    load_dotenv(_env_path)

import yaml
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

PROJECT_DIR = Path(__file__).parent
console = Console()

# ── Branding (configurable via credentials.env) ───────────────────────────────
AGENCY_NAME    = os.environ.get("AGENCY_NAME", "")
AGENCY_EMAIL   = os.environ.get("AGENCY_EMAIL", "")
AGENCY_WEBSITE = os.environ.get("AGENCY_WEBSITE", "")


# ──────────────────────────────────────────────
# NemoClaw Guard — wraps every LLM prompt/output
# ──────────────────────────────────────────────

_NEMOCLAW_URL = os.environ.get("NEMOCLAW_URL", "http://127.0.0.1:8080")
_nemoclaw_available: bool | None = None  # None = not yet probed


def _probe_nemoclaw() -> bool:
    """Check once whether NemoClaw is reachable."""
    global _nemoclaw_available
    if _nemoclaw_available is not None:
        return _nemoclaw_available
    try:
        import requests
        r = requests.get(f"{_NEMOCLAW_URL}/health", timeout=1)
        _nemoclaw_available = r.ok
    except Exception:
        _nemoclaw_available = False
    if not _nemoclaw_available:
        console.print("[dim]NemoClaw not reachable — running without guardrails[/dim]")
    return _nemoclaw_available


def guard_input(prompt: str, source: str = "audit_agent") -> str:
    """Pass prompt through NemoClaw input rail. Returns safe prompt or raises."""
    if not _probe_nemoclaw():
        return prompt
    try:
        import requests
        r = requests.post(
            f"{_NEMOCLAW_URL}/guard/input",
            json={"prompt": prompt, "source": source},
            timeout=5,
        )
        data = r.json()
        if not data.get("safe", True):
            raise ValueError(f"[NemoClaw] Blocked: {data.get('blocked_reason', 'unknown')}")
        return data.get("output", prompt)
    except ValueError:
        raise
    except Exception:
        return prompt  # fail open — audit must not break


def guard_output(output: str) -> str:
    """Pass LLM output through NemoClaw output rail before it reaches reports."""
    if not _probe_nemoclaw():
        return output
    try:
        import requests
        r = requests.post(
            f"{_NEMOCLAW_URL}/guard/output",
            json={"prompt": output, "source": "audit_agent"},
            timeout=5,
        )
        data = r.json()
        if not data.get("safe", True):
            console.print(f"[yellow][NemoClaw] Output sanitised: {data.get('blocked_reason')}[/yellow]")
            return "[Report section redacted by NemoClaw security layer]"
        return data.get("output", output)
    except Exception:
        return output  # fail open


# ──────────────────────────────────────────────
# Real API Helpers
# ──────────────────────────────────────────────

def _fetch_google_ads_real(account_id: str, date_range_days: int) -> dict:
    """Call real Google Ads API using google-ads Python client."""
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException

    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    login_cid = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    if login_cid:
        config["login_customer_id"] = login_cid

    client = GoogleAdsClient.load_from_dict(config)
    customer_id = account_id.replace("-", "")
    ga_service = client.get_service("GoogleAdsService")

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=date_range_days)
    date_range_str = f"'{start_date}' AND '{end_date}'"

    # ── Campaign performance query ──
    campaign_query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign.bidding_strategy_type,
            campaign_budget.amount_micros,
            campaign_budget.has_recommended_budget,
            campaign.target_cpa.target_cpa_micros,
            campaign.target_roas.target_roas,
            metrics.clicks,
            metrics.impressions,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversion_value,
            metrics.ctr,
            metrics.average_cpc
        FROM campaign
        WHERE segments.date BETWEEN {date_range_str}
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 20
    """

    # ── Account-level settings query ──
    account_query = """
        SELECT
            customer.id,
            customer.descriptive_name,
            customer.auto_tagging_enabled,
            customer.conversion_tracking_setting.conversion_tracking_id,
            customer.conversion_tracking_setting.cross_account_conversion_tracking_id
        FROM customer
        LIMIT 1
    """

    # ── Keyword stats query ──
    keyword_query = f"""
        SELECT
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.status,
            metrics.clicks,
            metrics.cost_micros
        FROM keyword_view
        WHERE segments.date BETWEEN {date_range_str}
          AND ad_group_criterion.status = 'ENABLED'
        LIMIT 500
    """

    try:
        # Fetch campaigns
        campaigns = []
        campaign_response = ga_service.search(customer_id=customer_id, query=campaign_query)
        channel_type_map = {
            "SEARCH": "SEARCH",
            "DISPLAY": "DISPLAY",
            "SHOPPING": "SHOPPING",
            "VIDEO": "VIDEO",
            "PERFORMANCE_MAX": "PERFORMANCE_MAX",
        }
        for row in campaign_response:
            c = row.campaign
            m = row.metrics
            b = row.campaign_budget
            campaigns.append({
                "id": str(c.id),
                "name": c.name,
                "status": c.status.name,
                "type": channel_type_map.get(c.advertising_channel_type.name, c.advertising_channel_type.name),
                "bidding_strategy": c.bidding_strategy_type.name,
                "budget": round(b.amount_micros / 1_000_000, 2),
                "budget_limited": b.has_recommended_budget,
                "target_cpa": round(c.target_cpa.target_cpa_micros / 1_000_000, 2) if c.target_cpa.target_cpa_micros else None,
                "target_roas": round(c.target_roas.target_roas * 100, 1) if c.target_roas.target_roas else None,
                "clicks": m.clicks,
                "impressions": m.impressions,
                "cost": round(m.cost_micros / 1_000_000, 2),
                "conversions": round(m.conversions, 1),
                "conversion_value": round(m.conversion_value, 2),
                "ctr": round(m.ctr * 100, 2),
                "avg_cpc": round(m.average_cpc / 1_000_000, 2),
            })

        # Fetch account settings
        account_data = {}
        acct_response = ga_service.search(customer_id=customer_id, query=account_query)
        for row in acct_response:
            cust = row.customer
            account_data = {
                "auto_tagging": cust.auto_tagging_enabled,
                "conversion_tracking_enabled": bool(cust.conversion_tracking_setting.conversion_tracking_id),
                "enhanced_conversions": False,  # fetched separately below
                "attribution_model": "last_click",
            }

        # Fetch keywords
        qs_scores = []
        total_keywords = 0
        low_qs = 0
        broad_count = 0
        kw_response = ga_service.search(customer_id=customer_id, query=keyword_query)
        for row in kw_response:
            total_keywords += 1
            qs = row.ad_group_criterion.quality_info.quality_score
            if qs:
                qs_scores.append(qs)
                if qs < 6:
                    low_qs += 1
            if row.ad_group_criterion.keyword.match_type.name == "BROAD":
                broad_count += 1

        keywords = {
            "total_active": total_keywords,
            "avg_quality_score": round(sum(qs_scores) / len(qs_scores), 1) if qs_scores else 0,
            "low_qs_keywords": low_qs,
            "negative_keyword_lists": 0,
            "broad_match_percentage": round((broad_count / total_keywords * 100) if total_keywords else 0, 1),
        }

        return {
            "account_id": account_id,
            "date_range": f"Last {date_range_days} days ({start_date} to {end_date})",
            "source": "google_ads_api",
            "account_level": account_data,
            "campaigns": campaigns,
            "keywords": keywords,
            "ads": {"total_active": 0, "note": "Ad-level data not fetched in this request"},
            "conversions": {"tracking_enabled": account_data.get("conversion_tracking_enabled", False)},
        }

    except GoogleAdsException as ex:
        errors = [e.message for e in ex.failure.errors]
        return {"error": f"GoogleAdsException: {'; '.join(errors)}"}


def send_telegram_report(report_paths: list[str], client_name: str, summary: str):
    """Send audit report PDF + summary to Telegram."""
    import requests as req
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return

    base = f"https://api.telegram.org/bot{token}"

    # Send text summary
    try:
        req.post(f"{base}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"✅ *Audit Complete — {client_name}*\n\n{summary}",
            "parse_mode": "Markdown",
        }, timeout=10)
    except Exception as e:
        console.print(f"  [yellow]⚠ Telegram message failed: {e}[/]")
        return

    # Send PDF file(s)
    for path_str in report_paths:
        pdf_path = Path(path_str.strip())
        if pdf_path.exists() and pdf_path.suffix == ".pdf":
            try:
                with open(pdf_path, "rb") as f:
                    req.post(f"{base}/sendDocument", files={"document": (pdf_path.name, f, "application/pdf")},
                             data={"chat_id": chat_id}, timeout=30)
                console.print(f"  [green]✓ PDF sent to Telegram: {pdf_path.name}[/]")
            except Exception as e:
                console.print(f"  [yellow]⚠ Telegram PDF upload failed: {e}[/]")


# ──────────────────────────────────────────────
# Custom Tools
# ──────────────────────────────────────────────

@tool
def fetch_google_ads_data(
    account_id: str = "",
    date_range_days: int = 90,
    metrics: str = "clicks,impressions,cost,conversions,conversion_value,ctr,avg_cpc,quality_score",
) -> dict:
    """Fetch Google Ads account data for auditing.

    Args:
        account_id: Google Ads customer ID (xxx-xxx-xxxx)
        date_range_days: Number of days to look back
        metrics: Comma-separated list of metrics to fetch

    Returns:
        Account data including campaigns, ad groups, keywords, and metrics.
    """
    # Try real Google Ads API if credentials are present
    dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    if all([dev_token, client_id, client_secret, refresh_token]):
        try:
            result = _fetch_google_ads_real(
                account_id or os.environ.get("GOOGLE_ADS_CUSTOMER_ID", ""),
                date_range_days,
            )
            if "error" not in result:
                return result
            console.print(f"  [yellow]⚠ Google Ads API: {result['error']} — using sample data[/]")
        except Exception as e:
            console.print(f"  [yellow]⚠ Google Ads API error: {e} — using sample data[/]")

    # If Windsor.ai API key is available, use it
    windsor_key = os.environ.get("WINDSOR_API_KEY")
    if windsor_key:
        try:
            import requests
            response = requests.get(
                "https://connectors.windsor.ai/google_ads",
                params={
                    "api_key": windsor_key,
                    "fields": metrics,
                    "date_preset": f"last_{date_range_days}_days",
                },
                timeout=30,
            )
            if response.ok:
                return response.json()
        except Exception as e:
            console.print(f"  [yellow]⚠ Windsor.ai fetch failed: {e} — using sample data[/]")

    # Sample data for testing/demo
    return {
        "account_id": account_id or "123-456-7890",
        "date_range": f"Last {date_range_days} days",
        "account_level": {
            "conversion_tracking_enabled": True,
            "auto_tagging": False,
            "enhanced_conversions": False,
            "attribution_model": "last_click",
        },
        "campaigns": [
            {
                "name": "Brand - Search",
                "type": "SEARCH",
                "status": "ENABLED",
                "budget": 50.0,
                "budget_limited": False,
                "bidding_strategy": "TARGET_CPA",
                "target_cpa": 25.0,
                "location_targeting": "presence_or_interest",
                "network": "search_with_partners",
                "clicks": 1250,
                "impressions": 15000,
                "cost": 1875.0,
                "conversions": 45,
                "ctr": 8.3,
                "avg_cpc": 1.50,
            },
            {
                "name": "Non-Brand - Search",
                "type": "SEARCH",
                "status": "ENABLED",
                "budget": 100.0,
                "budget_limited": True,
                "bidding_strategy": "MAXIMIZE_CONVERSIONS",
                "location_targeting": "presence_only",
                "network": "search_only",
                "clicks": 3200,
                "impressions": 45000,
                "cost": 6400.0,
                "conversions": 32,
                "ctr": 7.1,
                "avg_cpc": 2.00,
            },
            {
                "name": "PMax - All Products",
                "type": "PERFORMANCE_MAX",
                "status": "ENABLED",
                "budget": 75.0,
                "budget_limited": False,
                "bidding_strategy": "MAXIMIZE_CONVERSION_VALUE",
                "target_roas": 400,
                "clicks": 2100,
                "impressions": 120000,
                "cost": 2250.0,
                "conversions": 28,
                "conversion_value": 8400.0,
                "ctr": 1.75,
                "avg_cpc": 1.07,
            },
        ],
        "keywords": {
            "total_active": 156,
            "avg_quality_score": 6.2,
            "low_qs_keywords": 34,
            "negative_keyword_lists": 0,
            "broad_match_percentage": 65,
        },
        "ads": {
            "total_active": 12,
            "responsive_search_ads": 8,
            "avg_headlines_per_rsa": 10,
            "extensions": {
                "sitelinks": 4,
                "callouts": 3,
                "structured_snippets": 0,
                "image_extensions": 0,
            },
        },
        "conversions": {
            "tracking_enabled": True,
            "enhanced_conversions": False,
            "primary_actions": 2,
            "conversion_window": "30_days",
            "attribution": "last_click",
        },
    }


@tool
def fetch_meta_ads_data(
    account_id: str = "",
    date_range_days: int = 90,
) -> dict:
    """Fetch Meta Ads account data for auditing.

    Args:
        account_id: Meta Business Account ID
        date_range_days: Number of days to look back

    Returns:
        Account data including campaigns, pixel health, audiences, and creative performance.
    """
    windsor_key = os.environ.get("WINDSOR_API_KEY")
    if windsor_key:
        try:
            import requests
            response = requests.get(
                "https://connectors.windsor.ai/facebook",
                params={
                    "api_key": windsor_key,
                    "fields": "campaign,impressions,clicks,spend,conversions,cpc,ctr,roas",
                    "date_preset": f"last_{date_range_days}_days",
                },
                timeout=30,
            )
            if response.ok:
                return response.json()
        except Exception as e:
            return {"error": f"Windsor.ai fetch failed: {e}", "fallback": "using_sample_data"}

    # Sample data for testing
    return {
        "account_id": account_id or "act_123456789",
        "date_range": f"Last {date_range_days} days",
        "pixel": {
            "installed": True,
            "page_view_firing": True,
            "standard_events": ["PageView", "ViewContent", "AddToCart", "Lead"],
            "missing_events": ["Purchase", "CompleteRegistration"],
            "emq_scores": {"Lead": 5.2, "ViewContent": 7.1, "AddToCart": 4.8},
            "domain_verified": True,
            "aggregated_events_configured": False,
        },
        "capi": {
            "implemented": False,
            "deduplication": False,
            "user_data_params": [],
        },
        "campaigns": [
            {
                "name": "Prospecting - Broad",
                "objective": "CONVERSIONS",
                "status": "ACTIVE",
                "budget_type": "CBO",
                "daily_budget": 100.0,
                "spend": 8500.0,
                "conversions": 42,
                "cpa": 202.38,
                "ctr": 1.8,
                "frequency": 2.1,
                "learning_phase": "COMPLETED",
            },
            {
                "name": "Retargeting - Website Visitors",
                "objective": "CONVERSIONS",
                "status": "ACTIVE",
                "budget_type": "ABO",
                "daily_budget": 50.0,
                "spend": 4200.0,
                "conversions": 35,
                "cpa": 120.0,
                "ctr": 3.2,
                "frequency": 4.5,
                "learning_phase": "LEARNING_LIMITED",
            },
        ],
        "audiences": {
            "custom_audiences": 3,
            "lookalike_audiences": 1,
            "retargeting_segments": ["All visitors 30d"],
            "exclusions_configured": False,
            "audience_overlap": 35,
        },
        "creative": {
            "total_ads": 8,
            "formats": {"image": 5, "video": 2, "carousel": 1},
            "avg_creative_age_days": 45,
            "video_with_captions": 1,
            "ugc_creative": 0,
        },
    }


@tool
def fetch_analytics_data(
    property_id: str = "",
) -> dict:
    """Fetch Google Analytics 4 property data for auditing.

    Args:
        property_id: GA4 property ID

    Returns:
        Property configuration, events, conversions, and data quality metrics.
    """
    # Sample data for testing
    return {
        "property_id": property_id or "GA4-123456789",
        "implementation": {
            "ga4_active": True,
            "measurement_id": "G-XXXXXXXXXX",
            "data_stream": "web",
            "enhanced_measurement": True,
            "google_signals": False,
            "data_retention": "2_months",
        },
        "events": {
            "page_view": True,
            "scroll": True,
            "click": True,
            "form_submit": True,
            "purchase": False,
            "custom_events": ["contact_form", "download_brochure"],
            "duplicate_events_detected": False,
        },
        "conversions": {
            "marked_conversions": ["contact_form", "download_brochure"],
            "conversion_values": False,
            "attribution_model": "last_click",
            "cross_domain_tracking": False,
            "domains": ["example.com", "shop.example.com"],
        },
        "data_quality": {
            "internal_traffic_filtered": False,
            "bot_filtering": True,
            "utm_consistency": "partial",
            "referral_exclusions": [],
            "sampling_affected": False,
        },
        "integrations": {
            "google_ads_linked": True,
            "search_console_linked": False,
            "bigquery_export": False,
            "remarketing_audiences": 0,
        },
    }


@tool
def generate_audit_report(
    client_name: str,
    findings_json_path: str,
    output_format: Literal["html", "pdf", "both"] = "both",
) -> str:
    """Generate branded audit report from findings.

    Args:
        client_name: Client name for the report header
        findings_json_path: Path to aggregated findings JSON file
        output_format: Output format — "html", "pdf", or "both"

    Returns:
        Path(s) to generated report files.
    """
    import json

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    client_slug = client_name.lower().replace(" ", "_")

    # Read findings
    findings_path = PROJECT_DIR / findings_json_path
    if findings_path.exists():
        with open(findings_path) as f:
            findings = json.load(f)
    else:
        findings = {"error": "Findings file not found", "path": str(findings_path)}

    # Read CSS
    css_path = PROJECT_DIR / "branding" / "style.css"
    css = ""
    if css_path.exists():
        with open(css_path) as f:
            css = f.read()

    # Generate HTML
    html = _build_report_html(client_name, findings, css)

    html_path = PROJECT_DIR / "reports" / f"{client_slug}_audit_{timestamp}.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(html_path, "w") as f:
        f.write(html)

    result = f"HTML report saved: {html_path}"

    if output_format in ("pdf", "both"):
        pdf_path = PROJECT_DIR / "reports" / f"{client_slug}_audit_{timestamp}.pdf"
        chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if Path(chrome).exists():
            import subprocess
            subprocess.run(
                [chrome, "--headless", f"--print-to-pdf={pdf_path}",
                 "--no-margins", "--print-background", str(html_path)],
                capture_output=True, timeout=30,
            )
            result += f"\nPDF report saved: {pdf_path}"
        else:
            result += "\nPDF skipped: Chrome not found"

    return result


def _build_report_html(client_name: str, findings: dict, css: str) -> str:
    """Build the full HTML report."""
    audit_date = datetime.now().strftime("%B %d, %Y")
    platforms = findings.get("platforms", {})

    # Calculate overall score
    scores = []
    for platform_data in platforms.values():
        if isinstance(platform_data, dict) and "score" in platform_data:
            scores.append(platform_data["score"])
    overall_score = round(sum(scores) / len(scores)) if scores else 0

    # Count findings by severity
    all_findings = []
    for platform_data in platforms.values():
        if isinstance(platform_data, dict):
            all_findings.extend(platform_data.get("findings", []))

    critical = sum(1 for f in all_findings if f.get("severity") == "critical")
    high = sum(1 for f in all_findings if f.get("severity") == "high")

    # Score color
    if overall_score >= 75:
        score_color = "#4caf50"
    elif overall_score >= 50:
        score_color = "#ff9800"
    else:
        score_color = "#f44336"

    # Build platform sections
    platform_sections = ""
    for name, data in platforms.items():
        if not isinstance(data, dict):
            continue
        platform_sections += _build_platform_section(name, data)

    # Build action plan
    action_items = sorted(all_findings, key=lambda f: ["critical", "high", "medium", "low"].index(f.get("severity", "low")))
    action_plan = ""
    for i, item in enumerate(action_items[:10], 1):
        severity = item.get("severity", "low")
        sev_colors = {"critical": "#f44336", "high": "#ff9800", "medium": "#2196f3", "low": "#4caf50"}
        action_plan += f"""
        <div style="display:flex;align-items:flex-start;margin-bottom:16px;padding:16px;background:#252525;border-radius:8px;border-left:4px solid {sev_colors.get(severity, '#666')}">
            <div style="background:#E87811;color:#fff;font-weight:700;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:16px;flex-shrink:0">{i}</div>
            <div>
                <h4 style="margin:0 0 4px;color:#fff">{item.get('title', '')}</h4>
                <p style="margin:0;color:#b0b0b0;font-size:14px">{item.get('action', '')}</p>
                <p style="margin:4px 0 0;color:#888;font-size:12px">Effort: {item.get('effort', 'TBD')} | Impact: {item.get('impact', 'TBD')}</p>
            </div>
        </div>"""

    # Build agency footer block from env vars — empty if not configured
    _footer_parts = []
    if AGENCY_NAME:    _footer_parts.append(f"<p><strong>{AGENCY_NAME}</strong></p>")
    if AGENCY_EMAIL:   _footer_parts.append(f'<p class="footer-contact">{AGENCY_EMAIL}</p>')
    if AGENCY_WEBSITE: _footer_parts.append(f'<p><a href="https://{AGENCY_WEBSITE}" style="color:#E87811">{AGENCY_WEBSITE}</a></p>')
    agency_footer = "\n            ".join(_footer_parts)
    agency_name   = AGENCY_NAME or "ClawBoard"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Marketing Audit — {client_name}</title>
    <style>{css}</style>
    <style>
        body {{ background: #1b1b1b; color: #ffffff; font-family: Inter, -apple-system, sans-serif; margin: 0; padding: 0; }}
        .report-container {{ max-width: 900px; margin: 0 auto; padding: 40px 32px; }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <div class="header-top">
                <div class="logo">{agency_name}</div>
                <div class="header-meta">
                    <p><strong>{client_name}</strong></p>
                    <p>Audit Date: {audit_date}</p>
                </div>
            </div>
            <div class="header-title">Performance Marketing Audit</div>
            <div class="header-subtitle">Comprehensive Analysis &bull; {len(platforms)} Platforms Audited</div>
        </div>

        <div class="section">
            <h2 class="section-title">Executive Summary</h2>
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-label">Overall Score</div>
                    <div class="metric-value" style="color:{score_color}">{overall_score}<span class="metric-unit">/100</span></div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Platforms</div>
                    <div class="metric-value">{len(platforms)}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Critical Issues</div>
                    <div class="metric-value" style="color:#f44336">{critical}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">High Priority</div>
                    <div class="metric-value" style="color:#ff9800">{high}</div>
                </div>
            </div>
        </div>

        {platform_sections}

        <div class="section">
            <h2 class="section-title">Action Plan</h2>
            {action_plan}
        </div>

        <div class="report-footer">
            {agency_footer}
            <p style="margin-top:20px;font-size:11px;color:#666">Generated on {audit_date} · Powered by ClawBoard</p>
        </div>
    </div>
</body>
</html>"""


def _build_platform_section(name: str, data: dict) -> str:
    """Build HTML for one platform's findings."""
    display_name = name.replace("_", " ").title()
    score = data.get("score", 0)
    findings = data.get("findings", [])

    if score >= 75:
        badge_class = "high"
        score_color = "#4caf50"
    elif score >= 50:
        badge_class = "medium"
        score_color = "#ff9800"
    else:
        badge_class = "low"
        score_color = "#f44336"

    findings_html = ""
    for f in findings:
        severity = f.get("severity", "low")
        sev_colors = {"critical": "#f44336", "high": "#ff9800", "medium": "#2196f3", "low": "#4caf50"}
        findings_html += f"""
            <div style="margin-bottom:12px;padding:12px 16px;background:#252525;border-radius:6px;border-left:3px solid {sev_colors.get(severity, '#666')}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                    <strong style="color:#fff">{f.get('title', '')}</strong>
                    <span style="background:{sev_colors.get(severity, '#666')};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;text-transform:uppercase">{severity}</span>
                </div>
                <p style="margin:4px 0;color:#b0b0b0;font-size:13px">{f.get('description', '')}</p>
                <p style="margin:4px 0 0;color:#E87811;font-size:13px"><strong>Fix:</strong> {f.get('action', '')}</p>
            </div>"""

    return f"""
        <div class="section">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                <h2 class="section-title" style="margin:0">{display_name}</h2>
                <div style="background:{score_color};color:#fff;padding:6px 16px;border-radius:20px;font-weight:700;font-size:18px">{score}/100</div>
            </div>
            {findings_html if findings_html else '<p style="color:#b0b0b0">No issues found — all checks passed.</p>'}
        </div>"""


# ──────────────────────────────────────────────
# Subagent Loader
# ──────────────────────────────────────────────

def load_subagents(config_path: Path) -> list:
    """Load subagent definitions from YAML."""
    available_tools = {
        "fetch_google_ads_data": fetch_google_ads_data,
        "fetch_meta_ads_data": fetch_meta_ads_data,
        "fetch_analytics_data": fetch_analytics_data,
        "generate_audit_report": generate_audit_report,
    }

    with open(config_path) as f:
        config = yaml.safe_load(f)

    subagents = []
    for name, spec in config.items():
        subagent = {
            "name": name,
            "description": spec["description"],
            "system_prompt": spec["system_prompt"],
        }
        if "model" in spec:
            subagent["model"] = spec["model"]
        if "tools" in spec:
            subagent["tools"] = [available_tools[t] for t in spec["tools"] if t in available_tools]
        else:
            subagent["tools"] = []
        subagents.append(subagent)

    return subagents


# ──────────────────────────────────────────────
# Agent Factory
# ──────────────────────────────────────────────

def create_audit_agent():
    """Create the performance marketing audit agent."""
    # Use Gemini Flash if key available, fall back to Claude
    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    model = "google_genai:gemini-2.5-flash" if google_key else "anthropic:claude-sonnet-4-6"
    return create_deep_agent(
        model=model,
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[
            fetch_google_ads_data,
            fetch_meta_ads_data,
            fetch_analytics_data,
            generate_audit_report,
        ],
        subagents=load_subagents(PROJECT_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=PROJECT_DIR),
    )


# ──────────────────────────────────────────────
# CLI Display
# ──────────────────────────────────────────────

class AuditDisplay:
    """Rich terminal display for audit progress."""

    def __init__(self):
        self.printed_count = 0
        self.spinner = Spinner("dots", text="Planning audit...")

    def update_status(self, status: str):
        self.spinner = Spinner("dots", text=status)

    def print_message(self, msg):
        if isinstance(msg, HumanMessage):
            console.print(Panel(str(msg.content), title="You", border_style="blue"))

        elif isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                content = "\n".join(text_parts)

            if content and content.strip():
                console.print(Panel(Markdown(content), title="Audit Agent", border_style="yellow"))

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "unknown")
                    args = tc.get("args", {})

                    if name == "task":
                        agent_type = args.get("subagent_type", "general")
                        console.print(f"  [bold magenta]>> Delegating to {agent_type}[/]")
                        self.update_status(f"Running {agent_type}...")
                    elif name == "write_todos":
                        console.print(f"  [bold cyan]>> Planning audit tasks...[/]")
                    elif name.startswith("fetch_"):
                        console.print(f"  [bold blue]>> Fetching data: {name}[/]")
                        self.update_status(f"Fetching {name}...")
                    elif name == "generate_audit_report":
                        console.print(f"  [bold green]>> Generating report...[/]")
                        self.update_status("Generating PDF...")
                    elif name == "write_file":
                        path = args.get("file_path", "file")
                        console.print(f"  [bold yellow]>> Writing: {path}[/]")

        elif isinstance(msg, ToolMessage):
            name = getattr(msg, "name", "")
            if name == "task":
                console.print(f"  [green]✓ Subagent complete[/]")
            elif name.startswith("fetch_"):
                console.print(f"  [green]✓ Data fetched[/]")
            elif name == "generate_audit_report":
                console.print(f"  [green]✓ Report generated[/]")
            elif name == "write_file":
                console.print(f"  [green]✓ File saved[/]")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

async def main():
    """Run the audit agent."""
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = (
            "Run a full performance marketing audit for 'Example Client'. "
            "Audit Google Ads, Meta Ads, and Google Analytics. "
            "Use the specialized subagents to run each platform audit in parallel. "
            "Aggregate all findings, calculate scores, and generate a branded PDF report."
        )

    console.print()
    _label = AGENCY_NAME or "ClawBoard"
    console.print(f"[bold #E87811]━━━ {_label} ━━━[/]")
    console.print("[bold white]Performance Marketing Audit Agent[/]")
    console.print(f"[dim]{task}[/]")
    console.print()

    agent = create_audit_agent()
    display = AuditDisplay()

    with Live(display.spinner, console=console, refresh_per_second=10, transient=True) as live:
        async for chunk in agent.astream(
            {"messages": [("user", task)]},
            config={"configurable": {"thread_id": f"audit-{datetime.now().strftime('%Y%m%d%H%M%S')}"}},
            stream_mode="values",
        ):
            if "messages" in chunk:
                messages = chunk["messages"]
                if len(messages) > display.printed_count:
                    live.stop()
                    for msg in messages[display.printed_count:]:
                        display.print_message(msg)
                    display.printed_count = len(messages)
                    live.start()
                    live.update(display.spinner)

    console.print()
    console.print("[bold green]✓ Audit complete![/]")
    console.print("[dim]Reports saved to reports/ directory[/]")

    # Send results to Telegram if configured
    import glob
    report_pdfs = sorted(
        glob.glob(str(PROJECT_DIR / "reports" / "*.pdf")),
        key=os.path.getmtime,
        reverse=True,
    )[:1]  # most recent PDF only

    client_name = task.split("'")[1] if "'" in task else task.split('"')[1] if '"' in task else "Client"
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        console.print("[dim]Sending to Telegram...[/]")
        send_telegram_report(
            report_pdfs,
            client_name,
            f"Report ready in `reports/` directory.\n\nRun `ls reports/` to see it.",
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Audit interrupted[/]")
