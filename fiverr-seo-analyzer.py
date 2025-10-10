"""
app.py
Streamlit Fiverr Gig SEO Analyzer (v4.2)
Author: Muhammad Affaf
License: MIT

Upgrades:
✅ Fixed SyntaxError for tags fetching
✅ Added auto keyword fill if blank
✅ Added visual polish and section dividers
✅ Improved keyword density safety
✅ Ready for GitHub push
"""

import re
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup

# Optional import — matplotlib only if available
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

# -------------------------------------------------
# Utility: Fetch Fiverr Gig Data
# -------------------------------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
}

def fetch_gig_from_url(url, timeout=10):
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
            result["error"] = f"Failed to fetch page (status {r.status_code})"
            return result

        soup = BeautifulSoup(r.text, "html.parser")

        # Title
        title_tag = soup.find("meta", property="og:title")
        if title_tag and title_tag.get("content"):
            result["title"] = title_tag["content"].strip()
        else:
            t = soup.find("title")
            if t:
                result["title"] = t.get_text().strip()

        # Description
        desc_tag = soup.find("meta", property="og:description")
        if desc_tag and desc_tag.get("content"):
            result["description"] = desc_tag["content"].strip()
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["description"] = meta_desc["content"].strip()

        # Tags
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            tags = [t.strip() for t in meta_keywords["content"].split(",") if t.strip()]
            result["tags"].extend(tags)

        # Heuristic tag scraping
        potential_tags = set()
        for el in soup.select("a, span, div"):
            txt = el.get_text(separator=" ", strip=True)
            if not txt or len(txt) > 40:
                continue
            if re.match(r"^[A-Za-z0-9\s\-]{2,30}$", txt):
                if txt.lower() not in ("read more", "reviews", "about", "see more"):
                    potential_tags.add(txt)
        for t in list(potential_tags)[:8]:
            if t.lower() not in [x.lower() for x in result["tags"]]:
                result["tags"].append(t)

        # Seller level
        txt = soup.get_text(separator=" ", strip=True).lower()
        if "top rated seller" in txt:
            result["seller_level"] = "top_rated"
        elif "level two" in txt or "level 2" in txt:
            result["seller_level"] = "level_two"
        elif "level one" in txt or "level 1" in txt:
            result["seller_level"] = "level_one"

        # Media detection
        if soup.find("meta", property="og:image"):
            result["has_image"] = True
        if "video" in r.text.lower():
            result["has_video"] = True

        return result
    except Exception as e:
        result["error"] = str(e)
        return result


# -------------------------------------------------
# Analyzer Logic
# -------------------------------------------------
def keyword_density(text, keywords):
    if not text or not keywords:
        return 0
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0
    total = len(words)
    hits = sum(words.count(k.lower()) for k in keywords)
    return (hits / total) * 100


def analyze_gig_local(gig):
    title = gig.get("title", "") or ""
    description = gig.get("description", "") or ""
    tags = gig.get("tags", []) or []
    primary_keywords = gig.get("primary_keywords", []) or []
    extras = gig.get("extras", {}) or {}

    # --- Scores ---
    title_score = 0
    if 40 <= len(title) <= 80:
        title_score += 30
    elif 25 <= len(title) < 40:
        title_score += 20
    if any(k.lower() in title.lower() for k in primary_keywords):
        title_score += 15
    if title.lower().startswith("i will"):
        title_score += 5
    title_score = max(0, min(title_score, 50))

    desc_score = 0
    word_count = len(description.split())
    density = keyword_density(description, primary_keywords)
    if 150 <= word_count <= 600:
        desc_score += 25
    elif 80 <= word_count < 150:
        desc_score += 15
    if 2 <= density <= 6:
        desc_score += 15
    desc_score = max(0, min(desc_score, 50))

    tag_score = 0
    if len(tags) >= 3:
        tag_score += 20
    if len(tags) >= 5:
        tag_score += 10
    if any(k.lower() in [t.lower() for t in tags] for k in primary_keywords):
        tag_score += 10
    tag_score = min(tag_score, 40)

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
    faq_score = min(faq_score, 60)

    seller_boost = 0
    level = extras.get("seller_level")
    if level == "level_one":
        seller_boost += 5
    elif level == "level_two":
        seller_boost += 10
    elif level == "top_rated":
        seller_boost += 15

    overall = (
        title_score * 0.25 +
        desc_score * 0.3 +
        tag_score * 0.2 +
        faq_score * 0.15 +
        seller_boost * 0.1
    )
    overall = round(min(overall, 100), 1)

    if overall >= 85:
        health = "Perfect"
    elif overall >= 60:
        health = "Good"
    else:
        health = "Needs work"

    recs = []
    if title_score < 40:
        recs.append("Include your main keyword in the gig title.")
    if desc_score < 40:
        recs.append("Write a detailed description (150–300 words).")
    if tag_score < 30:
        recs.append("Use 5 relevant tags with your target keywords.")
    if faq_score < 40:
        recs.append("Add FAQs and gig media (image/video).")

    return {
        "overall_score": overall,
        "health": health,
        "components": {
            "Title Score": title_score,
            "Description Score": desc_score,
            "Tag Score": tag_score,
            "FAQ & Extras Score": faq_score,
            "Seller Boost": seller_boost
        },
        "recommendations": recs,
        "raw": {
            "word_count": word_count,
            "keyword_density": round(density, 2)
        }
    }


