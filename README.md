# Faktatutka

> Uutistekstin ja väitteiden uskottavuusarvio — rehellisellä
> epävarmuudella ja näkyvillä lähteillä. Ei tuomiota, vaan tutka.

## Tila
Kehitteillä — kerros 1/7 (baseline ML)

## Mitä tämä on
Faktatutka arvioi syötetyn uutistekstin tai väitteen uskottavuutta
yhdistämällä perinteisen ML-luokittelun, kielimallin ja lähdehaun
(RAG). Se ei julista totuutta — se antaa kalibroidun arvion ja
näyttää mihin se perustuu.

## Kerrokset
- [ ] 1. Baseline (TF-IDF + logistinen regressio)
- [ ] 2. Testit (pytest)
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

Kontrasti (99 % vs. 61 %) on tarkoituksellinen: sama koodi, kaksi eri datasettiä, kaksi hyvin eri lukua. Ero ei kerro että LIAR-malli olisi "huonompi" — se kertoo että ISOT:in luku oli lähes kokonaan lähdevuodon paisuttama.

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

### Signaalisanat vahvistavat datavuodon (1.14)
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

(täydentyy kerros kerrallaan)