"""
app.py
Streamlit Fiverr Gig SEO Analyzer (v4)
Author: Muhammad Affaf
License: MIT

Features:
- Manual gig input + analysis (Title, Description, Tags, Extras)
- Paste Fiverr gig URL -> auto-fetch title/description/tags/seller hints
- Health status (Perfect / Good / Needs work) + recommendations
- Optional matplotlib chart (if available)
"""

import re
import json
import requests
import streamlit as st

# Optional import — matplotlib only if available
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

from bs4 import BeautifulSoup

# ---------------------------
# Utility: fetch gig page & parse
# ---------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
}

def fetch_gig_from_url(url, timeout=10):
    """
    Try to fetch a Fiverr gig page and extract:
    - title (og:title or page title)
    - description (og:description or ld+json or meta description)
    - tags (meta keywords or guess from content)
    - seller hints (level text like 'Top Rated Seller' or 'Level 2 Seller')
    - image present (og:image)
    Returns dict with keys and possible 'error' message if failed.
    """
    result = {
        "title": None,
        "description": None,
        "tags": [],
        "has_image": False,
        "has_video": False,
        "seller_level": None,
        "error": None,
        "raw_html_snippet": None
    }

    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code != 200:
            result["error"] = f"Failed to fetch page (status code {r.status_code})."
            return result

        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # 1) og:title or title tag
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            result["title"] = og_title["content"].strip()
        else:
            # fallback: title tag
            t = soup.find("title")
            if t:
                result["title"] = t.get_text().strip()

        # 2) og:description or meta description or ld+json
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            result["description"] = og_desc["content"].strip()
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["description"] = meta_desc["content"].strip()
        # 2b) try JSON-LD
        if not result["description"]:
            for js in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(js.string or "{}")
                    # Look for description keys
                    if isinstance(data, dict):
                        if data.get("description"):
                            result["description"] = data.get("description").strip()
                            break
                        # sometimes offers or headline
                        if data.get("headline") and not result["title"]:
                            result["title"] = data.get("headline").strip()
                    elif isinstance(data, list):
                        for el in data:
                            if isinstance(el, dict) and el.get("description"):
                                result["description"] = el.get("description").strip()
                                break
                except Exception:
                    continue

        # 3) tags: try meta keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            tags = [t.strip() for t in meta_keywords["content"].split(",") if t.strip()]
            result["tags"].extend(tags)

        # 3b) attempt to extract visible tag-like labels (best-effort)
        # Common Fiverr markup may have elements with data-test or aria-labels — try some heuristics
        potential_tags = set()
        for el in soup.select("a,span,div"):
            # skip very short texts
            try:
                txt = el.get_text(separator=" ", strip=True)
            except Exception:
                continue
            if not txt or len(txt) > 40:
                continue
            # simple heuristic: tags often single words or 2-word phrases
            if re.match(r"^[A-Za-z0-9\s\-]{2,30}$", txt):
                # avoid common site words
                if txt.lower() in ("read more", "view profile", "see more", "reviews", "about"):
                    continue
                # avoid numbers-only
                if txt.isdigit():
                    continue
                if len(txt.split()) <= 3:
                    potential_tags.add(txt)
        # add top few potential tags
        for t in list(potential_tags)[:8]:
            if t.lower() not in [x.lower() for x in result["tags"]]:
                result["tags"].append(t)

        # 4) image: og:image presence
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            result["has_image"] = True

        # 5) seller level detection: search for known strings in page text
        txt = soup.get_text(separator=" ", strip=True).lower()
        if "top rated seller" in txt:
            result["seller_level"] = "top_rated"
        elif "level two seller" in txt or "level 2 seller" in txt or "level 2" in txt:
            result["seller_level"] = "level_two"
        elif "level one seller" in txt or "level 1 seller" in txt or "level 1" in txt:
            result["seller_level"] = "level_one"

        # 6) video detection — best-effort: search for 'video' in scripts or meta
        if "video" in html.lower() or soup.find("meta", property="og:video"):
            result["has_video"] = True

        # store snippet for debugging if nothing found
        if not result["title"] and not result["description"]:
            result["raw_html_snippet"] = html[:2000]

        return result

    except Exception as e:
        result["error"] = f"Exception when fetching URL: {str(e)}"
        return result

