# tests/test_analyze.py
# Testaa /analyze-endpointin HTTP-kayttaytymisen (3.11) - EI testaa onko
# LLM:n vastaus oikea, se ei ole edes mahdollista ilman oikeaa Ollama-
# kutsua. Tama testaa jotain eri: reagoiko main.py oikein SIIHEN MITA
# call_llm() palauttaa, riippumatta siita miten call_llm sisaisesti
# paatyi siihen tulokseen. Se on tarkalleen oikea rajapinta mockata -
# katso miksi alempaa.
#
# Lisatty askeleen 4.6/4.7 yhteydessa: kaksi uutta testia jotka EIVÄT
# mockaa call_llm():aa kokonaan, vaan vain ollama.generate():n - jotta
# retrieve_sources()/BM25-haku ajaa aidosti ja /analyze:n sources-kentta
# tulee todistetusti oikeasta RAG-putkesta, ei vain lapaistua lavitse.
import pytest
from unittest.mock import patch


# ---- Miksi mockataan juuri call_llm(), ei esim. ollama.generate() suoraan?
#
# main.py:n analyze()-funktio tekee yhden asian: kutsuu call_llm(text) ja
# palauttaa tuloksen. call_llm() itse tekee kaiken raskaan tyon (ML-piste,
# RAG-haku, Ollama-kutsu, retry, fallback). Jos mockaisimme ollama.generate()-
# kutsun syvemmalla tasolla, testi rakoilisi joka kerta kun call_llm():n
# SISAINEN toteutus muuttuu - vaikka /analyze-endpointin ulkoinen kayttaytyminen
# ei muuttuisi lainkaan. Mockaamalla call_llm() testataan vain sita mika
# oikeasti kuuluu 3.11:n vastuulle: toimiiko HTTP-kerros oikein.
#
# @patch("main.call_llm") - HUOM polku on "main.call_llm", EI
# "ollama.call_llm" tai vastaava. Patch osoittaa AINA siihen NIMITILAAN
# JOSSA funktiota KAYTETAAN (main-moduulin oma call_llm-nimi), ei siihen
# missa se on alun perin MAARITELTY. Tama on yleisin unittest.mock-virhe.


@patch("main.call_llm")
def test_analyze_endpoint_success(mock_call_llm, client):
    """Onnistunut tapaus: call_llm palauttaa validin tuloksen, endpoint
    valittaa sen sellaisenaan eteenpain HTTP 200:na."""
    mock_call_llm.return_value = {
        "score": 70,
        "label": "Viitteitä totuudesta",
        "explanation": "Testivastaus, ei oikeaa LLM-kutsua.",
        "ml_score": 55,
        "ml_vocab_hits": 3,
        "sources": [],
    }

    response = client.post("/analyze", json={"text": "jokin väite"})

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 70
    assert body["label"] == "Viitteitä totuudesta"
    assert body["ml_score"] == 55
    assert body["ml_vocab_hits"] == 3
    assert body["sources"] == []
    # HUOM: emme vertaa response_model=LLMResultia suoraan mock_call_llm:n
    # dict-paluuarvoon - FastAPI validoi/serialisoi sen LLMResultin
    # KAUTTA ennen kuin se lahtee asiakkaalle, joten juuri talla assertilla
    # todistetaan etta se validointi oikeasti tapahtuu eika vain oleteta.


@patch("main.call_llm")
def test_analyze_endpoint_passes_request_text_to_llm(mock_call_llm, client):
    """Endpointin pitaa valittaa pyynnon 'text'-kentta call_llm():lle
    SELLAISENAAN, ei esim. trimmattuna tai muutettuna. Tama testi ei
    tarkista vastausta lainkaan - se tarkistaa etta call_llm:aa kutsuttiin
    oikealla argumentilla, mika on eri asia kuin oikea paluuarvo."""
    mock_call_llm.return_value = {
        "score": 50, "label": "Epäselvä", "explanation": "x",
        "ml_score": 10, "ml_vocab_hits": 1, "sources": [],
    }

    client.post("/analyze", json={"text": "Helsinki on Suomen pääkaupunki."})

    mock_call_llm.assert_called_once_with("Helsinki on Suomen pääkaupunki.")


