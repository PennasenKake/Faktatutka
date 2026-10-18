# diagnose_bm25_fp.py
# Kertaluonteinen diagnoosi: MIKSI "Marsissa asuu vihreitä pikku-ukkoja"
# saa ei-nollia pisteita oikealla 208 artikkelin korpuksella, vaikka
# mikaan artikkeli ei liity Marsiin. Ei osa toimitettavaa koodia.
#
# HUOM Claudelta: en pääse ajamaan tätä itse (ei oikeaa korpusta/indeksiä
# tässä ympäristössä). Aja koneellasi faktatutka-kansiossa, liitä tuloste
# takaisin.
import json
import re
from collections import Counter
from pathlib import Path

from rag.index import load_index, search, tokenize

ROOT = Path(__file__).resolve().parent  # aja tama faktatutka-kansiosta

QUERY = "Marsissa asuu vihreitä pikku-ukkoja"
query_tokens = tokenize(QUERY)
print(f"Kyselyn tokenit: {query_tokens}\n")

bm25, metadata = load_index(ROOT / "rag" / "bm25_index.pkl")

with open(ROOT / "faktabaari_corpus.json", "r", encoding="utf-8") as f:
    articles = json.load(f)["articles"]
body_by_url = {a["url"]: a["body_text"] for a in articles}

results = search(bm25, metadata, QUERY, top_k=5)
print("Top 5 tulosta:")
for r in results:
    print(f"  {r['score']:6.2f}  {r['title']}")
print()

# Montako kertaa koko korpuksessa (208 artikkelia) kukin kyselyn token
# esiintyy kirjaimellisesti - paljastaa onko sana geneerinen vai aidosti
# harvinainen.
print("Kyselyn tokenien yleisyys koko korpuksessa (kuinka monessa\n"
      "208 artikkelista token esiintyy >=1 kertaa):")
for tok in set(query_tokens):
    count = sum(1 for body in body_by_url.values() if tok in tokenize(body))
    print(f"  {tok!r}: {count}/208 artikkelissa")
print()

# Mista tokeneista top-2 tuloksen pisteet oikeasti koostuvat
print("Top 2 tuloksen tokenitason erittely:")
for r in results[:2]:
    url = r["url"]
    body = body_by_url.get(url, "")
    body_tokens = Counter(tokenize(body))
    print(f"\n  {r['title']!r} (score {r['score']:.2f}):")
    for tok in query_tokens:
        hits = body_tokens.get(tok, 0)
        if hits:
            print(f"    tapaus: {tok!r} esiintyy {hits}x tassa artikkelissa")
