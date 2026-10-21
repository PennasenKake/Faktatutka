// Peilaa main.py:n label_from_score()-funktion kynnysarvot väriä varten.
// /analyze EI palauta väriä - vain score/label - joten tämä toistetaan
// tietoisesti frontendissä. Jos backendin kynnysarvot muuttuvat, nämä
// pitää päivittää käsin samaan tahtiin.
function scoreToColor(score) {
  if (score >= 80) return '#256B42'
  if (score >= 60) return '#2B6B54'
  if (score > 40) return '#8A5A00'
  if (score > 20) return '#9E4515'
  return '#962F2F'
}

export default function ResultView({ result }) {
  const { score, label, explanation, ml_score, ml_vocab_hits, sources } = result
  const color = scoreToColor(score)
  const r = 70
  const circumference = 2 * Math.PI * r
  const dashOffset = circumference * (1 - score / 100)
  const hasSources = sources.length > 0

  return (
    <div className="result-wrap">
      <div className="result">
        <svg
          width="160"
          height="160"
          viewBox="0 0 160 160"
          role="img"
          aria-label={`Uskottavuusarvio ${score} prosenttia`}
        >
          <circle cx="80" cy="80" r={r} fill="none" stroke="#3a3a3a" strokeWidth="12" />
          <circle
            cx="80"
            cy="80"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={dashOffset}
            transform="rotate(-90 80 80)"
          />
          <text x="80" y="78" textAnchor="middle" fontSize="28" fontWeight="700" fill="#fff">
            {score}%
          </text>
          <text x="80" y="98" textAnchor="middle" fontSize="12" fill="#aaa">
            arvio
          </text>
        </svg>
        <div className="result-text">
          <span className="label-badge" style={{ backgroundColor: color }}>
            {label}
          </span>
          <p>{explanation}</p>
        </div>
      </div>

      <div className="ml-transparency">
        <p className="box-title">
          Koneoppimismallin oma piste (tausta-arvo, ei pääasiallinen)
        </p>
        <p className="ml-value">
          {ml_score}/100 · {ml_vocab_hits} tunnettua sanaa
        </p>
        <p className="muted">
          Koulutettu englanninkielisellä uutisdatalla — painoarvo on tarkoituksella
          pieni suomenkieliselle tekstille.
        </p>
      </div>

      <div className="sources">
        <p className="box-title">Lähteet ({sources.length})</p>
        <p className="muted">
          Haku löysi nämä aiheeseen liittyvät Faktabaari.fi-artikkelit tekstin
          perusteella. Tämä ei yksin todista, että artikkeli ottaa kantaa juuri
          tähän väitteeseen — lue lähde itse ennen kuin luotat siihen.
        </p>

        {hasSources ? (
          <ul className="sources-list">
            {sources.map((s) => (
              <li key={s.url}>
                <a href={s.url} target="_blank" rel="noopener noreferrer">
                  {s.title}
                </a>
                <span className="muted"> · BM25-pistemäärä: {s.score}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-sources">
            Korpuksesta ei löytynyt tätä väitettä käsittelevää Faktabaari-artikkelia.
            Arvio perustuu kielimallin omaan tietoon, ei ulkoiseen lähteeseen — tämä
            on kelvollinen, rehellinen vastaus, ei virhe.
          </p>
        )}
      </div>

      <div className="calibration-note">
        Muista: {score}% ei tarkoita, että väite on {score}-prosenttisesti totta.
        Pistemäärä on kielimallin kalibroimaton arvio — tarkkuutta ei ole vielä
        mitattu (suunniteltu kerrokseen 8, ei toteutettu).
      </div>
    </div>
  )
}