@patch("main.call_llm")
def test_analyze_endpoint_surfaces_honest_fallback(mock_call_llm, client):
    """Projektin ydinteesi: epavarmuus ei ole virhe, se on kelvollinen
    vastaus. Kun call_llm() ei saanut luotettavaa LLM-vastausta (molemmat
    retry-yritykset epaonnistuivat), se palauttaa score=50 -fallbackin -
    EI heita poikkeusta. Talla testilla varmistetaan etta /analyze
    valittaa taman rehellisen "en tieda" -vastauksen normaalina HTTP
    200 -vastauksena, ei 500-virheena."""
    mock_call_llm.return_value = {
        "score": 50,
        "label": "Epäselvä",
        "explanation": (
            "Mallin vastausta ei saatu validoitua luotettavasti tälle "
            "väitteelle — tekninen epävarmuus, ei arvio väitteen sisällöstä."
        ),
        "ml_score": 42,
        "ml_vocab_hits": 0,
        "sources": [],
    }

    response = client.post("/analyze", json={"text": "jokin epäselvä väite"})

    assert response.status_code == 200
    assert response.json()["score"] == 50


def test_analyze_endpoint_rejects_missing_text_field(client):
    """Tama testi EI mockaa call_llm():aa lainkaan, eika sille ole
    tarvetta: pydantic hylkaa virheellisen pyynnon (puuttuva pakollinen
    'text'-kentta) FastAPI:n omassa validointikerroksessa ENNEN kuin
    analyze()-funktio edes suoritetaan."""
    response = client.post("/analyze", json={})

    assert response.status_code == 422  # FastAPI: Unprocessable Entity


# ---- Askel 4.8: testaa kaksi aaripaata RAG-haulle OIKEASTI, ei mockatulla
# call_llm:lla. Nama mockaavat VAIN ollama.generate():n (LLM-kutsun), jotta
# retrieve_sources()/BM25-haku ajaa aidosti oikeaa 208 artikkelin korpusta
# vasten. Tama todistaa etta /analyze palauttaa oikeat sources-kentat
# paasta paahan, ei vain etta HTTP-kerros valittaa mita sille syotetaan.

def _fake_ollama_response(score=60, label="Viitteitä totuudesta", explanation="x"):
    import json
    return {"response": json.dumps({
        "score": score, "label": label, "explanation": explanation,
    })}


@patch("main.ollama.generate")
def test_analyze_endpoint_includes_real_sources_for_known_claim(mock_generate, client):
    """Vaite jonka tiedetaan loytyvan korpuksesta (Nato-jasenyys) -
    sources-listan EI pitaisi olla tyhja."""
    mock_generate.return_value = _fake_ollama_response()

    response = client.post("/analyze", json={"text": "Suomi liittyi Natoon vuonna 2023"})

    assert response.status_code == 200
    sources = response.json()["sources"]
    assert len(sources) >= 1, "odotettiin vähintään yhtä lähdettä tunnetulle väitteelle"
    assert sources[0]["score"] > 0


@patch("main.ollama.generate")
def test_analyze_endpoint_sources_empty_for_unrelated_claim(mock_generate, client):
    """Vaite joka ei liity mihinkaan korpuksen artikkeliin - sources-
    listan PITAA olla tyhja, ei keksitty lahde. Tama on projektin teesin
    ydin: 'en loytanyt lahdetta' on kelvollinen vastaus, ei virhe eika
    syy keksia jotain."""
    mock_generate.return_value = _fake_ollama_response()

    response = client.post(
        "/analyze", json={"text": "Marsissa asuu vihreitä pikku-ukkoja"}
    )

    assert response.status_code == 200
    assert response.json()["sources"] == []


