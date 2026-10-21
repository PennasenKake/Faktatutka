import { useState } from 'react'
import './App.css'
import { useAnalyze } from './useAnalyze'
import ResultView from './ResultView'

// Ei kova yläraja - backend ei rajoita tekstin pituutta (AnalyzeRequest.text
// on pelkkä str), tämä on pelkkä läpinäkyvyysvihje käyttäjälle joka liittyy
// num_ctx=8192-löydökseen (ks. README): hyvin pitkä artikkeli voi silti olla
// riski, tarkkaa rajaa ei ole koskaan mitattu.
const LONG_TEXT_WARNING_THRESHOLD = 8000

function App() {
  const [claimText, setClaimText] = useState('')
  const { status, result, errorMessage, analyze, reset } = useAnalyze()

  function handleSubmit(e) {
    e.preventDefault()
    analyze(claimText)
  }

  function handleReset() {
    setClaimText('')
    reset()
  }

  const showResetLink = status === 'success' || status === 'error'
  const charCount = claimText.length
  const isLongText = charCount > LONG_TEXT_WARNING_THRESHOLD

  return (
    <>
      <header className="app-header">
        <div className="app-header-inner">
          <div>
            <h1>Faktatutka</h1>
            <p className="tagline">Rehellinen epävarmuus, näkyvät lähteet.</p>
          </div>
          {showResetLink && (
            <button type="button" className="reset-link" onClick={handleReset}>
              ← Uusi analyysi
            </button>
          )}
        </div>
      </header>

      <main>
        <form onSubmit={handleSubmit}>
          <label htmlFor="claim-text">Väite tai uutisteksti</label>
          <textarea
            id="claim-text"
            rows={7}
            value={claimText}
            onChange={(e) => setClaimText(e.target.value)}
            disabled={status === 'loading'}
            placeholder='Esim. "Hallitus aikoo nostaa polttoaineveroa 15 prosentilla ensi vuonna", tai liitä artikkelin koko teksti.'
          />
          <div className="form-footer">
            <span className={'char-count' + (isLongText ? ' char-count-warn' : '')}>
              {charCount} merkkiä
              {isLongText && ' — hyvin pitkä, voi katketa kontekstirajaan (ei vielä mitattu raja)'}
            </span>
            <button type="submit" disabled={claimText.trim() === '' || status === 'loading'}>
              {status === 'loading' ? 'Analysoidaan…' : 'Analysoi teksti'}
            </button>
          </div>
        </form>

        {status === 'loading' && (
          <div className="loading-state" role="status" aria-live="polite">
            <span className="spinner" aria-hidden="true" />
            <p>Analysoidaan väitettä…</p>
            <p className="muted">
              Tyypillisesti muutama sekunti — paikallinen kielimalli, ei pilvi-API:a.
            </p>
          </div>
        )}

        {status === 'success' && result && <ResultView result={result} />}

        {status === 'error' && (
          <p className="error-text">
            {errorMessage || 'Analyysi epäonnistui.'} Katso tarvittaessa konsoli (F12).
          </p>
        )}
      </main>

      <footer className="app-footer">
        <a
          href="https://github.com/PennasenKake/Faktatutka"
          target="_blank"
          rel="noopener noreferrer"
        >
          github.com/PennasenKake/Faktatutka
        </a>
        <span className="muted"> · Avoin lähdekoodi · Paikallinen kielimalli, ei pilvi-API:a</span>
      </footer>
    </>
  )
}

export default App