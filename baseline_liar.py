import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

mapping = {
    "true": 1, "mostly-true": 1, "half-true": 1,
    "barely-true": 0, "false": 0, "pants-fire": 0,
}

def load_liar(path):
    df = pd.read_csv(path, sep="\t", header=None)
    df = df.dropna(how="all")
    df["label"] = df[2].map(mapping)
    assert df["label"].isna().sum() == 0, f"Mäppäämättömiä luokkia: {df[df['label'].isna()][2].unique()}"
    return df

train_df = load_liar("data/train2.tsv")
test_df = load_liar("data/test2.tsv")

print("Train:", train_df["label"].value_counts().to_dict())
print("Test: ", test_df["label"].value_counts().to_dict())

# statement (sarake 3) on itse väite - sama kenttä jota mallin pitää arvioida.
vec = TfidfVectorizer(max_features=5000, stop_words="english")
X_train_v = vec.fit_transform(train_df[3])
X_test_v = vec.transform(test_df[3])

model = LogisticRegression(max_iter=1000)
model.fit(X_train_v, train_df["label"])
print(classification_report(test_df["label"], model.predict(X_test_v)))