# tests/test_baseline.py
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer


def test_model_loads(model):
    assert isinstance(model, LogisticRegression)


def test_vectorizer_loads(vectorizer):
    assert isinstance(vectorizer, TfidfVectorizer)


def test_predict_proba_sums_to_one(model, vectorizer):
    X = vectorizer.transform(["jokin testiteksti"])
    proba = model.predict_proba(X)
    assert proba.shape == (1, 2)
    assert (proba >= 0).all() and (proba <= 1).all()   # [0,1]-rajat eksplisiittisesti
    assert abs(proba.sum() - 1.0) < 1e-6


# HUOM: nämä esimerkit on valittu MUOTOILUN perusteella, ei sisällön
# totuusarvon - ne jäljittelevät tarkoituksella ISOT:in opittua signaalia
# (Reuters-dateline vs. blogityylinen otsikko/kuvateksti, ks. README
# "Tunnettu datavuoto" ja "Signaalisanat vahvistavat datavuodon"). Testi
# lukitsee mallin TODELLISEN käytöksen paikoilleen, ei toivottua
# käytöstä - jos joku yrittää "korjata" epäonnistuneen testin kirjoittamalla
# geneeriseen tekstiin Reuters-muotoilua vain läpäistäkseen sen, se ei
# todista mitään väitteen totuudenmukaisuudesta.

REAL_EXAMPLES = [
    "WASHINGTON (Reuters) - The Federal Reserve said on Tuesday it would "
    "keep interest rates unchanged, according to a statement released "
    "after a two-day policy meeting.",
    "LONDON (Reuters) - Britain's economy grew faster than expected in "
    "the third quarter, official data showed on Thursday, easing "
    "pressure on the government ahead of the budget.",
]

FAKE_EXAMPLES = [
    "WATCH: This shocking featured image will make you rethink "
    "everything - share this post if you agree, click here for more "
    "like it on our site.",
]


@pytest.mark.parametrize("text", REAL_EXAMPLES, ids=["fed_reuters", "uk_economy_reuters"])
def test_obvious_real_predicted_real(model, vectorizer, text):
    X = vectorizer.transform([text])
    pred = model.predict(X)[0]
    assert pred == 1, f"Odotettiin real (1), saatiin {pred}: {text[:50]}..."


@pytest.mark.parametrize("text", FAKE_EXAMPLES)
def test_obvious_fake_predicted_fake(model, vectorizer, text):
    X = vectorizer.transform([text])
    pred = model.predict(X)[0]
    assert pred == 0, f"Odotettiin fake (0), saatiin {pred}: {text[:50]}..."