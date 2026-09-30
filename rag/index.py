# rag/index.py
# Rakentaa BM25-hakuindeksin Faktabaari-korpuksesta (kerros 4, tehtava 4.3).
#
# HUOM: tehtavalistan alkuperainen 4.3 ehdotti suoraan embeddaus-skriptia
# (all-MiniLM-L6-v2). Korjattu 4.1-paatoksen mukaiseksi: BM25 ensin,
# koska korpus on pieni (208 dokumenttia) ja embeddaus lisaisi
# monimutkaisuutta jota ei ole viela osoitettu tarpeelliseksi - ja koska
# all-MiniLM-L6-v2 ei ole monikielinen (ei tue suomea kunnolla), mika
# olisi toistanut kerroksen 1 ISOT/FEVER-virheen (englanninkielinen
# tyokalu suomenkieliselle datalle). Jos BM25 ei riita, seuraava askel
# on bge-m3/e5-small - ei tama malli.
import json
import pickle
import re
import sys
from pathlib import Path

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    print("Puuttuu paketti. Asenna:")
    print("  pip install rank_bm25")
    sys.exit(1)

CORPUS_PATH = Path(__file__).resolve().parent.parent / "faktabaari_corpus.json"
INDEX_PATH = Path(__file__).resolve().parent / "bm25_index.pkl"

TOKEN_RE = re.compile(r"[a-zA-ZäöåÄÖÅ0-9]+")


def tokenize(text: str) -> list[str]:
    """Yksinkertainen tokenisointi: pienet kirjaimet + sananrajat regexilla.
    EI lemmatisointia/stemmingia - suomen taivutusmuodot (esim. "koronan",
    "koronasta", "korona") jäävät BM25:lle eri sanoiksi. Tämä on
    tietoinen yksinkertaistus ensimmäiseen versioon, ei unohdus: jos
    hakulaatu kärsii taivutusmuotojen takia, seuraava askel on joko
    yksinkertainen sanavartalointi tai siirtyminen embeddaukseen."""
    return TOKEN_RE.findall(text.lower())


def build_index(corpus_path: Path = CORPUS_PATH, index_path: Path = INDEX_PATH):
    if not corpus_path.exists():
        print(f"Korpusta ei löytynyt: {corpus_path}")
        print("Aja ensin: python faktabaari_scraper.py")
        sys.exit(1)

    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data["articles"]
    print(f"Ladattu {len(articles)} artikkelia korpuksesta.")

    tokenized = [tokenize(a["body_text"]) for a in articles]
    bm25 = BM25Okapi(tokenized)

    # Tallennetaan indeksi JA artikkelien metadata (ei koko body_textiä
    # uudelleen - se on jo korpus-JSON:issa) yhdessä pickle-tiedostossa,
    # jotta /analyze-endpoint voi ladata molemmat käynnistyessään ilman
    # koko korpuksen uudelleenlukua tai -indeksointia joka pyynnöllä.
    metadata = [
        {"title": a["title"], "url": a["url"], "date": a["date"]}
        for a in articles
    ]

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "wb") as f:
        pickle.dump({"bm25": bm25, "metadata": metadata}, f)

    print(f"Indeksi tallennettu: {index_path}")
    return bm25, metadata


def load_index(index_path: Path = INDEX_PATH):
    with open(index_path, "rb") as f:
        data = pickle.load(f)
    return data["bm25"], data["metadata"]


def search(bm25, metadata, query: str, top_k: int = 5):
    tokens = tokenize(query)
    scores = bm25.get_scores(tokens)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = []
    for i in ranked[:top_k]:
        results.append({**metadata[i], "score": round(float(scores[i]), 2)})
    return results


if __name__ == "__main__":
    bm25, metadata = build_index()

    # Pikatestaus: muutama oikea kysely korpuksesta, jotta näkee heti
    # tuottaako BM25 järkeviä osumia ennen kuin se yhdistetään
    # /analyze-endpointiin.
    test_queries = [
        "koronarokote",
        "Nato Suomi",
        "EU budjetti",
    ]
    print("\nPikatestaus muutamalla kyselyllä:\n")
    for q in test_queries:
        print(f"--- Kysely: {q!r} ---")
        for r in search(bm25, metadata, q, top_k=3):
            print(f"  {r['score']:6.2f}  {r['title'][:70]}")
        print()
