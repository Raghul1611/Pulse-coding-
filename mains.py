import requests
import json
import os
from datetime import datetime, date
from dateutil.parser import isoparse


# -----------------------------
# Fetch reviews from Wextractor
# -----------------------------
def fetch_g2_reviews(company: str, auth_token: str, offset: int = 0, batch_size: int = 50):
    url = "https://wextractor.com/api/v1/reviews/g2"
    params = {
        "id": company,
        "auth_token": auth_token,
        "offset": offset
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"API Error for {company}: {response.status_code} {response.text}")
        return []

    data = response.json()
    return data.get("reviews", [])[:batch_size]


# ---------------------------------------
# Fetch reviews within a valid date range
# ---------------------------------------
def fetch_reviews_in_date_range(company, auth_token, start_date_str, end_date_str):
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    all_reviews = []
    offset = 0

    print(f"\nFetching reviews for {company} from {start_date.date()} to {end_date.date()}...")

    while True:
        reviews = fetch_g2_reviews(company, auth_token, offset)

        if not reviews:
            break

        for r in reviews:
            try:
                review_date = isoparse(r.get("datetime", ""))
            except:
                continue

            # Stop early if reviews are older than start date
            if review_date < start_date:
                return all_reviews

            if start_date <= review_date <= end_date:
                all_reviews.append({
                    "source": "g2",
                    "company": company,
                    "title": r.get("title", ""),
                    "review": r.get("text", ""),
                    "reviewer": r.get("reviewer", ""),
                    "rating": r.get("rating", ""),
                    "date": review_date.strftime("%Y-%m-%d")
                })

        offset += len(reviews)

    return all_reviews


# -----------------------------
# Save reviews to JSON
# -----------------------------
def save_reviews(company, reviews):
    os.makedirs("output", exist_ok=True)
    output_file = f"output/{company}_g2_reviews.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(reviews)} reviews to {output_file}")


# -----------------------------
# MAIN
# -----------------------------
def main():
    companies_input = input("Enter G2 company slugs separated by comma (e.g., jira, notion): ")
    companies = [c.strip() for c in companies_input.split(",") if c.strip()]

    auth_token = input("Enter your Wextractor auth token: ").strip()
    start_date_input = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date_input = input("Enter end date (YYYY-MM-DD): ").strip()

    # -----------------------------
    # DATE VALIDATION (IMPORTANT)
    # -----------------------------
    today = date.today()

    start_date = datetime.fromisoformat(start_date_input).date()
    end_date = datetime.fromisoformat(end_date_input).date()

    if start_date > today:
        print("❌ Start date cannot be in the future.")
        return

    if end_date > today:
        print("⚠ End date is in the future. Adjusting to today.")
        end_date = today

    if start_date > end_date:
        print("❌ Start date must be before end date.")
        return

    # -----------------------------
    # FETCH FOR EACH COMPANY
    # -----------------------------
    for company in companies:
        reviews = fetch_reviews_in_date_range(
            company,
            auth_token,
            start_date.isoformat(),
            end_date.isoformat()
        )

        if not reviews:
            print(f"No reviews found for {company} in this date range.")
        else:
            save_reviews(company, reviews)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