# -------------------------------------------------
# ANALYZER LOGIC (same scoring engine extended)
# -------------------------------------------------
def keyword_density(text, keywords):
    """Calculate keyword density (ratio of keyword hits to total words)."""
    if not text or not keywords:
        return 0
    words = re.findall(r'\w+', text.lower())
    if not words:
        return 0
    count = sum(words.count(k.lower()) for k in keywords)
    return (count / len(words)) * 100


def analyze_gig_local(gig):
    """
    gig: dict containing:
      title, description, tags (list), primary_keywords (list), extras (dict)
    returns analysis dict
    """
    title = gig.get("title", "") or ""
    description = gig.get("description", "") or ""
    tags = gig.get("tags", []) or []
    primary_keywords = gig.get("primary_keywords", []) or []
    extras = gig.get("extras", {}) or {}

    # ----------------------- TITLE SCORE -----------------------
    title_score = 0
    if 40 <= len(title) <= 80:
        title_score += 30
    elif 25 <= len(title) < 40:
        title_score += 20
    if any(k.lower() in title.lower() for k in primary_keywords):
        title_score += 15
    if title.lower().startswith("i will"):
        title_score += 5
    if re.search(r"[!?.]{2,}", title):
        title_score -= 3
    title_score = max(0, min(title_score, 50))

    # ----------------------- DESCRIPTION SCORE -----------------------
    desc_score = 0
    word_count = len(description.split())
    density = keyword_density(description, primary_keywords)

    if 150 <= word_count <= 600:
        desc_score += 25
    elif 80 <= word_count < 150:
        desc_score += 15
    if 2 <= density <= 6:
        desc_score += 15
    elif 6 < density <= 10:
        desc_score += 10
    if "\n" in description:
        desc_score += 5
    if description.endswith("."):
        desc_score += 5
    desc_score = max(0, min(desc_score, 50))

    # ----------------------- TAG SCORE -----------------------
    tag_score = 0
    if len(tags) >= 3:
        tag_score += 20
    if len(tags) >= 5:
        tag_score += 10
    if any(k.lower() in [t.lower() for t in tags] for k in primary_keywords):
        tag_score += 10
    tag_score = min(tag_score, 40)

    # ----------------------- FAQ / EXTRAS SCORE -----------------------
    faq_score = 0
    if extras.get("has_faqs"):
        faq_score += 10
    if extras.get("has_packages"):
        faq_score += 10
    if extras.get("has_delivery_info"):
        faq_score += 10
    if extras.get("has_image"):
        faq_score += 10
    if extras.get("has_video"):
        faq_score += 10
    if extras.get("image_contains_text"):
        faq_score += 5
    if extras.get("completion_rate", 0) >= 90:
        faq_score += 10
    faq_score = min(faq_score, 60)

    # ----------------------- SELLER STATS -----------------------
    seller_boost = 0
    level = extras.get("seller_level")
    if level == "level_one":
        seller_boost += 5
    elif level == "level_two":
        seller_boost += 10
    elif level == "top_rated":
        seller_boost += 15
    if extras.get("response_time_hours", 24) <= 4:
        seller_boost += 5

    # ----------------------- ENGAGEMENT SIMULATION -----------------------
    engagement = 0
    if any(k in title.lower() for k in ["power bi", "data", "dashboard", "visualization"]):
        engagement += 5
    if len(description) > 250:
        engagement += 5
    engagement = min(engagement, 10)

    # ----------------------- FINAL SCORE -----------------------
    weights = {
        "title": 0.25,
        "description": 0.3,
        "tags": 0.2,
        "faq": 0.15,
        "seller": 0.1,
    }

    overall = (
        title_score * weights["title"]
        + desc_score * weights["description"]
        + tag_score * weights["tags"]
        + faq_score * weights["faq"]
        + seller_boost * weights["seller"]
        + engagement
    )
    overall = round(min(overall, 100), 1)

    # Health labeling
    if overall >= 85:
        health = "Perfect"
    elif overall >= 60:
        health = "Good"
    else:
        health = "Needs work"

    # ----------------------- RECOMMENDATIONS -----------------------
    recs = []
    if title_score < 40:
        recs.append("Improve your gig title — include 1–2 keywords naturally and place them early.")
    if desc_score < 40:
        recs.append("Add more detail and structure to your description (use bullets, deliverables, CTA).")
    if tag_score < 30:
        recs.append("Use 5 relevant tags closely related to your keywords; avoid generic terms.")
    if faq_score < 40:
        recs.append("Add FAQs, media (image/video), and ensure all gig extras are filled.")
    if overall >= 85:
        recs.append("Excellent SEO! Your gig is highly optimized for ranking.")
    else:
        recs.append("Follow the above suggestions and run the analysis again.")

    return {
        "overall_score": overall,
        "health": health,
        "components": {
            "Title Score": title_score,
            "Description Score": desc_score,
            "Tag Score": tag_score,
            "FAQ & Extras Score": faq_score,
            "Seller Boost": seller_boost,
            "Engagement": engagement
        },
        "primary_keywords_used": [k for k in primary_keywords if k.lower() in title.lower() or k.lower() in description.lower()],
        "recommendations": recs,
        "raw": {
            "keyword_density": round(density, 2),
            "word_count": word_count
        }
    }

