# tfidf_check.py
# Käsinlasku vs. sklearn: tarkistetaan ymmärretäänkö IDF:n mekaniikka,
# ei vain kutsuta funktiota sokkona (1.15).

from sklearn.feature_extraction.text import TfidfVectorizer
import math

toy_docs = ["kissa istuu matolla", "koira juoksee pihalla"]

vec_toy = TfidfVectorizer()
vec_toy.fit(toy_docs)

idx = list(vec_toy.get_feature_names_out()).index("kissa")
sklearn_idf = vec_toy.idf_[idx]
print("sklearnin laskema IDF sanalle 'kissa':", sklearn_idf)

# Vaihe 1: naiivi kaava (kuten "Opi tämä ensin" -laatikossa aiemmin)
# n = dokumenttien määrä, df = montako dokumenttia sisältää sanan
n, df = 2, 1
naive_idf = math.log(n / df)
print("Naiivi kaava log(n/df):        ", naive_idf, "<- EI täsmää")

# Vaihe 2: sklearnin oikea, tasoitettu (smoothed) kaava
smoothed_idf = math.log((1 + n) / (1 + df)) + 1
print("Tasoitettu ln((1+n)/(1+df))+1: ", smoothed_idf, "<- täsmää")

assert abs(sklearn_idf - smoothed_idf) < 1e-9, "Jotain meni pieleen kaavassa"
print("\nVahvistettu: sklearn käyttää tasoitettua kaavaa, ei oppikirjan naiivia versiota.")