"""
Enrich Google Maps salon data with external websites using Playwright.

Workflow:
1. Reads `cleaned_beauty_salons.csv` (or resumes from `final_beauty_salons.csv`).
2. Opens each business's Google Maps link in a headless browser.
3. Waits for the listing panel to load (h1 or Directions button).
4. Extracts the destination website from the Google Maps listing.
5. Categorizes into Dedicated Website, Social Media, or No Link.
6. Applies a 3-second delay between requests to prevent rate-limiting.
7. Saves progress incrementally and outputs `final_beauty_salons.csv`.
"""

import os
import re
import sys
import time
from urllib.parse import parse_qs, unquote, urlparse
import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

# Ensure console handles UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def unwrap_google_url(url: str) -> str:
    """Extract actual destination website from Google redirect URLs."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Google redirects usually look like /url?q=https://example.com or /url?url=...
        if "google." in parsed.netloc and "/url" in parsed.path:
            query = parse_qs(parsed.query)
            if "q" in query:
                return query["q"][0]
            if "url" in query:
                return query["url"][0]
    except Exception:
        pass
    return url


def classify_url(url: str) -> str:
    """Classify a website into Dedicated Website, Social Media, or No Link."""
    if not url or pd.isna(url):
        return "No Link"

    u = str(url).strip().lower()
    if not u or any(m in u for m in ["google.com/maps", "maps.google", "goo.gl"]):
        return "No Link"

    social_domains = [
        "facebook.com",
        "fb.com",
        "fb.me",
        "instagram.com",
        "instagr.am",
        "tiktok.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
        "youtube.com",
        "pinterest.com",
        "threads.net",
    ]
    if any(s in u for s in social_domains):
        return "Social Media"

    # If it has a standard URL format or domain dot
    if u.startswith("http://") or u.startswith("https://") or "." in u:
        return "Dedicated Website"

    return "No Link"


def scrape_websites(
    input_csv="cleaned_beauty_salons.csv",
    output_csv="final_beauty_salons.csv",
    resume=False,
):
    print("=" * 65)
    print("[*] Beauty Salons Google Maps Website Scraper (Playwright)")
    print("=" * 65)

    # Resume support: If output_csv already exists and resume requested, resume from it
    if resume and os.path.exists(output_csv):
        print(f"[*] Found existing '{output_csv}'. Resuming progress...")
        df = pd.read_csv(output_csv)
    elif os.path.exists(input_csv):
        print(f"[*] Loading input file: '{input_csv}'...")
        df = pd.read_csv(input_csv)
    else:
        print(f"[!] Error: Neither '{output_csv}' nor '{input_csv}' found.")
        return

    if "Website URL" not in df.columns:
        df["Website URL"] = ""
    if "Website Type" not in df.columns:
        df["Website Type"] = "No Link"

    total = len(df)
    print(f"Total businesses to process: {total}\n")

    with sync_playwright() as p:
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]

        browser = None
        # Try local Chrome, then Edge, then default Chromium
        for channel_name in ["chrome", "msedge", None]:
            try:
                if channel_name:
                    browser = p.chromium.launch(
                        channel=channel_name, headless=True, args=browser_args
                    )
                    print(f"[*] Successfully launched system {channel_name.capitalize()} browser.")
                else:
                    browser = p.chromium.launch(headless=True, args=browser_args)
                    print("[*] Successfully launched default Chromium browser.")
                break
            except Exception:
                continue

        if not browser:
            print("[!] Error: Could not launch any browser via Playwright.")
            return

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = context.new_page()

        for idx, row in df.iterrows():
            business_name = row.get("Business Name", f"Row {idx + 1}")
            maps_url = str(row.get("URL", "")).strip()

            # Skip if already resolved when resuming
            if resume:
                existing_url = str(row.get("Website URL", "")).strip()
                existing_type = str(row.get("Website Type", "")).strip()
                if existing_url and existing_type and existing_type != "nan":
                    print(f"[{idx + 1}/{total}] [SKIP] {business_name}: Already processed ({existing_url})")
                    continue

            if not maps_url or maps_url == "nan" or "google.com/maps" not in maps_url:
                print(f"[{idx + 1}/{total}] [SKIP] {business_name}: No valid Google Maps link.")
                df.at[idx, "Website URL"] = ""
                df.at[idx, "Website Type"] = "No Link"
                continue

            print(f"[{idx + 1}/{total}] Visiting: {business_name}...")
            extracted_url = ""

            try:
                page.goto(maps_url, timeout=18000, wait_until="domcontentloaded")

                # Handle Google consent / cookie dialogue if visible
                try:
                    consent_btn = page.locator(
                        'button:has-text("Accept all"), button:has-text("I agree"), form[action*="consent"] button'
                    ).first
                    if consent_btn.is_visible(timeout=1000):
                        consent_btn.click()
                except Exception:
                    pass

                # Wait for the listing panel (h1 or Directions button) to render
                try:
                    page.locator('h1, button[data-value*="Directions"]').first.wait_for(
                        state="visible", timeout=7000
                    )
                except Exception:
                    pass

                # Grace period for listing buttons to attach in DOM
                page.wait_for_timeout(800)

                # Google Maps official website button locators
                website_btn = page.locator(
                    'a[data-item-id="authority"], a[aria-label*="Website" i], a[data-tooltip*="website" i]'
                ).first

                if website_btn.is_visible():
                    raw_href = website_btn.get_attribute("href")
                    extracted_url = unwrap_google_url(raw_href)

            except PlaywrightTimeoutError:
                print("    [!] Timeout loading Google Maps page.")
            except Exception as e:
                print(f"    [!] Error occurred: {e}")

            site_type = classify_url(extracted_url)
            df.at[idx, "Website URL"] = extracted_url
            df.at[idx, "Website Type"] = site_type

            if extracted_url:
                print(f"    [+] Found: {extracted_url} [{site_type}]")
            else:
                print(f"    [-] No website found [{site_type}]")

            # Auto-save progress every 5 rows
            if (idx + 1) % 5 == 0:
                df.to_csv(output_csv, index=False, encoding="utf-8-sig")
                print(f"    [*] Progress auto-saved ({idx + 1}/{total} completed).")

            # 3-second delay between visits to prevent rate-limiting
            time.sleep(3)

        browser.close()

    # Reorder columns neatly
    preferred_order = [
        "Business Name",
        "Category",
        "Rating",
        "Reviews",
        "Address",
        "Hours",
        "Website URL",
        "Website Type",
        "URL",
    ]
    final_cols = [c for c in preferred_order if c in df.columns] + [
        c for c in df.columns if c not in preferred_order
    ]
    df = df[final_cols]

    # Final save
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 65)
    print(f"[*] Enrichment Complete! Output saved to: {output_csv}")
    print("=" * 65)
    print("\n[*] Summary Breakdown of Website Types:")
    print(df["Website Type"].value_counts())
    print("\n")


if __name__ == "__main__":
    resume_flag = "--resume" in sys.argv
    scrape_websites(resume=resume_flag)
