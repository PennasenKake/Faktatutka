# baseline_liar.py
# Sama TF-IDF + logistinen regressio -putki kuin baseline.py:ssa, ajettuna
# LIAR-PLUS-datalla. Tarkoitus: verrata ISOT:in tulokseen ja osoittaa kuinka
# paljon ISOT:in 99 % oli lähdevuotoa, ei mallin oikeaa kykyä (askel 1.12).

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# --- 1. Binäärimappaus (askel 1.10) ---
# LIAR:n 6 luokkaa ovat asteikko (true -> pants-fire), ei kolme paria.
# Tämä raja on tulkinnanvarainen päätös - dokumentoitu README:hen erikseen,
# ei kirjoitettu tähän hiljaisena oletuksena.
mapping = {
    "true": 1, "mostly-true": 1, "half-true": 1,          # "vähintään puoliksi totta" -> uskottava
    "barely-true": 0, "false": 0, "pants-fire": 0,          # loput -> ei-uskottava
}

def load_liar(path):
    # header=None: tiedostossa ei ole otsikkoriviä, sarakkeet tunnistetaan
    # vain indeksin perusteella (0-15, ks. README).
    df = pd.read_csv(path, sep="\t", header=None)

    # train2.tsv sisälsi 2 täysin tyhjää riviä lähdetiedostossa - pudotetaan
    # ne ennen mappausta, muuten label-sarake sisältäisi NaN-arvoja.
    df = df.dropna(how="all")

    # Sarake 2 on label alkuperäisessä tsv:ssä (sarake 1 on pelkkä id-string
    # kuten "2635.json", ei totuusarvo - helppo sekoittaa keskenään).
    df["label"] = df[2].map(mapping)

    # Jos joku arvo jää mäppäämättä, se on merkki datasta jota ei odotettu
    # (esim. kirjoitusvirhe alkuperäisessä tiedostossa) - ei pidä jatkaa
    # hiljaa NaN-labeleilla.
    assert df["label"].isna().sum() == 0, \
        f"Mäppäämättömiä luokkia: {df[df['label'].isna()][2].unique()}"
    return df

# --- 2. Data sisään: käytetään LIAR-PLUS:n omaa train/test-jakoa ---
# Toisin kuin ISOT:issa (train_test_split), tässä jako tulee valmiina
# datasetin tekijöiltä - se on tarkoituksella erotettu pidättäytymisjoukko,
# joten sen käyttäminen antaa luotettavamman kuvan yleistymisestä kuin
# oma satunnaisjako samasta tiedostosta.
train_df = load_liar("data/train2.tsv")
test_df = load_liar("data/test2.tsv")

print("Train:", train_df["label"].value_counts().to_dict())
print("Test: ", test_df["label"].value_counts().to_dict())

# --- 3. TF-IDF-vektorisointi ---
# Sarake 3 on itse väite (statement) - sama kenttä jota mallin oikeasti
# pitää arvioida, ei koko artikkelia kuten ISOT:issa.
vec = TfidfVectorizer(max_features=5000, stop_words="english")
X_train_v = vec.fit_transform(train_df[3])
X_test_v = vec.transform(test_df[3])   # transform, ei fit - sama periaate kuin baseline.py:ssä

# --- 4. Malli ---
model = LogisticRegression(max_iter=1000)
model.fit(X_train_v, train_df["label"])
print(classification_report(test_df["label"], model.predict(X_test_v)))