# faktabaari_scraper.py
# Kerää Faktabaari.fi:n faktantarkistukset RAG-korpukseksi (kerros 4).
#
# Valitsimet (h1/og:title, article:published_time, article.post__content)
# on todennettu inspect_html.py:n ajolla oikeaa sivua vasten 30.9.2026 -
# ei arvattu. Skeema: {title, url, date, body_text} - EI tags-kenttaa,
# ks. README 4.2: kokeiltiin, 0/208 artikkelista loytyi mitaan rel="tag"-
# tai luokkanimipohjaisella haulla taydessa ajossa, pudotettu pois
# kokonaan sen sijaan etta jatettaisiin aina-tyhja kentta nayttamaan
# dataa jota ei ole.
#
# HUOM Claudelta: en voi ajaa tätä itse (ei verkkoyhteyttä faktabaari.fi:hin
# tästä ympäristöstä). Aja itse, katso tuloste, liitä takaisin.
#
# SUOSITUS: aja ensin --dry-run, joka vain kerää ja tulostaa artikkeli-
# URLit (ei hae 200 artikkelia) - tarkista että lista näyttää järkevältä
# (pelkkiä yksittäisiä faktantarkistuksia, ei esim. tagi- tai
# arkistosivuja) ENNEN kuin ajat täyden scrapen. Täysi ajo tekee n.
# 210-225 HTTP-pyyntöä 1.5s viiveellä = n. 5-6 min.
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Puuttuu paketteja. Asenna ensin:")
    print("  pip install requests beautifulsoup4 lxml")
    sys.exit(1)

BASE = "https://faktabaari.fi"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FaktatutkaBot/0.1; "
                  "opinnaytetyo/portfolio-projekti, ei kaupallinen)"
}
DELAY_SECONDS = 1.5  # kohtelias viive pyyntöjen välillä - ei hakata sivustoa
NUM_PAGES = 14  # todennettu 30.9.2026 (inspect_html.py, "Sivunumerot
                 # linkeissä" -> [2,3,4,5,14]) - jos tämä scraperi ajetaan
                 # paljon myöhemmin, sivumäärä on voinut kasvaa, tarkista.

# Huomaa: linkit sivulla ovat SUHTEELLISIA ("/fakta/jotain/"), ei
# täysiä https://-URLeja - alkuperäinen inspect_html.py:n regex vaati
# https-etuliitettä ja siksi löysi 0 osumaa listaussivulta. Korjattu.
ARTICLE_LINK_RE = re.compile(r"^/fakta/([^/]+)/?$")


def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    # requests arvaa enkoodauksen HTTP-headerista kun sitä ei ole
    # eksplisiittisesti ilmoitettu, ja päätyy tällä sivustolla väärään
    # (ISO-8859-1) vaikka sisältö on UTF-8 - todennettu inspect_html.py:n
    # ajossa ("VÃ¤ite" pitäisi olla "Väite"). Pakotetaan oikeaksi.
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "lxml")


def collect_article_urls(verbose: bool = True) -> list[str]:
    urls = set()
    listing_pages = [f"{BASE}/fakta/"] + [
        f"{BASE}/fakta/sivu/{n}/" for n in range(2, NUM_PAGES + 1)
    ]
    for page_url in listing_pages:
        soup = get_soup(page_url)
        new_on_page = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/fakta/sivu/" in href:
                continue  # paginaatiolinkki, ei artikkeli
            m = ARTICLE_LINK_RE.match(href)
            if m:
                full = BASE + href.rstrip("/") + "/"
                if full not in urls:
                    new_on_page += 1
                urls.add(full)
        if verbose:
            print(f"  {page_url}: +{new_on_page} uutta, {len(urls)} yhteensä")
        time.sleep(DELAY_SECONDS)
    return sorted(urls)


def parse_article(url: str) -> dict | None:
    soup = get_soup(url)

    title_tag = soup.find("meta", property="og:title")
    title = title_tag["content"].strip() if title_tag and title_tag.get("content") else (
        soup.h1.get_text(strip=True) if soup.h1 else None
    )

    date_tag = soup.find("meta", property="article:published_time")
    date = date_tag["content"] if date_tag else None

    body_tag = soup.find("article", class_="post__content")
    body_text = body_tag.get_text(" ", strip=True) if body_tag else None

    if not title or not body_text:
        return None  # ei tarpeeksi sisältöä, jätetään korpuksen ulkopuolelle

    return {
        "title": title,
        "url": url,
        "date": date,
        "body_text": body_text,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Kerää ja tulosta vain artikkeli-URLit, älä hae sisältöä.",
    )
    args = parser.parse_args()

    print("Kerätään artikkeli-URLit kaikilta sivuilta...")
    urls = collect_article_urls()
    print(f"\nYhteensä {len(urls)} uniikkia artikkeli-URLia löytyi.\n")

    if args.dry_run:
        print("--dry-run: tulostetaan koko lista tarkistettavaksi:\n")
        for u in urls:
            print(f"  {u}")
        print(f"\n{len(urls)} URLia. Tarkista että lista näyttää järkevältä "
              f"(pelkkiä faktantarkistuksia) ennen täyttä ajoa.")
        return

    articles = []
    failed = []

    for i, url in enumerate(urls, 1):
        try:
            article = parse_article(url)
        except Exception as e:
            print(f"  [{i}/{len(urls)}] VIRHE {url}: {e}")
            failed.append(url)
            continue

        if article is None:
            print(f"  [{i}/{len(urls)}] OHITETTU (ei title/body) {url}")
            failed.append(url)
            continue

        articles.append(article)
        print(f"  [{i}/{len(urls)}] OK: {article['title'][:60]}")
        time.sleep(DELAY_SECONDS)

    out = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "faktabaari.fi",
        "count": len(articles),
        "articles": articles,
    }
    with open("faktabaari_corpus.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nValmis. {len(articles)} artikkelia tallennettu "
          f"faktabaari_corpus.json-tiedostoon.")
    print(f"Epäonnistuneita/ohitettuja: {len(failed)}")
    if failed:
        print("\nEpäonnistuneet/ohitetut URLit:")
        for u in failed:
            print(f"  {u}")


if __name__ == "__main__":
    main()
