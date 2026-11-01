from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import re
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# -------- PYDANTIC MODELS (Frontend se aane wala data) --------
class Extras(BaseModel):
    has_faqs: bool = False
    has_packages: bool = False
    has_delivery_info: bool = False
    has_image: bool = False
    has_video: bool = False
    image_contains_text: bool = False
    seller_level: Optional[str] = None
    response_time_hours: int = 24
    completion_rate: int = 100

class GigData(BaseModel):
    title: str = ""
    description: str = ""
    tags: List[str] = []
    primary_keywords: List[str] = []
    extras: Extras = Extras()

# -------- HELPER FUNCTIONS (Aapke purane code se) --------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
}

def keyword_density(text, keywords):
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
        phrase = k.lower().split()
        if len(phrase) == 1:
            hits += words.count(phrase[0])
        else:
            hits += len(re.findall(r"\b" + re.escape(" ".join(phrase)) + r"\b", text.lower()))
    return (hits / total) * 100

# -------- MAIN ANALYSIS LOGIC --------
def analyze_gig_local(gig: GigData):
    title = gig.title.strip()
    description = gig.description.strip()
    tags = gig.tags
    primary_keywords = [k.strip() for k in gig.primary_keywords if k.strip()]
    extras = gig.extras

    # ---------- Title score (0-30) ----------
    title_score = 0
    title_len = len(title)
    if 40 <= title_len <= 80:
        title_score += 18
    elif 25 <= title_len < 40:
        title_score += 12
    elif title_len > 80:
        title_score += 10
    else:
        title_score += 6

    if any(k.lower() in title.lower() for k in primary_keywords):
        title_score += 8
    if title.lower().startswith("i will") or title.lower().startswith("i'll") or title.lower().startswith("i can"):
        title_score += 4

    title_score = max(0, min(title_score, 30))

    # ---------- Description score (0-30) ----------
    desc_score = 0
    words = re.findall(r"\w+", description)
    word_count = len(words)
    density = keyword_density(description, primary_keywords)

    if 180 <= word_count <= 450:
        desc_score += 16
    elif 120 <= word_count < 180:
        desc_score += 12
    elif 60 <= word_count < 120:
        desc_score += 6

    if 1.5 <= density <= 5:
        desc_score += 10
    elif 0.5 <= density < 1.5:
        desc_score += 6
    elif density > 5:
        desc_score += 4

    if "\n" in description or "-" in description or "*" in description:
        desc_score += 4

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

    # ---------- Extras score (0-10) ----------
    extras_score = 0
    if extras.has_image: extras_score += 3
    if extras.has_video: extras_score += 4
    if extras.has_faqs: extras_score += 2
    if extras.has_packages: extras_score += 1
    extras_score = max(0, min(extras_score, 10))

    # ---------- Seller boost (0-10) ----------
    seller_boost = 0
    if extras.seller_level == "top_rated": seller_boost += 8
    elif extras.seller_level == "level_two": seller_boost += 5
    elif extras.seller_level == "level_one": seller_boost += 3
    
    if extras.completion_rate >= 95: seller_boost += 2
    if extras.response_time_hours <= 4: seller_boost += 2
    seller_boost = max(0, min(seller_boost, 10))

    # ---------- Engagement (0-5) ----------
    engagement = 0
    if any(k.lower() in title.lower() for k in ["power bi", "dashboard", "data", "analytics", "visualization"]):
        engagement += 2
    if word_count >= 200 and word_count <= 450:
        engagement += 2
    if extras.has_video:
        engagement += 1
    engagement = min(engagement, 5)

    # ---------- Overall ----------
    overall = (
        title_score * 0.28 +
        desc_score * 0.32 +
        tag_score * 0.18 +
        extras_score * 0.1 +
        seller_boost * 0.08 +
        engagement
    )
    overall = round(min(overall, 100), 1)

    if overall >= 85: health = "Perfect"
    elif overall >= 65: health = "Good"
    else: health = "Needs work"

    # ---------- Recommendations ----------
    recs = []
    if title_score < 20:
        recs.append("Improve title: include 1–2 primary keywords early and a clear benefit.")
    elif title_score < 26:
        recs.append("Polish title for clarity & keyword placement to increase CTR (aim 40–80 characters).")

    if desc_score < 18:
        recs.append("Expand description to 150–300 words, use bullets for deliverables, and include a clear CTA.")
    if density < 1.0 and primary_keywords:
        recs.append(f"Keyword density is low ({round(density,2)}%). Mention your primary keywords more naturally.")
    if density > 6:
        recs.append(f"Keyword density is high ({round(density,2)}%). Reduce repetition.")

    if tag_score < 12:
        recs.append("Add 4–6 focused tags that exactly match phrases buyers search for.")

    if extras_score < 6:
        recs.append("Add a high-quality gig image and consider a short gig video.")
    if not extras.has_faqs:
        recs.append("Add 2–4 FAQs to address common buyer questions.")

    if seller_boost < 4:
        recs.append("Improve seller signals: faster response time and high completion rate.")

    suggested_title = None
    if primary_keywords:
        main_kw = primary_keywords[0]
        if main_kw.lower() not in title.lower():
            suggested_title = f"I will {title[:60]} for {main_kw}".strip() if title else f"I will create {main_kw}"

    return {
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

# -------- API ENDPOINTS --------
@app.post("/api/analyze")
def api_analyze_gig(data: GigData):
    result = analyze_gig_local(data)
    return result

@app.post("/api/fetch-fiverr")
def api_fetch_fiverr(url_data: dict):
    url = url_data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    result = {"title": "", "description": "", "tags": [], "has_image": False, "has_video": False, "seller_level": "none"}
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            title_tag = soup.find("meta", property="og:title")
            if title_tag: result["title"] = title_tag["content"].strip()
            
            desc_tag = soup.find("meta", property="og:description")
            if desc_tag: result["description"] = desc_tag["content"].strip()
            
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords:
                result["tags"] = [t.strip() for t in meta_keywords["content"].split(",") if t.strip()]
            
            if soup.find("meta", property="og:image"): result["has_image"] = True
            if "video" in r.text.lower(): result["has_video"] = True
            
            txt = soup.get_text(separator=" ", strip=True).lower()
            if "top rated seller" in txt: result["seller_level"] = "top_rated"
            elif "level two" in txt or "level 2" in txt: result["seller_level"] = "level_two"
            elif "level one" in txt or "level 1" in txt: result["seller_level"] = "level_one"
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
