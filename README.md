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

BASELINE

Tunnettu datavuoto: ISOT-baseline saavuttaa 99 % tarkkuuden, mutta se ei ole luotettava mittari. df["text"].str.contains("Reuters") -tarkistus osoittaa että sana "Reuters" esiintyy 99.8 %:ssa tosi-uutisia mutta vain 1.4 %:ssa vale-uutisia — malli oppii todennäköisesti tunnistamaan lähteen (Reuters-uutistoimiston kirjoitustyylin/dateline-muodon), ei väitteen totuudenmukaisuutta. Tämä tarkkuusluku ei siis edusta mallin kykyä yleistää muihin lähteisiin.


(täydentyy kerros kerrallaan)