@patch("main.ollama.generate")
def test_analyze_endpoint_filters_single_incidental_token_match(mock_generate, client):
    """Regressiotesti oikealle löydetylle bugille (ks. README,
    'Vaara osuma korjattu'): yllä oleva testi ei paljastanut aiemmin
    todellista ongelmaa, koska testikorpuksella ei sattunut olemaan
    yhteisia sanoja. Oikealla 208 artikkelin korpuksella kysely
    "Marsissa asuu vihreita pikku-ukkoja" sai pisteen 5.27 YHDEN sanan
    ("asuu") kirjaimellisesta osumasta yhteen täysin aiheeseen
    liittymättömään artikkeliin. Tämä testi varmistaa, etta pelkka
    yhden sanan sattumaosuma ei enää riitä ylittämään suodattimen -
    vaaditaan useampi eri kyselysana, ks. retrieve_sources()."""
    mock_generate.return_value = _fake_ollama_response()

    response = client.post(
        "/analyze", json={"text": "Marsissa asuu vihreitä pikku-ukkoja"}
    )

    assert response.status_code == 200
    sources = response.json()["sources"]
    assert sources == [], (
        f"odotettiin tyhjaa listaa, saatiin {sources} - jos tämä palaa, "
        "RAG_MIN_TOKEN_OVERLAP-suodatin ei enää toimi oikealla korpuksella"
    )



# ---- Regressiotestit kahdelle äskettäin korjatulle/lisätylle asialle
# (ks. README: "num_ctx-korjaus" ja "Käyttöliittymä, kerros 5"). Kumpikaan
# ei ollut minkään olemassa olevan testin piirissä aiemmin - py_compile
# ja mockattu "ei kaadu" -testi eivät olisi huomanneet kumpaakaan
# regressiota, koska kumpikaan ei kaada sovellusta, se vain käyttäytyy
# väärin hiljaisesti.

@patch("main.ollama.generate")
def test_analyze_endpoint_sets_num_ctx_to_avoid_silent_truncation(mock_generate, client):
    """num_ctx puuttui aiemmin kokonaan options-sanakirjasta - Ollaman
    oletusarvo (usein 2048 tokenia) olisi voinut katkaista pitkän
    liitetyn artikkelin hiljaa, ilman virhettä. Tämä testi ei todista
    että 8192 on oikea/riittävä arvo millekään syötteelle - se
    varmistaa vain ettei arvo ole enää kokonaan asettamatta, mikä oli
    itse puute."""
    mock_generate.return_value = _fake_ollama_response()

    client.post("/analyze", json={"text": "jokin väite"})

    passed_options = mock_generate.call_args.kwargs["options"]
    assert passed_options.get("num_ctx") == 8192, (
        "num_ctx puuttuu tai on muuttunut - pitkä liitetty artikkeli voi "
        "taas katketa hiljaa Ollaman kontekstirajaan"
    )


@patch("main.ollama.generate")
def test_cors_allows_configured_dev_origin(mock_generate, client):
    """CORS_ORIGINS-ympäristömuuttujan oletusarvo (http://localhost:5173,
    React-devserverin oletusportti) saa Access-Control-Allow-Origin
    -headerin takaisin - varmistaa että CORSMiddleware on oikeasti
    kytketty, ei vain lisätty koodiin ilman vaikutusta."""
    mock_generate.return_value = _fake_ollama_response()

    response = client.post(
        "/analyze",
        json={"text": "jokin väite"},
        headers={"Origin": "http://localhost:5173"},
    )

    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )


