import datetime
from typing import List, Dict, Any, Tuple

def build_email_teaser(report_data: List[Dict[str, Any]], product_name: str, iso_week: str, doc_url: str) -> Tuple[str, str, str]:
    """
    Builds the email teaser components.
    Returns: (subject, html_body, text_body)
    """
    subject = f"{product_name} Weekly Review Pulse — {iso_week}"
    
    # Extract top 3-5 themes for the teaser
    themes = [f"{t.get('theme_name', 'Theme')} — {t.get('summary', '')}" for t in report_data[:5]]
    
    # 1. Plain Text Body
    text_body = f"Here is your {product_name} weekly review pulse for {iso_week}.\n\nTop Themes:\n"
    for t in themes:
        text_body += f"- {t}\n"
    text_body += f"\nRead the full report with quotes and action ideas here: {doc_url}\n"
    
    # 2. HTML Body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2>{product_name} Weekly Review Pulse — {iso_week}</h2>
        <p>Here is your weekly review pulse covering the top feedback themes from the Google Play Store.</p>
        <h3>Top Themes</h3>
        <ul>
    """
    for t in themes:
        html_body += f"<li>{t}</li>"
        
    html_body += f"""
        </ul>
        <p><a href="{doc_url}" style="display: inline-block; padding: 10px 15px; background-color: #0056b3; color: white; text-decoration: none; border-radius: 4px;">Read Full Report in Google Docs</a></p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #999;">Generated: {datetime.date.today().isoformat()}</p>
    </body>
    </html>
    """
    
    return subject, html_body, text_body