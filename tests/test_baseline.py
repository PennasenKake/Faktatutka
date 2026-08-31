# tests/test_baseline.py
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer


def test_model_loads(model):
    assert isinstance(model, LogisticRegression)


def test_vectorizer_loads(vectorizer):
    assert isinstance(vectorizer, TfidfVectorizer)