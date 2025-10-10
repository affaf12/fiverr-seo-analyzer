"""
app.py
Fiverr Gig SEO Analyzer (v5.0 - Pro)
Author: Muhammad Affaf
License: MIT

Features:
- Paste Fiverr gig URL (best-effort fetch) OR manually enter gig fields
- SEO scoring (Title, Description, Tags, Extras, Seller)
- Smart, dynamic recommendations
- Plotly radar + bar chart visualization (interactive)
- Downloadable JSON report
- Polished Streamlit UI
"""

import re
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup

# Optional plotting libraries
try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

# -------- CONFIG / CONSTANTS --------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
}

# -------- HELPERS: FETCHING --------
def fetch_gig_from_url(url, timeout=10):
    """
    Best-effort fetch for publicly available Fiverr gig pages.
    Extracts og:title, og:description, meta keywords and some heuristics.
    Returns dict with fields or error.
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

        # Tags (meta keywords)
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            tags = [t.strip() for t in meta_keywords["content"].split(",") if t.strip()]
            result["tags"].extend(tags)

        # Heuristic tag scraping (best-effort)
        potential_tags = set()
        for el in soup.select("a, span, div"):
            txt = el.get_text(separator=" ", strip=True)
            if not txt or len(txt) > 40:
                continue
            if re.match(r"^[A-Za-z0-9\s\-\&]{2,30}$", txt):
                banned = ("read more", "reviews", "about", "see more", "view profile")
                if txt.lower() not in banned and len(txt.split()) <= 3:
                    potential_tags.add(txt)
        for t in list(potential_tags)[:8]:
            if t.lower() not in [x.lower() for x in result["tags"]]:
                result["tags"].append(t)

        # Seller level detection
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
        if "video" in r.text.lower() or soup.find("meta", property="og:video"):
            result["has_video"] = True

        return result
    except Exception as e:
        result["error"] = str(e)
        result["raw_html_snippet"] = (r.text[:2000] if 'r' in locals() and getattr(r, 'text', None) else None)
        return result

# -------- HELPERS: ANALYSIS LOGIC --------
def keyword_density(text, keywords):
    """Return percent keyword density (0..100)."""
    if not text or not keywords:
        return 0.0
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0.0
    total = len(words)
    hits = 0
    for k in keywords:
        if not k:
            continue
        # count occurrences of keyword tokens (exact token or phrase tokens)
        phrase = k.lower().split()
        if len(phrase) == 1:
            hits += words.count(phrase[0])
        else:
            # phrase count: approximate by joining and searching
            hits += len(re.findall(r"\b" + re.escape(" ".join(phrase)) + r"\b", text.lower()))
    return (hits / total) * 100

def analyze_gig_local(gig):
    """
    Input gig dict:
      title, description, tags(list), primary_keywords(list), extras(dict)
    Output: analysis dict with component scores, overall, health, recs, raw
    """
    title = (gig.get("title") or "").strip()
    description = (gig.get("description") or "").strip()
    tags = gig.get("tags") or []
    primary_keywords = gig.get("primary_keywords") or []
    extras = gig.get("extras") or {}

    # normalize keywords: remove empties
    primary_keywords = [k for k in (pk.strip() for pk in primary_keywords) if k]

    # ---------- Title score (0-30 scaled into component max 30) ----------
    title_score = 0
    title_len = len(title)
    if 40 <= title_len <= 80:
        title_score += 18
    elif 25 <= title_len < 40:
        title_score += 12
    elif title_len > 80:
        title_score += 10
    else:
        title_score += 6  # short title gets little points

    # keyword presence in title
    if any(k.lower() in title.lower() for k in primary_keywords):
        title_score += 8
    # action verb presence
    if title.lower().startswith("i will") or title.lower().startswith("i'll") or title.lower().startswith("i can"):
        title_score += 4

    title_score = max(0, min(title_score, 30))

    # ---------- Description score (0-30) ----------
    desc_score = 0
    words = re.findall(r"\w+", description)
    word_count = len(words)
    density = keyword_density(description, primary_keywords)

    # length
    if 180 <= word_count <= 450:
        desc_score += 16
    elif 120 <= word_count < 180:
        desc_score += 12
    elif 60 <= word_count < 120:
        desc_score += 6

    # density best range 1.5% - 5%
    if 1.5 <= density <= 5:
        desc_score += 10
    elif 0.5 <= density < 1.5:
        desc_score += 6
    elif density > 5:
        desc_score += 4  # too many repeats is suspicious

    # structure (bullets/newlines)
    if "\n" in description or "-" in description or "*" in description:
        desc_score += 4

    # CTA presence
    if re.search(r"\b(order|message|contact|hire|dm|start|get)\b", description.lower()):
        desc_score += 4

    desc_score = max(0, min(desc_score, 30))

    # ---------- Tags score (0-20) ----------
    tag_score = 0
    num_tags = len(tags)
    if 3 <= num_tags <= 7:
        tag_score += 10
    elif num_tags > 7:
        tag_score += 12
    if any(k.lower() in [t.lower() for t in tags] for k in primary_keywords):
        tag_score += 8
    tag_score = max(0, min(tag_score, 20))

    # ---------- Extras / Media / FAQs (0-10) ----------
    extras_score = 0
    if extras.get("has_image"):
        extras_score += 3
    if extras.get("has_video"):
        extras_score += 4
    if extras.get("has_faqs"):
        extras_score += 2
    if extras.get("has_packages"):
        extras_score += 1
    extras_score = max(0, min(extras_score, 10))

    # ---------- Seller boost (0-10) ----------
    seller_boost = 0
    level = extras.get("seller_level")
    if level == "top_rated":
        seller_boost += 8
    elif level == "level_two":
        seller_boost += 5
    elif level == "level_one":
        seller_boost += 3
    # completion and response
    completion_rate = extras.get("completion_rate", 100)
    if completion_rate >= 95:
        seller_boost += 2
    if extras.get("response_time_hours", 24) <= 4:
        seller_boost += 2
    seller_boost = max(0, min(seller_boost, 10))

    # ---------- Engagement simulation (small bonus 0-5) ----------
    engagement = 0
    if any(k.lower() in title.lower() for k in ["power bi", "dashboard", "data", "analytics", "visualization"]):
        engagement += 2
    if word_count >= 200 and word_count <= 450:
        engagement += 2
    if extras.get("has_video"):
        engagement += 1
    engagement = min(engagement, 5)

    # ---------- Weighted overall ----------
    # Increase title importance slightly (CTR) and keep description high
    overall = (
        title_score * 0.28 +
        desc_score * 0.32 +
        tag_score * 0.18 +
        extras_score * 0.1 +
        seller_boost * 0.08 +
        engagement
    )
    overall = round(min(overall, 100), 1)

    # Health label
    if overall >= 85:
        health = "Perfect"
    elif overall >= 65:
        health = "Good"
    else:
        health = "Needs work"

    # ---------- Smart recommendations ----------
    recs = []
    # Title suggestions
    if title_score < 20:
        recs.append("Improve title: include 1–2 primary keywords early and a clear benefit (e.g., 'I will design responsive Power BI dashboards').")
    elif title_score < 26:
        recs.append("Polish title for clarity & keyword placement to increase CTR (aim 40–80 characters).")

    # Description suggestions
    if desc_score < 18:
        recs.append("Expand description to 150–300 words, use bullets for deliverables, and include a clear CTA (e.g., 'Message me to start').")
    if density < 1.0 and primary_keywords:
        recs.append(f"Keyword density is low ({round(density,2)}%). Mention your primary keyword(s) {', '.join(primary_keywords)} 2–4 more times naturally.")
    if density > 6:
        recs.append(f"Keyword density is high ({round(density,2)}%). Reduce repetition and focus on readability.")

    # Tags suggestions
    if tag_score < 12:
        recs.append("Add 4–6 focused tags that exactly match phrases buyers search for (use keywords and close variations).")

    # Extras suggestions
    if extras_score < 6:
        recs.append("Add a high-quality gig image and consider a short gig video — visuals boost CTR dramatically.")
    if not extras.get("has_faqs"):
        recs.append("Add 2–4 FAQs to address common buyer questions and increase conversions.")

    # Seller suggestions
    if seller_boost < 4:
        recs.append("Improve seller signals: faster response time and high completion rate improve rank over time.")

    # Auto-suggest title (simple heuristic)
    suggested_title = None
    if primary_keywords:
        main_kw = primary_keywords[0]
        # if title missing main keyword, suggest one
        if main_kw.lower() not in title.lower():
            prefix = "I will "
            tail = f"for {main_kw}" if main_kw else ""
            short_title = title if title else f"{prefix}create {main_kw}"
            suggested_title = f"{prefix}{short_title[:60]} {tail}".strip()

    analysis = {
        "overall_score": overall,
        "health": health,
        "components": {
            "Title Score": round(title_score, 1),
            "Description Score": round(desc_score, 1),
            "Tag Score": round(tag_score, 1),
            "Extras Score": round(extras_score, 1),
            "Seller Boost": round(seller_boost, 1),
            "Engagement": round(engagement, 1)
        },
        "primary_keywords_used": [k for k in primary_keywords if k.lower() in (title + " " + description).lower()],
        "recommendations": recs,
        "suggested_title": suggested_title,
        "raw": {
            "word_count": word_count,
            "keyword_density_pct": round(density, 3),
            "title_len": title_len,
            "tags_count": len(tags)
        }
    }
    return analysis

# -------- UI: Streamlit --------
st.set_page_config(page_title="Fiverr Gig SEO Analyzer (v5.0)", layout="wide")
st.title("💡 Fiverr Gig SEO Analyzer — v5.0 (Pro)")

st.markdown(
    """
