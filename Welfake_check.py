# Welfake_check.py
# Yleistyvyystesti (1.16, valinnainen): opetetaan ISOT-datasetilla,
# testataan täysin erillisellä WELFake-datasetilla. Tarkoitus: nähdä
# yleistyykö malli lähteestä toiseen vai oppiiko se vain ISOT:in
# omia muotoiluvihjeitä (ks. README "Tunnettu datavuoto").

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report


def load_isot(fake_path="data/Fake.csv", real_path="data/True.csv"):
    """ISOT: opetusdata."""
    fake = pd.read_csv(fake_path)[["text"]]
    fake["label"] = 0
    real = pd.read_csv(real_path)[["text"]]
    real["label"] = 1
    return pd.concat([fake, real], ignore_index=True)


def load_welfake(isot_texts, path="data/WELFake_Dataset.csv"):
    """WELFake: testidata. Tekee kolme korjausta ennen käyttöä:
    puuttuvien tekstirivien poiston, label-inversion korjauksen ja
    ISOT:in kanssa päällekkäisten rivien poiston.
    """
    df = pd.read_csv(path)[["text", "label"]]

    n_before = len(df)
    df = df.dropna(subset=["text"])
    print(f"WELFake: pudotettu {n_before - len(df)} riviä joissa text "
          f"puuttui ({n_before} -> {len(df)})")

    # KORJAUS (1.16-löydös): WELFaken CSV:n label-arvot ovat käänteiset
    # sen omaan Zenodo-dokumentaatioon nähden ("0 = fake, 1 = real" on
    # väitetty, mutta data on todellisuudessa 0 = real, 1 = fake).
    # Todistettu kahdella riippumattomalla tavalla:
    #   1) käännettyjen labelien tarkkuus 0.83 vs. alkuperäisten 0.17 -
    #      tasapainoisella testijoukolla alle satunnaistarkkuuden
    #      (~50 %) jäävä tulos on itsessään merkki systemaattisesta
    #      etumerkkivirheestä, ei siitä ettei mallissa olisi signaalia
    #   2) manuaalinen luku: label=0-rivit ovat aidosti Reuters-tyylistä
    #      uutistekstiä, label=1-rivit lähteetöntä/kärjistävää tekstiä
    df["label"] = 1 - df["label"].astype(int)

    # Duplikaattien poisto: WELFake jakaa osan lähdeartikkeleistaan
    # ISOT:in kanssa. Jos näitä ei poisteta testidatasta, testi mittaisi
    # osittain muistamista eikä yleistymistä.
    n_before = len(df)
    df = df[~df["text"].isin(isot_texts)]
    print(f"WELFake: poistettu {n_before - len(df)} riviä jotka "
          f"esiintyvät myös ISOT:issa ({n_before} -> {len(df)})")

    return df


def main():
    isot = load_isot()
    welfake = load_welfake(isot["text"])

    vec = TfidfVectorizer(max_features=5000, stop_words="english")
    model = LogisticRegression(max_iter=1000)

    X_train, y_train = vec.fit_transform(isot["text"]), isot["label"]
    X_test, y_test = vec.transform(welfake["text"]), welfake["label"]
    model.fit(X_train, y_train)

    print("\nYleistyvyystesti: opetettu ISOT:illa, testattu WELFakella "
          "(korjatuilla labeleilla)")
    print(classification_report(y_test, model.predict(X_test)))

    # Rehellisyyshuomio: korkea tarkkuus ei todista puhdasta sisällön
    # yleistymistä. WELFaken korjattu "real"-luokka on sekin pääosin
    # Reuters-lähtöistä, joten osa tarkkuudesta voi yhä selittyä samalla
    # lähdesignaalilla kuin ISOT:in oma datavuoto (ks. README "Tunnettu
    # datavuoto (ISOT)") eikä aidosta väitteen totuudenmukaisuuden
    # arvioinnista.
    print("\nHuom: korkea tarkkuus ei todista puhdasta yleistymistä - "
          "ks. kommentti koodissa.")


if __name__ == "__main__":
    main()