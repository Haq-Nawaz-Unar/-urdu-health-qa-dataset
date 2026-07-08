"""
clean_dataset.py
------------------
Purane qa_dataset.json mein se "echo/circular" jawab wale ghalat pairs
hataata hai - jese Q: "kya X faidemand hai?" A: "haan, X faidemand hai"
(jahan jawab sirf sawal ko dobara keh raha ho, koi nayi maloomat na de).

Kaise use karein:
1. python clean_dataset.py
2. Output: qa_dataset_clean.json (saaf pairs) + qa_dataset_removed.json
   (jo hataye gaye, taake aap khud bhi check kar sakein)

Ye original qa_dataset.json ko nahi badalta - safe hai.
"""

import json
import re

INPUT_FILE = "qa_dataset.json"
CLEAN_FILE = "qa_dataset_clean.json"
REMOVED_FILE = "qa_dataset_removed.json"

# Yes/No jawab ki shuruaat mein aane wale common Urdu words
YES_NO_STARTERS = ["ہاں", "جی ہاں", "نہیں", "بے شک", "یقیناً", "جی نہیں"]


def normalize(text: str) -> str:
    """Punctuation/spaces hata ke comparison ke liye text saaf karta hai."""
    text = re.sub(r"[،۔؟!٫٬\s]+", " ", text)
    return text.strip()


def is_circular(question: str, answer: str) -> bool:
    """
    Check karta hai ke jawab sirf sawal ko dobara repeat kar raha hai
    (yes/no ke sath) ya asal mein nayi maloomat de raha hai.
    """
    norm_q = normalize(question)
    norm_a = normalize(answer)

    # Agar jawab yes/no se shuru hota hai
    starts_yes_no = any(norm_a.startswith(starter) for starter in YES_NO_STARTERS)
    if not starts_yes_no:
        return False

    # Yes/No hata ke dekhte hain baqi jawab sawal se kitna similar hai
    remainder = norm_a
    for starter in YES_NO_STARTERS:
        remainder = remainder.replace(starter, "", 1).strip()

    # Agar bacha hua jawab bohot chhota hai (jese sirf "،" ya khaali)
    if len(remainder) < 8:
        return True

    # Agar bacha hua jawab sawal ke alfaaz se 70%+ overlap karta hai,
    # to ye sirf sawal ka echo hai, nayi maloomat nahi
    q_words = set(norm_q.replace("؟", "").split())
    a_words = set(remainder.split())
    if not q_words:
        return False

    overlap = len(q_words & a_words) / len(q_words)
    return overlap >= 0.6


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    clean = []
    removed = []

    for pair in dataset:
        q = pair.get("question", "")
        a = pair.get("answer", "")
        if is_circular(q, a):
            removed.append(pair)
        else:
            clean.append(pair)

    with open(CLEAN_FILE, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)

    with open(REMOVED_FILE, "w", encoding="utf-8") as f:
        json.dump(removed, f, ensure_ascii=False, indent=2)

    print(f"Total pairs: {len(dataset)}")
    print(f"Clean (kept): {len(clean)} -> {CLEAN_FILE}")
    print(f"Removed (circular/echo): {len(removed)} -> {REMOVED_FILE}")
    print("\nTip: qa_dataset_removed.json khol ke khud check kar lein ke")
    print("kahin theek pairs galti se na hat gaye hon.")


if __name__ == "__main__":
    main()