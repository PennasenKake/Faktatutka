# Faktatutka

> Uutistekstin ja väitteiden uskottavuusarvio — rehellisellä
> epävarmuudella ja näkyvillä lähteillä. Ei tuomiota, vaan tutka.

## Tila
Kehitteillä — kerrokset 1–2 valmiit (baseline ML + pytest-testit), kerros 3/7 (LLM-arvio) alkamassa

## Mitä tämä on
Faktatutka arvioi syötetyn uutistekstin tai väitteen uskottavuutta
yhdistämällä perinteisen ML-luokittelun, kielimallin ja lähdehaun
(RAG). Se ei julista totuutta — se antaa kalibroidun arvion ja
näyttää mihin se perustuu.

## Kerrokset
- [X] 1. Baseline (TF-IDF + logistinen regressio)
- [X] 2. Testit (pytest)
- [ ] 3. LLM-arvio (Ollama)
- [ ] 4. RAG (lähdehaku)
- [ ] 5. Käyttöliittymä (React)
- [ ] 6. Docker
- [ ] 7. Selainlaajennus (valinnainen)

## Asennus

(täydentyy)

## Baseline (kerros 1)

### Tulokset

| Dataset | Accuracy | Huomio |
|---|---|---|
| ISOT | 99 % | Lähdevuoto (ks. alla) — ei luotettava mittari mallin oikeasta kyvystä |
| LIAR-PLUS | 61 % | Realistisempi luku, mutta luokka 0:n recall vain 0.43 — malli jättää yli puolet ei-uskottavista väitteistä tunnistamatta |
| ISOT → WELFake (yleistyvyystesti) | 57 % | Vuodoton, aidosti erillinen testijoukko — malli tunnistaa 93 % real-artikkeleista mutta vain 20 % fake-artikkeleista |

Kontrasti näiden kolmen välillä on tarkoituksellinen: sama koodi, eri tavat testata, hyvin eri luvut. Ero ei kerro että jokin malli olisi "huonompi" — se kertoo kuinka paljon aiemmat luvut olivat lähdevuodon paisuttamia, ja mitä jää jäljelle kun vuoto poistetaan.

### Tunnettu datavuoto (ISOT)
ISOT-baseline saavuttaa 99 % tarkkuuden, mutta se ei ole luotettava mittari.
`df["text"].str.contains("Reuters")` -tarkistus osoittaa että sana "Reuters"
esiintyy 99.8 %:ssa tosi-uutisia mutta vain 1.4 %:ssa vale-uutisia — malli
oppii todennäköisesti tunnistamaan lähteen (Reuters-uutistoimiston
kirjoitustyylin/dateline-muodon), ei väitteen totuudenmukaisuutta. Tämä
tarkkuusluku ei siis edusta mallin kykyä yleistää muihin lähteisiin.

### LIAR-datan binäärikynnys
LIAR-PLUS:n kuusi luokkaa (`true` → `pants-fire`) mapattiin binääriseksi:
`true`/`mostly-true`/`half-true` → uskottava (1), `barely-true`/`false`/
`pants-fire` → ei-uskottava (0). Raja on tulkinnanvarainen, ei neutraali:
`half-true` luokiteltiin uskottavaksi. Tiukempi raja (vain `true`+
`mostly-true` → 1) olisi tuottanut eri — todennäköisesti matalamman —
tarkkuuden ja epätasapainoisemman luokkajakauman. Lähdetiedosto sisälsi
myös 2 täysin tyhjää riviä, jotka pudotettiin ennen käsittelyä.

### Signaalisanat vahvistavat datavuodon
Mallin 15 vahvinta "real"-signaalisanaa (`model.coef_`) ovat lähes
yksinomaan Reuters-uutistoimiston kirjoitusmuotoon liittyviä: `reuters`
(paino 27.4 — ylivoimaisesti suurin yksittäinen piirre koko sanastossa),
`said`, `washington`, kaikki viisi arkipäivää, ja `edt` (aikavyöhykelyhenne
uutistoimistojen aikaleimoista — ei mitään tekemistä väitteen
totuudenmukaisuuden kanssa). "Fake"-puolen vahvimmat sanat (`image`,
`featured`, `getty`, `pic`) viittaavat puolestaan blogialustojen
kuvatekstimuotoiluun. Malli erottaa siis kaksi julkaisuformaattia
toisistaan, ei väitteiden totuudenmukaisuutta — sama havainto kuin
kohdassa 1.8, nyt vahvistettuna suoraan mallin painoista.

### WELFake-yleistyvyystesti
ISOT- ja LIAR-PLUS-tulokset molemmat testaavat mallia saman datasetin
sisällä (train/test-jako samasta lähteestä). Aidompi yleistyvyystesti on
opettaa malli yhdellä datasetillä ja testata täysin toisella:
`Welfake_check.py` opettaa ISOT:illa ja testaa WELFake-datasetillä
(Zenodo, 72095 riviä puuttuvien tekstirivien pudotuksen jälkeen).

