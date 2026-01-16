"""Test script for alerting system."""

from datetime import datetime, timezone

from src.alerting.dispatch import dispatch_alert, send_email, send_pushover


def test_alerting():
    """Test alerting dispatch with sample payload."""
    
    # Sample alert payload
    payload = {
        'listing_id': 'test_source:https://example.com/listing/123',
        'title': '123 Main St, Portland, ME 04101',
        'source': 'test_source',
        'listing_url': 'https://example.com/listing/123',
        'price': '$350,000',
        'source_timestamp': datetime.now(timezone.utc).isoformat(),
        'raw_payload': {
            'beds': '3',
            'baths': '2',
            'sqft': '1,800',
            'price': '$350,000',
        },
        'score': {
            'confidence': 'high',
            'reasons': ['In target price range', 'Good location', 'Matches house profile'],
        }
    }
    
    print("="*70)
    print("ALERTING SYSTEM TEST")
    print("="*70)
    print("\nTest Payload:")
    print(f"  Listing: {payload['title']}")
    print(f"  Source: {payload['source']}")
    print(f"  URL: {payload['listing_url']}")
    print(f"  Price: {payload['price']}")
    print()
    
    # Test email alerting
    print("-"*70)
    print("Testing Email Alerting:")
    print("-"*70)
    try:
        send_email(payload)
        print("✅ Email function executed without errors")
    except Exception as e:
        print(f"❌ Email function failed: {type(e).__name__}: {str(e)}")
    print()
    
    # Test Pushover alerting
    print("-"*70)
    print("Testing Pushover Alerting:")
    print("-"*70)
    try:
        send_pushover(payload)
        print("✅ Pushover function executed without errors")
    except Exception as e:
        print(f"❌ Pushover function failed: {type(e).__name__}: {str(e)}")
    print()
    
    # Test dispatch (both channels)
    print("-"*70)
    print("Testing Dispatch (Both Channels):")
    print("-"*70)
    try:
        dispatch_alert(payload)
        print("✅ Dispatch function executed without errors")
    except Exception as e:
        print(f"❌ Dispatch function failed: {type(e).__name__}: {str(e)}")
    print()
    
    print("="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nNotes:")
    print("- Email and Pushover are disabled by default in alerts.example.yaml")
    print("- To enable, set enabled: true and configure environment variables:")
    print("  - SMTP_USERNAME, SMTP_PASSWORD for email")
    print("  - PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN for Pushover")
    print("- Functions execute without errors even when disabled")
    print()


if __name__ == "__main__":
    test_alerting()
