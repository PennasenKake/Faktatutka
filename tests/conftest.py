# tests/conftest.py
# Jaetut fixturet kaikille tests/-kansion testeille. Ei importata erikseen
# missään testitiedostossa - pytest lataa tämän automaattisesti.


# tests/conftest.py
import pathlib
import joblib
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session")
def model():
    return joblib.load(ROOT / "model.joblib")

@pytest.fixture(scope="session")
def vectorizer():
    return joblib.load(ROOT / "vectorizer.joblib")
