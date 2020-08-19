import torch
import numpy as np
from collections import Counter
from sklearn.base import TransformerMixin, BaseEstimator
from unidecode import unidecode

__all__ = [
    'Projector',
    'LabelEncoder',
    'BasicTokenizer',
    'TokensEncoder',
    'ToTensor'
]

class Projector(TransformerMixin, BaseEstimator):
    def __init__(self, keys):
        self.keys = keys if isinstance(keys, list) else [keys]

    def get(self, x):
        for key in self.keys:
            x = x.get(key)
        return x

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [self.get(x) for x in X]


class LabelEncoder(TransformerMixin, BaseEstimator):
    class UnknownLabel:
        def __repr__(self):
            return "<UNK>"

    def __init__(self, is_target=False):
        self.is_target = is_target

    def fit(self, X, y=None):
        self.vocab = [x for x in sorted(set(X)) if x is not None]
        if not self.is_target:
            self.vocab.insert(0, self.UnknownLabel())
        self.category2code = {x:i for i,x in enumerate(self.vocab)}
        return self

    def get_category_code(self, x):
        return self.category2code.get(x) if self.is_target else self.category2code.get(x, 0)

    def transform(self, X):
        return np.array([self.get_category_code(x) for x in X], dtype=np.int)


class BasicTokenizer(TransformerMixin, BaseEstimator):
    def __init__(self, lower=True, map_to_ascii=True):
        self.lower = lower
        self.map_to_ascii = map_to_ascii

    def tokenize(self, text):
        if text is None:
            text = ""
        elif not isinstance(text, str):
            text = str(text)

        if self.map_to_ascii:
            text = unidecode(text)
        if self.lower:
            text = text.lower()
        res = []
        for token in text.split():
            while token and not token[-1].isalnum():
                token = token[:-1]
            while token and not token[0].isalnum():
                token = token[1:]
            if token:
                res.append(token)
        return res

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [self.tokenize(x) for x in X]


class TokensEncoder(TransformerMixin, BaseEstimator):
    class PaddingToken:
        def __repr__(self):
            return "<PAD>"

    class UnknownToken:
        def __repr__(self):
            return "<UNK>"

    def __init__(self, max_len, max_vocab, min_freq):
        self.max_len = max_len
        self.max_vocab = max_vocab
        self.min_freq = min_freq

    def fit(self, X, y=None):
        token_freq = Counter()
        for sentence in X:
            token_freq.update(sentence)

        vocab = [token for token, count in token_freq.most_common(self.max_vocab)
                    if count >= self.min_freq]
        vocab.insert(0, self.PaddingToken())
        vocab.insert(1, self.UnknownToken())
        self.token2code = {token: i for i, token in enumerate(vocab)}
        self.vocab = vocab
        return self

    def transform(self, X):
        out = np.zeros((len(X), self.max_len), dtype=np.int)
        for i, sentence in enumerate(X):
            codes = [self.token2code.get(token, 1) for token in sentence[:self.max_len]]
            sentence_len = min(len(sentence), self.max_len)
            out[i,:sentence_len] = np.array(codes)
        return out


class ToTensor(TransformerMixin, BaseEstimator):
    def __init__(self, dtype=None):
        self.dtype = dtype

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return torch.tensor(X, dtype=self.dtype)