# -------------------------------------------------
# Streamlit UI
# -------------------------------------------------
st.set_page_config(page_title="Fiverr Gig SEO Analyzer (v4.2)", layout="wide")
st.title("💡 Fiverr Gig SEO Analyzer (v4.2)")

st.markdown("""
Paste your Fiverr gig URL or fill in the details below.
The tool calculates your **SEO ranking score (0–100)** and shows improvement tips.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ Paste Gig URL (Optional)")
    url = st.text_input("Fiverr Gig URL")
    if st.button("🔗 Fetch from Fiverr"):
        if not url:
            st.warning("Please enter a valid Fiverr URL.")
        else:
            with st.spinner("Fetching gig data..."):
                data = fetch_gig_from_url(url)
            if data.get("error"):
                st.error(data["error"])
            else:
                st.session_state["title"] = data.get("title", "")
                st.session_state["description"] = data.get("description", "")
                st.session_state["tags"] = ", ".join(data.get("tags", []))
                st.session_state["seller_level"] = data.get("seller_level", "none")
                st.success("✅ Gig data fetched successfully!")

    st.write("---")
    st.subheader("2️⃣ Gig Details")
    title = st.text_input("Gig Title", value=st.session_state.get("title", ""))
    description = st.text_area("Gig Description", value=st.session_state.get("description", ""), height=200)
    tags_input = st.text_input("Tags (comma separated)", value=st.session_state.get("tags", ""))
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    keywords_input = st.text_input("Primary Keywords (comma separated)", value=", ".join(tags[:2]))
    primary_keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

with col2:
    st.subheader("3️⃣ Extras / Seller Info")
    has_faqs = st.checkbox("Has FAQs?")
    has_packages = st.checkbox("Has Packages?")
    has_delivery_info = st.checkbox("Has Delivery Info?")
    has_image = st.checkbox("Has Image?")
    has_video = st.checkbox("Has Video?")
    seller_level = st.selectbox("Seller Level", ["none", "level_one", "level_two", "top_rated"])
    completion_rate = st.slider("Completion Rate (%)", 0, 100, 95)

if st.button("🚀 Analyze Gig"):
    gig_data = {
        "title": title,
        "description": description,
        "tags": tags,
        "primary_keywords": primary_keywords,
        "extras": {
            "has_faqs": has_faqs,
            "has_packages": has_packages,
            "has_delivery_info": has_delivery_info,
            "has_image": has_image,
            "has_video": has_video,
            "seller_level": None if seller_level == "none" else seller_level,
            "completion_rate": completion_rate
        }
    }
    result = analyze_gig_local(gig_data)

    st.success(f"✅ SEO Analysis Complete: {result['health']} ({result['overall_score']} / 100)")

    cols = st.columns(3)
    for i, (k, v) in enumerate(result["components"].items()):
        cols[i % 3].metric(k, f"{v}")

    if plt:
        fig, ax = plt.subplots()
        ax.barh(list(result["components"].keys()), list(result["components"].values()))
        ax.set_xlim(0, 100)
        ax.set_xlabel("Score")
        st.pyplot(fig)

    st.subheader("💬 Recommendations")
    for rec in result["recommendations"]:
        st.markdown(f"- {rec}")

    with st.expander("🔎 Raw Details"):
        st.json(result["raw"])