# -------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------
st.set_page_config(page_title="Fiverr Gig SEO Analyzer (v4)", layout="wide")
st.title("💡 Fiverr Gig SEO Analyzer (v4)")
st.markdown(
    """
Paste a Fiverr gig link to auto-fetch gig content, or manually paste title/description/tags.
The analyzer returns a 0–100 SEO score, component breakdown, and health label (Perfect / Good / Needs work).
"""
)

# Left column: URL fetch + manual inputs
left, right = st.columns([1, 1])

with left:
    st.subheader("1) Paste Fiverr Gig URL (optional)")
    gig_url = st.text_input("Fiverr Gig URL", placeholder="https://www.fiverr.com/username/gig-title")
    if st.button("🔗 Fetch from URL"):
        if not gig_url:
            st.error("Please paste a Fiverr gig URL.")
        else:
            with st.spinner("Fetching gig... (may take a few seconds)"):
                fetched = fetch_gig_from_url(gig_url)
            if fetched.get("error"):
                st.error(f"Could not fetch gig: {fetched['error']}")
                # show raw snippet if available
                if fetched.get("raw_html_snippet"):
                    st.info("Page snippet available for debugging.")
                    st.code(fetched["raw_html_snippet"][:800])
                # allow manual override
                st.session_state["fetched"] = None
            else:
                st.success("Fetched successfully! Fields populated below.")
                st.session_state["fetched"] = fetched
                # Pre-fill inputs by writing to session_state keys (used below)
                st.session_state["title_prefill"] = fetched.get("title") or ""
                st.session_state["description_prefill"] = fetched.get("description") or ""
                # tags
                if fetched.get("tags"):
                    st.session_state["tags_prefill"] = ", ".join(fetched.get("tags")[:8])
                else:
                    st.session_state["tags_prefill"] = ""
                # extras
                st.session_state["has_image_prefill"] = fetched.get("has_image", False)
                st.session_state["has_video_prefill"] = fetched.get("has_video", False)
                st.session_state["seller_level_prefill"] = fetched.get("seller_level") or "none"

    st.write("---")
    st.subheader("2) Manual / Auto fields")
    # use session_state prefilled values if available
    title_val = st.text_input("Gig Title (editable)", value=st.session_state.get("title_prefill", ""))
    description_val = st.text_area("Gig Description (editable)", value=st.session_state.get("description_prefill", ""), height=220)
    tags_input = st.text_input("Tags (comma separated)", value=st.session_state.get("tags_prefill", ""))
    tags_list = [t.strip() for t in tags_input.split(",") if t.strip()]

