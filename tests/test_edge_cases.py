# tests/test_edge_cases.py
import pytest


def assert_valid_proba(proba):
    """Rakenteellinen tarkistus: kaksi arvoa, [0,1]-välillä, summa 1."""
    assert proba.shape == (1, 2)
    assert (proba >= 0).all() and (proba <= 1).all()
    assert abs(proba.sum() - 1.0) < 1e-6


EDGE_CASE_INPUTS = [
    "",                                                # tyhjä syöte
    "pitkä teksti " * 1000,                            # hyvin pitkä syöte
    "123 456 789 000 111 2024 2025",                   # pelkkiä numeroita
    "!!! *** ### $$$ %%% &&& ???",                     # pelkkiä symboleja
    "Tämä on suomenkielinen väite jota malli ei ole koskaan nähnyt harjoitusdatassa.",  # ei-englanninkielinen
]


@pytest.mark.parametrize(
    "text",
    EDGE_CASE_INPUTS,
    ids=["tyhja", "hyvin_pitka", "pelkat_numerot", "pelkat_symbolit", "muu_kieli"],
)
def test_edge_case_inputs_do_not_crash(model, vectorizer, text):
    X = vectorizer.transform([text])
    assert_valid_proba(model.predict_proba(X))