@patch("main.ollama.generate")
def test_cors_rejects_unconfigured_origin(mock_generate, client):
    """Negatiivinen pari edelliselle: origin jota CORS_ORIGINS ei
    listaa EI saa Access-Control-Allow-Origin-headeria - varmistaa
    ettei middleware salli kaikkea (ei wildcard "*"), vain nimetyt
    originit."""
    mock_generate.return_value = _fake_ollama_response()

    response = client.post(
        "/analyze",
        json={"text": "jokin väite"},
        headers={"Origin": "https://jokin-tuntematon-sivusto.fi"},
    )

    assert "access-control-allow-origin" not in response.headers


# ---- Kaksi lisätestiä, jotka paikkaavat yllä olevien CORS/num_ctx-
# testien tunnetut aukot (ks. README "Testien riittävyys" -huomio):
# edelliset CORS-testit todistavat vain Starletten "simple response"
# -polun (suora POST + Origin-header), eivät oikeaa selaimen preflight-
# mekanismia; ja num_ctx-testi käyttää lyhyttä tekstiä, joka ei koskaan
# kulje build_rag_context()/user_prompt-koonnin läpi realistisella
# pituudella. Molemmat ovat halpoja lisätä nyt - ei arkkitehtuurimuutosta.

@patch("main.ollama.generate")
def test_cors_preflight_response_for_configured_origin(mock_generate, client):
    """Edelliset kaksi CORS-testiä lähettävät suoraan POST-pyynnön Origin-
    headerin kanssa - se on CORSMiddlewaren "simple response" -polku,
    joka tarkistaa VAIN originin, ei metodia tai headereita. Oikea selain
    lähettää ensin erillisen OPTIONS-preflight-pyynnön (Access-Control-
    Request-Method/-Headers), joka kulkee CORSMiddlewaren ERI haaran
    (preflight_response()) läpi - se ei koskaan edes saavuta /analyze-
    reittiä itse. Tämä testi ei kutsu ollama.generate:ä - preflight-
    vastaus syntyy middlewaressa, LLM:ää ei tarvita. mock_generate on
    mukana vain koska @patch-dekoraattori pysyy yhtenäisenä tiedoston
    muiden testien kanssa; assert_not_called() varmistaa että oletus
    pitää."""
    response = client.options(
        "/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200, (
        "preflight epäonnistui - CORS_ORIGINS, allow_methods tai "
        "allow_headers ei enää täsmää selaimen lähettämään pyyntöön"
    )
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    mock_generate.assert_not_called()


@patch("main.ollama.generate")
def test_analyze_endpoint_handles_full_length_article_without_crashing(
    mock_generate, client
):
    """num_ctx-testi yllä käyttää lyhyttä "jokin väite" -tekstiä - se
    todistaa VAIN että options-sanakirja sisältää num_ctx:n, ei että
    pitkä teksti oikeasti kulkee ehjänä build_rag_context()/user_prompt-
    koonnin läpi asti ollama.generate-kutsuun asti. Tämä testi liittää
    oikean mittaisen (~6000 merkkiä, vastaa pitkää uutisartikkelia)
    väitteen ja varmistaa ettei RAG-kontekstin rakennus tai promptin
    koonti kaada pyyntöä tai katkaise väitettä ITSE koodissamme.
    Ollaman omaa num_ctx-rajaa (katkaiseeko se 8192 tokenin kohdalla)
    ei voi todistaa mockatulla kutsulla - se vaatisi oikean Ollama-
    kutsun, ks. README "num_ctx-korjaus"."""
    mock_generate.return_value = _fake_ollama_response()
    long_claim = "Hallitus aikoo nostaa polttoaineveroa ensi vuonna. " * 120

    response = client.post("/analyze", json={"text": long_claim})

    assert response.status_code == 200
    passed_prompt = mock_generate.call_args.kwargs["prompt"]
    assert long_claim in passed_prompt, (
        "pitkä väite ei päätynyt kokonaisena LLM:lle annettuun promptiin - "
        "jokin koodissamme (EI Ollama itse) katkaisi tai muokkasi sitä "
        "ennen ollama.generate-kutsua"
    )