Paste a Fiverr gig URL (optional) to auto-fill fields, or enter fields manually.
The analyzer provides a **0–100 SEO score**, component breakdown, smart recommendations,
interactive radar chart, and downloadable JSON report.
"""
)

# Layout: left = inputs, right = results / actions
left, right = st.columns([1, 1])

with left:
    st.header("1) Fetch or Enter Gig")
    url = st.text_input("Fiverr Gig URL (optional)", placeholder="https://www.fiverr.com/username/gig-title")
    if st.button("🔗 Fetch from Fiverr"):
        if not url:
            st.warning("Please enter a Fiverr gig URL first.")
        else:
            with st.spinner("Fetching... (best-effort)"):
                fetched = fetch_gig_from_url(url)
            if fetched.get("error"):
                st.error(f"Fetch error: {fetched['error']}")
                if fetched.get("raw_html_snippet"):
                    st.info("Partial page snippet available for debugging.")
                    st.code(fetched["raw_html_snippet"][:600])
                st.session_state['fetched'] = None
            else:
                st.success("Fetched! Fields prefilled below.")
                st.session_state['fetched'] = fetched
                # prefill
                st.session_state['title_prefill'] = fetched.get("title") or ""
                st.session_state['desc_prefill'] = fetched.get("description") or ""
                st.session_state['tags_prefill'] = ", ".join(fetched.get("tags", []))
                st.session_state['seller_prefill'] = fetched.get("seller_level") or "none"

    st.markdown("---")
    st.subheader("Gig Details")
    title = st.text_input("Gig Title", value=st.session_state.get('title_prefill', ""))
    description = st.text_area("Gig Description", value=st.session_state.get('desc_prefill', ""), height=220)
    tags_input = st.text_input("Tags (comma separated)", value=st.session_state.get('tags_prefill', ""))
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]

    primary_input = st.text_input("Primary Keywords (comma separated)", value=", ".join(tags[:2]))
    primary_keywords = [k.strip() for k in primary_input.split(",") if k.strip()]

    st.markdown("---")
    st.subheader("Extras / Seller Info")
    col_a, col_b = st.columns(2)
    with col_a:
        has_faqs = st.checkbox("Has FAQs?", value=False)
        has_packages = st.checkbox("Has Packages?", value=False)
        has_delivery_info = st.checkbox("Has Delivery Info?", value=False)
    with col_b:
        has_image = st.checkbox("Has Image?", value=bool(st.session_state.get('tags_prefill')))
        has_video = st.checkbox("Has Video?", value=False)
        image_contains_text = st.checkbox("Image contains text?", value=False)

    seller_level = st.selectbox("Seller Level", ["none", "level_one", "level_two", "top_rated"], index=0 if not st.session_state.get('seller_prefill') else ["none", "level_one", "level_two", "top_rated"].index(st.session_state.get('seller_prefill')))
    response_time = st.number_input("Response time (hours)", min_value=0, max_value=72, value=4)
    completion_rate = st.slider("Completion rate (%)", 0, 100, 95)

    analyze_btn = st.button("🚀 Analyze Gig")

with right:
    st.header("Results & Actions")
    st.info("Run analysis from the left panel. Results appear below.")

# When Analyze clicked
if analyze_btn:
    with st.spinner("Analyzing..."):
        gig_payload = {
            "title": title,
            "description": description,
            "tags": tags,
            "primary_keywords": primary_keywords or tags[:2],
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

        analysis = analyze_gig_local(gig_payload)

    # Top summary
    st.subheader("🎯 Summary")
    st.metric("Overall SEO Score", f"{analysis['overall_score']} / 100", delta=None)
    st.write(f"**Health:** {analysis['health']}")
    st.write(f"**Primary keywords detected in text:** {', '.join(analysis['primary_keywords_used']) or '—'}")
    st.write("---")

    # Components — cards / metrics
    comps = analysis['components']
    cols = st.columns(3)
    keys = list(comps.keys())
    for i, k in enumerate(keys):
        cols[i % 3].metric(k, f"{comps[k]}")

    # Visualization: radar via Plotly if available, else matplotlib bar
    st.markdown("### Visual: Component Comparison")
    labels = list(comps.keys())
    values = list(comps.values())

    if go:
        # radar needs loop to close the polygon
        radar_vals = values + [values[0]]
        radar_labels = labels + [labels[0]]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=radar_vals, theta=radar_labels, fill="toself", name="Scores"))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0,100], visible=True)), showlegend=False, margin=dict(t=20,b=10,l=10,r=10), height=420)
        st.plotly_chart(fig, use_container_width=True)
    elif plt:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.barh(labels, values)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Score")
        ax.set_title("Component Scores")
        st.pyplot(fig)
    else:
        st.write("Install `plotly` or `matplotlib` to see charts.")

    st.markdown("### 🔧 Smart Recommendations")
    for i, rec in enumerate(analysis['recommendations'], 1):
        st.markdown(f"**{i}.** {rec}")

    if analysis.get("suggested_title"):
        st.markdown("### ✍️ Suggested Title (quick tweak)")
        st.code(analysis["suggested_title"])

    # Download JSON report
    st.markdown("---")
    st.download_button(
        label="⬇️ Download SEO Report (JSON)",
        data=json.dumps({"input": gig_payload, "analysis": analysis}, indent=2),
        file_name="fiverr_seo_report.json",
        mime="application/json"
    )

    # Quick actionable checklist
    st.markdown("### ✅ Quick Action Checklist")
    st.markdown("- Put the primary keyword within the first 8–12 words of the title.")
    st.markdown("- Expand description to 150–300 words, use bullets, and add a CTA.")
    st.markdown("- Use 4–6 specific tags matching buyer search terms.")
    st.markdown("- Add a high-quality image and a short gig video if possible.")
    st.markdown("- Keep response time low (<4h) and completion rate high (>95%).")

    # Debug raw
    with st.expander("🔎 Raw analysis data (debug)"):
        st.json(analysis["raw"])
