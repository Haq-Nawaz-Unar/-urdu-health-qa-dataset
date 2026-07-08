"""
generate_qa.py
----------------
raw_data.json (scrape.py ka output) ko chunks mein todta hai, aur har chunk
se Groq API (Qwen model) ke zariye Urdu mein Question-Answer pairs
generate karta hai.

Kaise use karein:
1. pip install groq --break-system-packages
2. Apni Groq API key terminal mein set karein (key: https://console.groq.com/keys):
   Windows (PowerShell):  setx GROQ_API_KEY "apni_key_yahan"
   Mac/Linux:              export GROQ_API_KEY="apni_key_yahan"
   (Ya neeche GROQ_API_KEY variable mein seedha bhi likh sakte hain.)
3. python generate_qa.py
4. Output: qa_dataset.json (question, answer, source_url fields ke sath)
"""

import json
import time
import re
import os

from groq import Groq

# -------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YAHAN_APNI_API_KEY_DALEIN")
MODEL_NAME = "qwen/qwen3.6-27b"
TARGET_QA_COUNT = 20000                  # sir ka diya hua target
QA_PER_CHUNK = 5                         # har chunk se kitne QA pairs
CHUNK_WORD_LIMIT = 150                   # har chunk mein kitne words

client = Groq(api_key=GROQ_API_KEY)


def chunk_text(text: str, word_limit: int = CHUNK_WORD_LIMIT) -> list[str]:
    """Lambe text ko chhote chunks (paragraphs) mein todta hai."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), word_limit):
        chunk = " ".join(words[i:i + word_limit])
        if len(chunk.split()) > 30:   # bohot chhote chunks skip karo
            chunks.append(chunk)
    return chunks


def extract_json_array(raw: str) -> str:
    """
    Raw model output mein se pehla balanced [...] JSON array nikalta hai.
    Simple regex ke bajaye bracket-counting use karta hai, taake reasoning
    model ke izafi text/brackets se confuse na ho.
    """
    start = raw.find("[")
    if start == -1:
        raise ValueError("Response mein koi '[' nahi mila")

    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "[":
            depth += 1
        elif raw[i] == "]":
            depth -= 1
            if depth == 0:
                return raw[start:i + 1]

    raise ValueError("JSON array band (]) nahi hua - shayad response truncate ho gaya")


def call_llm(chunk: str, n_pairs: int = QA_PER_CHUNK, debug: bool = True) -> list[dict]:
    """Ek chunk se Groq (Qwen) ke zariye Q&A pairs banwata hai."""
    prompt = f"""Neeche diye gaye Urdu health paragraph ko parh kar {n_pairs} sawal-jawab
(question-answer) pair banayein. Sirf usi paragraph ki maloomat use karein,
bahar se kuch na milayein. Sawal awam ke andaz mein hon (jese koi mareez
ya aam insan poochta hai), aur jawab mukhtasar aur saaf Urdu mein hon.

Apna jawab SIRF neeche di gayi JSON array format mein dein. Koi tashreeh,
koi extra jumla, koi <think> tag, koi ```json``` fencing na likhein - bas
seedha [ se shuru aur ] pe khatam hone wala array:
[
  {{"question": "...", "answer": "..."}},
  ...
]

Paragraph:
\"\"\"{chunk}\"\"\"
"""
    raw = ""
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_completion_tokens=4096,
            top_p=0.95,
            reasoning_effort="none",   # reasoning off - seedha jawab, JSON saaf rehta hai
            stream=True,
            stop=None,
        )

        # Stream true hai, isliye chunks ko jama karke poora response banate hain
        for part in completion:
            delta = part.choices[0].delta.content
            if delta:
                raw += delta

        raw = raw.strip()

        # Model kabhi kabhi <think>...</think> mein reasoning likh deta hai, hata dein
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # ```json ... ``` fencing hata dein
        raw = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()

        json_str = extract_json_array(raw)
        pairs = json.loads(json_str)
        return pairs

    except Exception as e:
        print(f"[ERROR generating QA] {e}")
        if debug:
            print(f"[DEBUG raw response preview] {raw[:300]}\n")
        return []


def main():
    with open("raw_data.json", "r", encoding="utf-8") as f:
        articles = json.load(f)

    if not articles:
        print("raw_data.json khali hai! Pehle scrape.py chalayein.")
        return

    qa_dataset = []

    for article in articles:
        chunks = chunk_text(article["text"])
        for chunk in chunks:
            if len(qa_dataset) >= TARGET_QA_COUNT:
                break

            pairs = call_llm(chunk)
            for pair in pairs:
                if "question" in pair and "answer" in pair:
                    qa_dataset.append({
                        "question": pair["question"],
                        "answer": pair["answer"],
                        "source_url": article["url"],
                    })

            print(f"Total QA pairs so far: {len(qa_dataset)}")
            time.sleep(1.0)  # API rate limit se bachne ke liye

        if len(qa_dataset) >= TARGET_QA_COUNT:
            break

    with open("qa_dataset.json", "w", encoding="utf-8") as f:
        json.dump(qa_dataset, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(qa_dataset)} QA pairs saved to qa_dataset.json")


if __name__ == "__main__":
    main()