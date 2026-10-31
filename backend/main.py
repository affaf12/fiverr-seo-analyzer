
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Yeh structure batata hai ke frontend se kya data aayega
class GigData(BaseModel):
    title: str
    description: str
    tags: str

# Yeh hamara API endpoint hai
@app.post("/api/analyze")
def analyze_gig(data: GigData):
    # Yahan aap apna purana scoring logic dalenge (abhi ke liye basic example)
    score = 0
    feedback = []
    
    # Title check
    if len(data.title) > 10:
        score += 30
        feedback.append("Title achi hai!")
    else:
        feedback.append("Title bohot choti hai, kam az kam 10 characters likhein.")
        
    # Description check
    if len(data.description) > 50:
        score += 40
        feedback.append("Description achi hai.")
    else:
        feedback.append("Description mein mazeed tafseel likhein.")
        
    # Tags check
    if len(data.tags.split(',')) >= 3:
        score += 30
        feedback.append("Tags sahi hain.")
    else:
        feedback.append("Kam az kam 3 tags dalein.")
        
    return {
        "score": score,
        "feedback": feedback
    }
