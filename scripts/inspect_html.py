# inspect_html.py
# Kertaluonteinen tiedustelu ennen varsinaisen scraperin kirjoittamista.
#
# HUOM Claudelta: en pääse itse tekemään HTTP-pyyntöjä faktabaari.fi:hin
# tästä ympäristöstä (organisaation egress-policy estää sekä pilvi-
# sandboxin että laitteesi device_bash-VM:n suorat HTTP-yhteydet ulos —
# molemmat testattu, molemmat saivat 403:n proxylta). WebFetch-työkalu
# näkee sivun vain markdown-muunnettuna tekstinä, ei raakaa HTML:ää,
# joten en voi lukea oikeita CSS-luokkia sieltä. Tarvitsen siis sinun
# koneesi oikean, rajoittamattoman verkkoyhteyden tähän yhteen
# kertaluonteiseen ajoon.
#
# Aja tämä itse (`python inspect_html.py`) ja liitä koko tuloste takaisin.
# Sen perusteella lukitsen scraperin oikeat valitsimet (title/date/tags/
# body) sen sijaan että arvaisin ne sokkona pelkän markdown-yhteenvedon
# perusteella.
import re
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Puuttuu paketteja. Asenna ensin:")
    print("  pip install requests beautifulsoup4 lxml")
    sys.exit(1)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FaktatutkaBot/0.1; "
                  "opinnaytetyo/portfolio-projekti, ei kaupallinen)"
}

ARTICLE_URL = (
    "https://faktabaari.fi/fakta/"
    "vaite-suomen-kaksinkertaisesta-covid-19-ylikuolleisuudesta-on-virheellinen/"
)
LISTING_URL = "https://faktabaari.fi/fakta/sivu/2/"


def fetch(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def inspect_article():
    print("=" * 70)
    print("ARTIKKELISIVU:", ARTICLE_URL)
    print("=" * 70)
    soup = fetch(ARTICLE_URL)

    print("\n--- <title> ---")
    print(soup.title.string if soup.title else "(ei löytynyt)")

    print("\n--- <h1>-elementit ---")
    for h1 in soup.find_all("h1"):
        print(f"  class={h1.get('class')!r}  text={h1.get_text(strip=True)[:100]!r}")

    print("\n--- Relevantit <meta>-tagit (og:*, article:*) ---")
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name") or ""
        if prop.startswith("og:") or prop.startswith("article:"):
            print(f"  {prop} = {meta.get('content')!r}")

    print("\n--- <time>-elementit ---")
    for t in soup.find_all("time"):
        print(f"  datetime={t.get('datetime')!r}  text={t.get_text(strip=True)!r}")

    print('\n--- Linkit rel="tag" (WordPressin tyypillinen tagi-merkintä) ---')
    for a in soup.find_all("a", rel="tag"):
        print(f"  {a.get_text(strip=True)!r}  href={a.get('href')!r}")

    print("\n--- Leipätekstin ehdokkaat (div/article, sanamäärä > 50) ---")
    candidates = []
    for tag in soup.find_all(["div", "article", "section"]):
        text = tag.get_text(" ", strip=True)
        wc = len(text.split())
        if wc > 50:
            candidates.append((wc, tag.name, tag.get("class"), tag.get("id")))
    candidates.sort(key=lambda c: c[0])
    for wc, name, cls, _id in candidates[-15:]:
        print(f"  {wc:5d} sanaa  <{name}>  class={cls!r}  id={_id!r}")

    print("\n--- Ensimmäiset 500 merkkiä <body>:n tekstistä (tarkistukseksi) ---")
    body = soup.body.get_text(" ", strip=True) if soup.body else ""
    print(body[:500])


def inspect_listing():
    print("\n\n" + "=" * 70)
    print("LISTAUSSIVU:", LISTING_URL)
    print("=" * 70)
    soup = fetch(LISTING_URL)

    print("\n--- Linkit jotka täsmäävät /fakta/<slug>/-kaavaan ---")
    pattern = re.compile(r"^https://faktabaari\.fi/fakta/[^/]+/?$")
    found = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if pattern.match(href):
            found.add(href)
    print(f"  Löytyi {len(found)} uniikkia artikkelilinkkiä tällä sivulla")
    for href in sorted(found)[:5]:
        print(f"   {href}")

    print("\n--- Paginaatio-linkit (sivu N) ---")
    pag_pattern = re.compile(r"/fakta/sivu/(\d+)/?$")
    pages = set()
    for a in soup.find_all("a", href=True):
        m = pag_pattern.search(a["href"])
        if m:
            pages.add(int(m.group(1)))
    print(f"  Sivunumerot linkeissä: {sorted(pages)}")


if __name__ == "__main__":
    inspect_article()
    inspect_listing()
    print("\n\nValmis. Kopioi koko yllä oleva tuloste takaisin Claudelle.")