with right:
    st.subheader("3) Extras / Seller info")
    col1, col2 = st.columns(2)
    with col1:
        has_faqs = st.checkbox("Has FAQs?", value=st.session_state.get("has_faqs_prefill", False))
        has_packages = st.checkbox("Has Packages?", value=False)
        has_delivery_info = st.checkbox("Has Delivery Info?", value=False)
    with col2:
        has_image = st.checkbox("Has Image?", value=st.session_state.get("has_image_prefill", False))
        has_video = st.checkbox("Has Video?", value=st.session_state.get("has_video_prefill", False))
        image_contains_text = st.checkbox("Image Contains Text?", value=False)

    seller_level = st.selectbox("Seller Level", ["none", "level_one", "level_two", "top_rated"], index=0 if not st.session_state.get("seller_level_prefill") else ["none", "level_one", "level_two", "top_rated"].index(st.session_state.get("seller_level_prefill")))
    response_time = st.number_input("Response Time (hours)", min_value=0, max_value=72, value=4)
    completion_rate = st.slider("Completion Rate (%)", 0, 100, 90)

    st.write("---")
    st.markdown("### Quick tips")
    st.markdown("- Use `power bi`, `dashboard`, or the primary keyword in title + first sentence of description.")
    st.markdown("- Include at least 4–5 focused tags and a short gig video or image.")

# Run analysis button
if st.button("🔍 Analyze Gig (Run)"):
    gig_payload = {
        "title": title_val,
        "description": description_val,
        "tags": tags_list,
        "primary_keywords": [k.strip() for k in (st.text_input("Primary Keywords (comma separated)", value="") or "").split(",") if k.strip()] or [t for t in tags_list[:2]],
        "extras": {
            "has_faqs": has_faqs,
            "has_packages": has_packages,
            "has_delivery_info": has_delivery_info,
            "has_image": has_image,
            "has_video": has_video,
            "image_contains_text": image_contains_text,
            "seller_level": None if seller_level == "none" else seller_level,
            "response_time_hours": response_time,
            "completion_rate": completion_rate
        }
    }

    # If user fetched earlier and left primary keywords blank, attempt to extract from fetched tags/title
    if "fetched" in st.session_state and st.session_state.get("fetched"):
        fetched = st.session_state["fetched"]
        # fill missing fields if left empty
        if not gig_payload["title"]:
            gig_payload["title"] = fetched.get("title") or gig_payload["title"]
        if not gig_payload["description"]:
            gig_payload["description"] = fetched.get("description") or gig_payload["description"]
        if not gig_payload["tags"] and fetched.get("tags"):
            gig_payload["tags"] = fetched.get("tags"]
        # set extras from fetched if user left defaults
        if gig_payload["extras"].get("has_image") is False and fetched.get("has_image"):
            gig_payload["extras"]["has_image"] = fetched.get("has_image")
        if (not gig_payload["extras"].get("seller_level")) and fetched.get("seller_level"):
            gig_payload["extras"]["seller_level"] = fetched.get("seller_level")

    # analyze
    analysis = analyze_gig_local(gig_payload)

    # Display results
    st.success("✅ Analysis Completed!")
    st.markdown(f"## 🎯 Overall Score: **{analysis['overall_score']} / 100** — **{analysis['health']}**")

    # components display as metrics
    comp = analysis["components"]
    # 3 columns layout for metrics
    ccols = st.columns(3)
    items = list(comp.items())
    for i, (k, v) in enumerate(items):
        ccols[i % 3].metric(k, f"{v}")

    # show chart if matplotlib available
    if plt:
        st.markdown("### 📈 SEO Component Chart")
        fig, ax = plt.subplots(figsize=(7, 3.5))
        labels = list(comp.keys())
        scores = list(comp.values())
        ax.barh(labels, scores)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Score")
        ax.set_title("Component Scores")
        st.pyplot(fig)

    # show recommendations
    st.markdown("### 💬 Recommendations & Next Steps")
    for i, r in enumerate(analysis["recommendations"], 1):
        st.markdown(f"**{i}.** {r}")

    # extra raw info
    with st.expander("🔎 Raw analysis data"):
        st.json(analysis["raw"])

    # quick action suggestions
    st.markdown("### 🚀 Action Checklist")
    st.markdown("- Put primary keyword within first 8–12 words of the title.")
    st.markdown("- Expand description to 150–300 words, with bullet points for deliverables.")
    st.markdown("- Add 4–6 focused tags and at least 1 gig image or short video.")
    st.markdown("- Keep response time under 4 hours and maintain high completion rate.")

