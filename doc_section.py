import datetime
from typing import List, Dict, Any

def build_doc_blocks(report_data: List[Dict[str, Any]], product_name: str, iso_week: str, window_weeks: int) -> str:
    """
    Transforms the LLM JSON output into a plain text string to be appended to Google Docs,
    as the current MCP server does not support formatting.
    """
    today_str = datetime.date.today().isoformat()
    
    lines = []
    
    # Title Block
    lines.append(f"{product_name} — Weekly Review Pulse — {iso_week}")
    lines.append("")
    
    # Metadata Paragraph
    lines.append(f"Period: Last {window_weeks} weeks (rolling) · Source: Google Play Store · Generated: {today_str} IST")
    lines.append("")
    
    # Top Themes
    lines.append("Top themes")
    for theme in report_data:
        theme_name = theme.get("theme_name", "Unknown Theme")
        summary = theme.get("summary", "")
        lines.append(f"• {theme_name} — {summary}")
    lines.append("")
    
    # Real User Quotes
    lines.append("Real user quotes")
    for theme in report_data:
        for q in theme.get("quotes", []):
            lines.append(f"• \"{q}\"")
    lines.append("")
    
    # Action Ideas
    lines.append("Action ideas")
    for theme in report_data:
        for a in theme.get("action_ideas", []):
            lines.append(f"• {a.get('title', 'Idea')} — {a.get('detail', '')}")
    lines.append("")
    
    # Who this helps (Standard Boilerplate)
    lines.append("Who this helps")
    lines.append("• Product: Prioritize roadmap")
    lines.append("• Support: Spot repeating complaints")
    lines.append("• Leadership: Fast health snapshot")
    lines.append("")
    
    return "\n".join(lines)