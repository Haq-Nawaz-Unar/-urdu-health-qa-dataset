# Urdu Health Question-Answer Dataset — Project Steps

## Pipeline (jo sir chahte hain: Extract → RAG → Streamlit/Gradio)

### Step 1 — Extract (scrape.py)
1. `pip install requests beautifulsoup4 --break-system-packages`
2. `scrape.py` file kholein, `URLS` list mein Urdu health websites ke
   article links dalein (jitne zyada, utna behtar — 100-300 articles
   se acha data milega).
3. `python scrape.py` chalayein → `raw_data.json` banega.

**Suggested Urdu health sources** (khud jaake check kar lein ke scraping
allowed hai ya nahi, aur robots.txt respect karein):
- BBC Urdu — Health section
- Jang.com.pk — Health section
- Hum Urdu — Health articles
- Dawn Urdu — Health section
- Koi Pakistani hospital/NGO ki Urdu website (Aga Khan, Indus Hospital
  awam-friendly health guides)

### Step 2 — Q&A Generate (generate_qa.py)
1. `pip install google-generativeai --break-system-packages`
2. Free Gemini API key banayein: https://aistudio.google.com/apikey
3. `generate_qa.py` mein `GEMINI_API_KEY` dalein.
4. `python generate_qa.py` chalayein → `qa_dataset.json` banega
   (target 20,000 QA pairs, script khud track karti hai).

⚠️ Note: 20k tak pahonchne ke liye kaafi raw text chahiye hoga
(andaza: ~4000 chunks agar 5 QA/chunk). Agar articles kam hain to
Step 1 mein aur zyada URLs add karein.

### Step 3 — Quality check
- `qa_dataset.json` mein se random 100-200 pairs nikal ke khud
  parh lein, ghalat/bekar jawab hatayein. (Sir ko ye zaroor
  achha lagega ke aapne manually verify kiya hai.)

### Step 4 — RAG system banana (agla step)
- `qa_dataset.json` (ya raw chunks) ko embeddings mein convert karke
  FAISS/ChromaDB mein store karna
- User question aane par relevant chunks retrieve karna
- LLM se un chunks ke base pe Urdu jawab generate karwana

### Step 5 — Streamlit/Gradio UI
- Simple chat interface banake RAG system ko demo ke liye deploy karna

---
**Agla step jo main bana sakta hoon:** RAG (Step 4) ka code aur
Streamlit chat interface (Step 5) — jab aap ka `qa_dataset.json`
tayyar ho jaye, mujhe bata dein, main wo bhi bana doonga.