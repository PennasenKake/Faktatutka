# tests/test_rag.py
# Testaa rag/index.py:n BM25-mekaniikan suoraan, erillaan /analyze-
# endpointista (jota test_analyze.py:n kaksi uutta testia testaavat
# paasta paahan). Tama kerros oli aiemmin kokonaan testaamatta (vrt.
# kerrokset 1-3, joilla oli pytest-kattavuus heti alusta) - suljettu
# askeleen 4.6/4.7 toteutuksen yhteydessa.
#
# HUOM: tama testi lataa OIKEAN rag/bm25_index.pkl:n levylta, ei mocksia -
# sama periaate kuin tests/conftest.py:n model/vectorizer-fixtureilla
# (kerros 1): generoitu artefakti, ei committoitu gittiin (.gitignore),
# mutta ladataan suoraan koska se on olemassa taman koneen levylla sen
# jalkeen kun rag/index.py on ajettu kerran.
import pathlib

from rag.index import load_index, search

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_search_finds_relevant_match():
    bm25, metadata = load_index(ROOT / "rag" / "bm25_index.pkl")
    results = search(bm25, metadata, "EU budjetti", top_k=3)

    assert results[0]["score"] > 0
    assert "EU" in results[0]["title"] or "eu" in results[0]["title"].lower()


def test_search_returns_zero_score_for_unrelated_query():
    bm25, metadata = load_index(ROOT / "rag" / "bm25_index.pkl")
    results = search(bm25, metadata, "Marsin pikku-ukot avaruusaluksineen", top_k=3)

    # Haku palauttaa silti top_k tulosta (BM25 ei koskaan "lopu kesken"),
    # mutta aidosti eparelevanteilla pistemaara on 0.0 - se on main.py:n
    # RAG_MIN_SCORE-kynnyksen perusta.
    assert all(r["score"] == 0.0 for r in results)
