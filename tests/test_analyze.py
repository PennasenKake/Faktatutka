# tests/test_analyze.py
# Testaa /analyze-endpointin HTTP-käyttäytymisen (3.11) - EI testaa onko
# LLM:n vastaus oikea, se ei ole edes mahdollista ilman oikeaa Ollama-
# kutsua. Tämä testaa jotain eri: reagoiko main.py oikein SIIHEN MITÄ
# call_llm() palauttaa, riippumatta siitä miten call_llm sisäisesti
# päätyi siihen tulokseen. Se on tarkalleen oikea rajapinta mockata -
# katso miksi alempaa.
import pytest
from unittest.mock import patch


# ---- Miksi mockataan juuri call_llm(), ei esim. ollama.generate() suoraan?
#
# main.py:n analyze()-funktio tekee yhden asian: kutsuu call_llm(text) ja
# palauttaa tuloksen. call_llm() itse tekee kaiken raskaan työn (ML-piste,
# Ollama-kutsu, retry, fallback). Jos mockaisimme ollama.generate()-
# kutsun syvemmällä tasolla, testi rakoilisi joka kerta kun call_llm():n
# SISÄINEN toteutus muuttuu (esim. retry-logiikka, promptin muotoilu) -
# vaikka /analyze-endpointin ulkoinen käyttäytyminen ei muuttuisi lainkaan.
# Mockaamalla call_llm() testataan vain sitä mikä oikeasti kuuluu 3.11:n
# vastuulle: toimiiko HTTP-kerros oikein. call_llm():n SISÄINEN logiikka
# (retry, JSON-validointi, fallback) on jo katettu ollama_test.py:n
# käsin ajetuilla kokeiluilla - eri kerros, eri testi, ei päällekkäisyyttä.
#
# @patch("main.call_llm") - HUOM polku on "main.call_llm", EI
# "ollama.call_llm" tai vastaava. Patch osoittaa AINA siihen NIMITILAAN
# JOSSA funktiota KÄYTETÄÄN (main-moduulin oma call_llm-nimi), ei siihen
# missä se on alun perin MÄÄRITELTY. Tämä on yleisin unittest.mock-virhe.


@patch("main.call_llm")
def test_analyze_endpoint_success(mock_call_llm, client):
    """Onnistunut tapaus: call_llm palauttaa validin tuloksen, endpoint
    välittää sen sellaisenaan eteenpäin HTTP 200:na."""
    mock_call_llm.return_value = {
        "score": 70,
        "label": "Viitteitä totuudesta",
        "explanation": "Testivastaus, ei oikeaa LLM-kutsua.",
        "ml_score": 55,
        "ml_vocab_hits": 3,
    }

    response = client.post("/analyze", json={"text": "jokin väite"})

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 70
    assert body["label"] == "Viitteitä totuudesta"
    assert body["ml_score"] == 55
    assert body["ml_vocab_hits"] == 3
    # HUOM: emme vertaa response_model=LLMResultia suoraan mock_call_llm:n
    # dict-paluuarvoon - FastAPI validoi/serialisoi sen LLMResultin
    # KAUTTA ennen kuin se lähtee asiakkaalle, joten juuri tällä assertilla
    # todistetaan että se validointi oikeasti tapahtuu eikä vain oleteta.


@patch("main.call_llm")
def test_analyze_endpoint_passes_request_text_to_llm(mock_call_llm, client):
    """Endpointin pitää välittää pyynnön 'text'-kenttä call_llm():lle
    SELLAISENAAN, ei esim. trimmattuna tai muutettuna. Tämä testi ei
    tarkista vastausta lainkaan - se tarkistaa että call_llm:ää kutsuttiin
    oikealla argumentilla, mikä on eri asia kuin oikea paluuarvo."""
    mock_call_llm.return_value = {
        "score": 50, "label": "Epäselvä", "explanation": "x",
        "ml_score": 10, "ml_vocab_hits": 1,
    }

    client.post("/analyze", json={"text": "Helsinki on Suomen pääkaupunki."})

    mock_call_llm.assert_called_once_with("Helsinki on Suomen pääkaupunki.")


@patch("main.call_llm")
def test_analyze_endpoint_surfaces_honest_fallback(mock_call_llm, client):
    """Projektin ydinteesi: epävarmuus ei ole virhe, se on kelvollinen
    vastaus. Kun call_llm() ei saanut luotettavaa LLM-vastausta (molemmat
    retry-yritykset epäonnistuivat), se palauttaa score=50 -fallbackin -
    EI heitä poikkeusta. Tällä testillä varmistetaan että /analyze
    välittää tämän rehellisen "en tiedä" -vastauksen normaalina HTTP
    200 -vastauksena, ei 500-virheenä. Jos joku joskus refaktoroi
    call_llm():n heittämään poikkeuksen fallbackin sijaan, tämä testi
    hajoaa ja paljastaa että käyttäjälle näkyisi outo 500 pelkän
    epävarmuuden takia - juuri sitä mitä teesi kieltää teeskentelemästä."""
    mock_call_llm.return_value = {
        "score": 50,
        "label": "Epäselvä",
        "explanation": (
            "Mallin vastausta ei saatu validoitua luotettavasti tälle "
            "väitteelle — tekninen epävarmuus, ei arvio väitteen sisällöstä."
        ),
        "ml_score": 42,
        "ml_vocab_hits": 0,
    }

    response = client.post("/analyze", json={"text": "jokin epäselvä väite"})

    assert response.status_code == 200
    assert response.json()["score"] == 50


def test_analyze_endpoint_rejects_missing_text_field(client):
    """Tämä testi EI mockaa call_llm():ää lainkaan, eikä sille ole
    tarvetta: pydantic hylkää virheellisen pyynnön (puuttuva pakollinen
    'text'-kenttä) FastAPI:n omassa validointikerroksessa ENNEN kuin
    analyze()-funktio edes suoritetaan. Jos tämä palauttaisi 200 tai 500
    validoinnin sijaan puuttuvalla kentällä, se olisi merkki että
    AnalyzeRequest-mallin validointi ei toimi oikein."""
    response = client.post("/analyze", json={})

    assert response.status_code == 422  # FastAPI: Unprocessable Entity
