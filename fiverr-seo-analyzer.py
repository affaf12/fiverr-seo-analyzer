"""
app.py
Streamlit Fiverr Gig SEO Analyzer (v3.1)
Author: Muhammad Affaf
License: MIT
"""

import re
import streamlit as st

# Optional import — matplotlib only if available
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# -------------------------------------------------
# HELPER FUNCTIONS
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


def analyze_gig(gig):
    title = gig.get("title", "")
    description = gig.get("description", "")
    tags = gig.get("tags", [])
    primary_keywords = gig.get("primary_keywords", [])
    extras = gig.get("extras", {})

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
    if re.search(r"[!?.]", title):
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

    # ----------------------- RECOMMENDATIONS -----------------------
    recs = []
    if title_score < 40:
        recs.append("Improve your gig title — include 1–2 keywords naturally.")
    if desc_score < 40:
        recs.append("Add more detail and structure to your gig description.")
    if tag_score < 30:
        recs.append("Use 5 relevant tags closely related to your keywords.")
    if faq_score < 40:
        recs.append("Add FAQs, media, and ensure all gig extras are filled.")
    if overall >= 85:
        recs.append("Excellent SEO! Your gig is highly optimized for ranking.")

    return {
        "overall_score": overall,
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
st.set_page_config(page_title="Fiverr Gig SEO Analyzer", layout="wide")

st.title("💡 Fiverr Gig SEO Analyzer (v3.1)")
st.markdown(
    """
Analyze your Fiverr gig and get a **0–100 SEO score** based on title, description, tags, FAQs, and seller performance.  
Designed to help you **rank higher** on Fiverr search results 🚀
"""
)

# -------------------------- FORM --------------------------
with st.form("gig_form"):
    st.subheader("📝 Enter Your Gig Details")

    title = st.text_input("Gig Title", placeholder="e.g., I will design modern Power BI dashboards for business insights")
    description = st.text_area("Gig Description", placeholder="Write your gig description here...", height=200)
    tags_input = st.text_input("Tags (comma separated)", placeholder="power bi, dashboard, data visualization")
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    primary_keywords_input = st.text_input("Primary Keywords (comma separated)", placeholder="power bi, dashboard")
    primary_keywords = [k.strip() for k in primary_keywords_input.split(",") if k.strip()]

    st.markdown("### ⚙️ Gig Extras")
    col1, col2, col3 = st.columns(3)
    with col1:
        has_faqs = st.checkbox("Has FAQs?")
        has_packages = st.checkbox("Has Packages?")
        has_delivery_info = st.checkbox("Has Delivery Info?")
    with col2:
        has_image = st.checkbox("Has Image?")
        has_video = st.checkbox("Has Video?")
        image_contains_text = st.checkbox("Image Contains Text?")
    with col3:
        seller_level = st.selectbox("Seller Level", ["none", "level_one", "level_two", "top_rated"], index=0)
        response_time = st.number_input("Response Time (hours)", min_value=0, max_value=72, value=4)
        completion_rate = st.slider("Completion Rate (%)", 0, 100, 90)

    submitted = st.form_submit_button("🔍 Analyze Gig")

# -------------------------- RESULTS --------------------------
if submitted:
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
            "image_contains_text": image_contains_text,
            "seller_level": None if seller_level == "none" else seller_level,
            "response_time_hours": response_time,
            "completion_rate": completion_rate
        }
    }

    result = analyze_gig(gig_data)
    st.success("✅ Analysis Completed!")

    # --- Metrics Dashboard ---
    st.subheader("📊 Fiverr SEO Breakdown")
    cols = st.columns(3)
    metrics = list(result["components"].items())
    for i, (name, score) in enumerate(metrics):
        cols[i % 3].metric(name, f"{score}")

    # --- Chart (optional if matplotlib available) ---
    if plt:
        st.markdown("### 📈 SEO Component Comparison")
        fig, ax = plt.subplots()
        labels = list(result["components"].keys())
        scores = list(result["components"].values())
        ax.barh(labels, scores)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Score")
        ax.set_title("Fiverr SEO Component Scores")
        st.pyplot(fig)

    # --- Recommendations ---
    st.write("### 💬 Recommendations")
    if result["recommendations"]:
        for i, r in enumerate(result["recommendations"], 1):
            st.markdown(f"**{i}.** {r}")
    else:
        st.success("Your gig looks perfectly optimized!")

    with st.expander("🔍 Debug Info"):
        st.json(result["raw"])