Diagnoosin aikana löytyi kaksi erillistä ongelmaa. Ensimmäinen: WELFaken
CSV:n label-arvot ovat käänteiset sen omaan Zenodo-dokumentaatioon
nähden ("0 = fake, 1 = real" on väitetty, data on päinvastoin) —
vahvistettu sekä tarkkuuden kääntymisellä (0.17 → 0.83 kun labelit
käännettiin) että manuaalisella esimerkkirivien luvulla. Toinen,
vakavampi: 45010 WELFaken riviä (62 % koko datasetistä) osoittautui
sanasta sanaan samoiksi artikkeleiksi kuin ISOT:issa — WELFake jakaa siis
suuren osan lähdemateriaalistaan ISOT:in kanssa. Kun nämä
päällekkäisyydet poistettiin testidatasta, jäljelle jäi 27085 aidosti
uutta riviä.

Tällä puhtaalla testijoukolla tarkkuus on 0.57 — ei 0.83, joka oli
suurelta osin vuotanut luku (osa "testiriveistä" oli malli nähnyt jo
opetusdatassa toisena CSV-tiedostona). 0.57 on myös vahvasti vino: malli
tunnistaa 93 % oikeasti fake-artikkeleista mutta vain 20 % oikeasti
real-artikkeleista — se leimaa siis 80 % aidosta uutissisällöstä
virheellisesti epäluotettavaksi. Todennäköinen syy: kun ISOT:in kanssa
identtiset rivit poistettiin, jäljelle jäänyt "real"-joukko koostuu
artikkeleista jotka eivät enää kanna ISOT:in Reuters-muotoilua (dateline,
"said", viikonpäivät) - juuri niitä signaaleja joita malli oppi
pitämään "real":na. Malli ei siis ole oppinut arvioimaan sisältöä, vaan
yhtä kapeaa muotoilutunnistetta, ja soveltaa sen puuttumista väärin.

## Testit (kerros 2)

### Kattavuus lukuina

| Tiedosto | Testejä | Mitä todistaa |
|---|---|---|
| `tests/test_baseline.py` | 6 | Malli ja vectorizer latautuvat oikeina tyyppeinä, `predict_proba()` palauttaa validin [0,1]-jakauman joka summautuu ykköseen, kaksi ilmiselvää real-esimerkkiä ja yksi ilmiselvä fake-esimerkki menevät oikeaan suuntaan |
| `tests/test_edge_cases.py` | 5 | Tyhjä syöte, hyvin pitkä syöte, pelkät numerot, pelkät symbolit ja suomenkielinen syöte eivät kaadu — kaikki palauttavat rakenteellisesti validin todennäköisyysjakauman |

11/11 vihreää. `scope="session"`-fixturet lataavat mallin ja vectorizerin levyltä vain kerran koko testiajolle uudelleenkoulutuksen sijaan.

### Real/fake-esimerkit on valittu muotoilulla, ei totuusarvolla
Testien real-esimerkit sisältävät tarkoituksella Reuters-dateline-muodon
(`"WASHINGTON (Reuters) - ..."`) ja sanan `said`, fake-esimerkki
blogityylisiä signaalisanoja (`watch`, `featured`, `image`, `like`) —
samat piirteet jotka "Tunnettu datavuoto" ja "Signaalisanat" -osiot
yllä jo osoittivat mallin todellisiksi päätöksentekoperusteiksi. Testi
lukitsee mallin todellisen, opitun käytöksen paikoilleen — ei sitä
onko jokin väite totta. Jos joku yrittäisi "korjata" epäonnistuneen
testin syöttämällä geneeriseen tekstiin Reuters-muotoilua vain
läpäistäkseen sen, se ei todistaisi mitään väitteen
totuudenmukaisuudesta.

### Kattavuusraportti paljasti tietoisen rajauksen
`pytest --cov=. --cov-report=term-missing` näyttää 0 % kattavuuden
`baseline.py`:lle, `baseline_liar.py`:lle, `Welfake_check.py`:lle ja
`tfidf_check.py`:lle — ei siksi että koodi olisi rikki, vaan koska
yksikään testi ei koskaan tuo (`import`) näitä tiedostoja. Testit
lataavat vain valmiiksi tallennetun `model.joblib`/`vectorizer.joblib`-
tiedoston ja todistavat sen käyttäytymisen, eivät itse
koulutuslogiikkaa (`train_test_split`, `pd.concat`, TF-IDF-sovitus).
Tämä on tietoinen rajaus, ei aukko joka huomattiin liian myöhään: jos
koulutuslogiikkaan tulisi regressio, testit huomaisivat sen vasta
seuraavalla `baseline.py`-ajolla ja mallin uudelleentallennuksella,
eivät automaattisesti. Testi-infrastruktuuri itsessään (`conftest.py`,
molemmat testitiedostot) on 100 % katettu — kokonaisluku 29 % on siis
mittausvääristymä joka sisältää tarkoituksella testaamattomat
kertakäyttöskriptit, ei todiste puutteellisesta testauksesta.

(täydentyy kerros kerrallaan)