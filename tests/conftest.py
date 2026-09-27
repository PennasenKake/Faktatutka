# tests/conftest.py
# Jaetut fixturet kaikille tests/-kansion testeille. Ei importata erikseen
# missään testitiedostossa - pytest lataa tämän automaattisesti.


# tests/conftest.py
import pathlib
import joblib
import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session")
def model():
    return joblib.load(ROOT / "model.joblib")

@pytest.fixture(scope="session")
def vectorizer():
    return joblib.load(ROOT / "vectorizer.joblib")


@pytest.fixture(scope="session")
def client():
    """FastAPI:n testiasiakas /analyze-endpointin testaamiseen (3.11).

    HUOM: `from main import app` suorittaa main.py:n MODUULITASON koodin,
    eli myös rivit `ML_MODEL = joblib.load("model.joblib")` ja
    `ML_VECTORIZER = joblib.load(...)`. Ne käyttävät SUHTEELLISTA polkua
    (ei ROOT-muuttujaa kuten model/vectorizer-fixturet yllä), joten import
    toimii vain jos pytest ajetaan projektin juuresta (`pytest tests/ -v`
    faktatutka/-kansiossa) - siellä "model.joblib" osoittaa oikeaan
    tiedostoon. Jos import epäonnistuu FileNotFoundErroriin, tarkista ajatko
    pytestiä väärästä kansiosta.

    Tällä ei silti oteta yhteyttä Ollamaan: import lataa vain ML-baselinen,
    ei kutsu ollama.generate()-funktiota. Se tapahtuu vasta call_llm()-
    kutsun sisällä, ja se on tarkalleen se kutsu jonka jokainen testi
    mockaa alla - Ollaman ei tarvitse olla käynnissä tämän testitiedoston
    ajamiseksi.
    """
    from main import app
    return TestClient(app)
