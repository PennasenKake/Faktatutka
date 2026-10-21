import { useState } from 'react'

const API_URL = 'http://localhost:8000/analyze'

// Neljän tilan kuvio (idle/loading/success/error) kapseloituna omaksi
// hookiksi - App.jsx ei enää tiedä mitään fetchin sisäisyyksistä, vain
// nykyisestä tilasta ja kahdesta funktiosta.
//
// AbortController jätetty TIETOISESTI pois (poikkeaa tehtävälistan 5.9:stä).
// Listan oma perustelu AbortControllerille on kilpa-ajotilanne: käyttäjä
// ehtii lähettää uuden pyynnön ennen kuin edellinen on valmis, ja vanhempi
// vastaus voi ylikirjoittaa uudemman. App.jsx disabloi sekä tekstikentän
// että napin koko "loading"-tilan ajaksi - toista pyyntöä EI VOI käynnistää
// ennen kuin ensimmäinen on valmis, joten sama ongelma ei voi syntyä tässä
// UI:ssa rakenteellisesti. AbortController ratkaisisi saman ongelman
// monimutkaisemmin. "Ei ylimääräistä rakennetta" -periaate puoltaa
// yksinkertaisempaa ratkaisua. HUOM: tämä päätös pitää tarkistaa uudelleen
// jos joskus lisätään esim. "peruuta analyysi" -nappi latauksen aikana.
export function useAnalyze() {
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  async function analyze(text) {
    setStatus('loading')
    setResult(null)
    setErrorMessage('')

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })

      if (!response.ok) {
        // Backend vastasi, mutta HTTP-virheellä (esim. 500 - ks. README:n
        // "Ollama OOM" / num_ctx-löydökset). Tämä EI ole sama asia kuin
        // "LLM/RAG epäonnistuu kesken" (tehtävälistan 5.6:n kolmas
        // virhetila) - call_llm():n oma fallback (main.py) hoitaa SEN jo
        // backend-puolella ja palauttaa silti 200 OK:n rehellisellä
        // selitystekstillä, joka renderöityy normaalisti ResultView'ssa,
        // ei virhetilana. Tänne päädytään vain kun itse HTTP-pyyntö
        // epäonnistuu kokonaan (esim. käsittelemätön poikkeus backendissä).
        setErrorMessage(`Palvelin vastasi virheellä (status ${response.status}).`)
        setStatus('error')
        return
      }

      const data = await response.json()
      setResult(data)
      setStatus('success')
    } catch (err) {
      // Tähän päädytään kun fetch ei edes saanut vastausta - backend ei
      // ole käynnissä, väärä portti, tai verkkoyhteys katkesi kesken.
      console.error('Analyysi epäonnistui:', err)
      setErrorMessage('Backend ei vastaa. Tarkista että se on käynnissä (uvicorn, portti 8000).')
      setStatus('error')
    }
  }

  function reset() {
    setStatus('idle')
    setResult(null)
    setErrorMessage('')
  }

  return { status, result, errorMessage, analyze, reset }
}