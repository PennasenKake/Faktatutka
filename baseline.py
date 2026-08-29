# baseline.py
# TF-IDF + logistinen regressio ISOT-datasetille, ja konkreettinen tarkistus
# tunnetulle datavuodolle (askeleet 1.5-1.8).

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# --- 1. Data sisään ja labelointi ---
# Fake.csv ja True.csv ovat kaksi erillistä tiedostoa ilman valmista
# label-saraketta - lisätään se itse ennen yhdistämistä.
fake = pd.read_csv("data/Fake.csv"); fake["label"] = 0   # 0 = fake
real = pd.read_csv("data/True.csv"); real["label"] = 1   # 1 = real

# concat liittää rivit peräkkäin (ei sarakkeittain), reset_index nollaa
# indeksin ettei kahdella rivillä ole samaa indeksinumeroa yhdistämisen jälkeen.
df = pd.concat([fake, real]).reset_index(drop=True)

# --- 2. Train/test-jako ---
# stratify=df["label"] varmistaa että molemmat luokat pysyvät samassa
# suhteessa sekä train- että test-osassa - ilman sitä jako voisi sattumalta
# vinoutua, mikä vääristäisi classification_reportin.
# random_state=42 tekee jaosta toistettavan: sama tulos joka ajokerralla.
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"])

# --- 3. TF-IDF-vektorisointi ---
# fit_transform train-datalla: TF-IDF oppii sanaston JA muuntaa samalla.
# transform (ei fit) test-datalla: käytetään train-datasta opittua sanastoa,
# ei opita uutta - muuten testidata "vuotaisi" vektorisointiin.
# max_features=5000 rajaa yleisimpiin sanoihin, stop_words="english"
# poistaa merkityksettömät täytesanat (the, is, and...).
vec = TfidfVectorizer(max_features=5000, stop_words="english")
X_train_v = vec.fit_transform(X_train)
X_test_v = vec.transform(X_test)

# --- 4. Malli ---
# max_iter=1000 nostettu oletuksesta (100), koska 5000 piirrettä ei aina
# konvergoi oletusiteraatiomäärässä - ilman tätä sklearn varoittaisi.
model = LogisticRegression(max_iter=1000)
model.fit(X_train_v, y_train)
print(classification_report(y_test, model.predict(X_test_v)))

# --- 5. Datavuototarkistus (1.8) ---
# ISOT:ssa tosi-uutiset ovat lähes kaikki Reutersilta ja usein muotoa
# "WASHINGTON (Reuters) - ...". Jos "Reuters"-maininnan yleisyys eroaa
# rajusti luokkien välillä, malli on voinut oppia tunnistamaan LÄHTEEN
# kirjoitustyylin sisällön totuudenmukaisuuden sijaan - mikä selittäisi
# epärealistisen korkean tarkkuuden kohdasta 4.
leak_check = df["text"].str.contains("Reuters", case=False).groupby(df["label"]).mean()
print("\nReuters-maininnan osuus luokittain (0 = fake, 1 = real):")
print(leak_check.round(3))

testit = [
    "Helsinki (STT) - Suomen hallitus ilmoitti tiistaina uudesta koulutusuudistuksesta.",
    "WASHINGTON (Reuters) - The moon is made of cheese, scientists confirm.",
]
X_test_manual = vec.transform(testit)
print(model.predict(X_test_manual))       # 0 = fake, 1 = real
print(model.predict_proba(X_test_manual)) # kuinka varma malli on