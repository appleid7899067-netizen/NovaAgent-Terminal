#!/usr/bin/env python3
import argparse
import json
import sys
from bs4 import BeautifulSoup
import requests

# Simple fetcher for live slot results; tries to extract a minimal structured payload.
# Note: This is a pragmatic starter script; real-world pages may require more robust parsing.


def parse_slot_html(html):
    """Try to parse a basic slot result from an HTML page.
    Returns a dict with keys: reels, payout, bankroll, timestamp, raw."""
    data = {
        "success": False,
        "timestamp": int(__import__('time').time()),
        "latest_spin": None,
        "snippet": None
    }
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # Attempt common patterns
        reels_elems = soup.find_all(string=lambda t: t and ('REELS' in t.upper() or 'REEL' in t.upper()))
        if reels_elems:
            data["latest_spin"] = [r.strip() for r in reels_elems[:3]]
        # Payout / bankroll lookups (simple heuristics)
        payout_text = soup.find(string=lambda t: t and ('PAYOUT' in t.upper() or 'WIN' in t.upper()))
        if payout_text:
            data["snippet"] = str(payout_text.strip())
        # Fallback: take the first 2-3 numeric values on the page as bankroll/payout
        nums = [float(n) for n in soup.find_all(text=lambda t: t and t.replace('.', '', 1).isdigit())]
        if nums:
            data["bankroll"] = nums[-1]
            data["payout"] = nums[-2] if len(nums) > 1 else None
            data["latest_spin"] = data.get("latest_spin") or []
        data["success"] = True if data["latest_spin"] or data["snippet"] else False
    except Exception as e:
        data["snippet"] = str(e)
        data["success"] = False
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True, help='Slot game URL to fetch')
    ap.add_argument('--output', required=False, help='Output JSON path')
    args = ap.parse_args()
    try:
        resp = requests.get(args.url, timeout=20)
        html = resp.text
        parsed = parse_slot_html(html)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        sys.exit(0 if parsed.get('success') else 1)
    except Exception as e:
        err = {'success': False, 'timestamp': int(__import__('time').time()), 'snippet': str(e)}
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(err, f, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(err, ensure_ascii=False, indent=2))
        sys.exit(2)

if __name__ == '__main__':
    main()
