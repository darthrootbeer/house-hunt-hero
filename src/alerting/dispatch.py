from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

import requests
import yaml


def load_alerts_config() -> Dict:
    """Load alerts configuration from configs/alerts.example.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'configs', 'alerts.example.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Return default config if file not found
        return {
            'email': {'enabled': False},
            'pushover': {'enabled': False}
        }


def format_alert_email(payload: Dict) -> str:
    """Format alert payload as plain text email body."""
    lines = [
        "🏠 New Property Alert!",
        "",
        f"Title: {payload.get('title', 'N/A')}",
        f"Source: {payload.get('source', 'N/A')}",
        f"URL: {payload.get('listing_url', 'N/A')}",
        f"Price: {payload.get('price', 'N/A')}",
        "",
        "Property Details:",
    ]
    
    # Add property details from raw_payload if available
    raw_payload = payload.get('raw_payload', {})
    if raw_payload:
        for key, value in raw_payload.items():
            if value and key != 'card_text':  # Skip long text fields
                lines.append(f"  {key}: {value}")
    
    # Add AI scoring if available
    if 'score' in payload:
        lines.extend([
            "",
            f"AI Confidence: {payload['score'].get('confidence', 'N/A')}",
            f"Reasons: {', '.join(payload['score'].get('reasons', []))}",
        ])
    
    # Add timestamp
    lines.extend([
        "",
        f"Discovered: {payload.get('source_timestamp', 'N/A')}",
        "",
        "---",
        "This alert was sent by House Hunt Hero",
    ])
    
    return "\n".join(lines)


def send_email(payload: Dict) -> None:
    """Send alert via SMTP email."""
    config = load_alerts_config()
    email_config = config.get('email', {})
    
    if not email_config.get('enabled', False):
        print(f"[email] Disabled - would send alert for {payload.get('listing_id')}")
        return
    
    # Get SMTP credentials from environment
    smtp_username = os.environ.get(email_config.get('username_env', 'SMTP_USERNAME'))
    smtp_password = os.environ.get(email_config.get('password_env', 'SMTP_PASSWORD'))
    
    if not smtp_username or not smtp_password:
        print(f"[email] ERROR: SMTP credentials not found in environment variables")
        return
    
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = email_config.get('from', 'alerts@example.com')
        msg['To'] = ', '.join(email_config.get('to', []))
        msg['Subject'] = f"🏠 New Property: {payload.get('title', 'Property Alert')}"
        
        # Format body
        body = format_alert_email(payload)
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server and send
        smtp_host = email_config.get('smtp_host', 'smtp.gmail.com')
        smtp_port = email_config.get('smtp_port', 587)
        use_tls = email_config.get('use_tls', True)
        
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f"[email] ✅ Sent alert for {payload.get('listing_id')}")
        
    except Exception as e:
        print(f"[email] ❌ Failed to send: {type(e).__name__}: {str(e)}")


def send_pushover(payload: Dict) -> None:
    """Send alert via Pushover API."""
    config = load_alerts_config()
    pushover_config = config.get('pushover', {})
    
    if not pushover_config.get('enabled', False):
        print(f"[pushover] Disabled - would send alert for {payload.get('listing_id')}")
        return
    
    # Get Pushover credentials from environment
    user_key = os.environ.get(pushover_config.get('user_key_env', 'PUSHOVER_USER_KEY'))
    api_token = os.environ.get(pushover_config.get('api_token_env', 'PUSHOVER_API_TOKEN'))
    
    if not user_key or not api_token:
        print(f"[pushover] ERROR: Pushover credentials not found in environment variables")
        return
    
    try:
        # Format message
        title = f"🏠 {payload.get('title', 'New Property')}"
        message = f"{payload.get('source', 'Source')}: {payload.get('price', 'N/A')}\n{payload.get('listing_url', '')}"
        
        # Add AI score if available
        if 'score' in payload:
            confidence = payload['score'].get('confidence', 'N/A')
            message = f"Confidence: {confidence}\n{message}"
        
        # Send to Pushover API
        response = requests.post(
            'https://api.pushover.net/1/messages.json',
            data={
                'token': api_token,
                'user': user_key,
                'title': title,
                'message': message,
                'url': payload.get('listing_url', ''),
                'url_title': 'View Listing',
                'priority': pushover_config.get('priority', 0),
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"[pushover] ✅ Sent alert for {payload.get('listing_id')}")
        else:
            print(f"[pushover] ❌ Failed: HTTP {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"[pushover] ❌ Failed to send: {type(e).__name__}: {str(e)}")


def dispatch_alert(payload: Dict) -> None:
    """Dispatch alert to all enabled channels."""
    send_email(payload)
    send_pushover(payload)
