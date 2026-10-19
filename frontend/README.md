# Faktatutka — frontend (kerros 5, aloitettu)

React + Vite -skaffoldi (JavaScript, ei TypeScript — tietoinen valinta,
ks. projektin juuren README.md). Tällä hetkellä pelkkä oletusskaffoldi
(`npm create vite@latest frontend -- --template react`) — ei yhtään
Faktatutka-spesifistä komponenttia vielä. Rakenne (src/api/,
src/components/ tms.) päätetään seuraavassa askeleessa kun oikeaa UI:ta
aletaan kirjoittaa, ei etukäteen tyhjillä kansioilla.

## Ajaminen

```
cd frontend
npm install
npm run dev      # kehityspalvelin, oletus http://localhost:5173
npm run build    # tuotantobuild dist/-kansioon
```

Backend (`/analyze`-endpoint) ajetaan erikseen juurikansiosta, ks.
pääREADME:n "Asennus"-osio. Frontend ja backend ovat kehityksessä
aina erillisiä palveluita — ks. pääREADME:n avoin kysymys CORS- ja
tarjoilumallista ennen kuin API-kutsuja kirjoitetaan.

Koko projektin tarina, tavoite ja tekniset päätökset: ks. juurikansion
`README.md`.
