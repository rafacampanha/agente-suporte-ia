"""Busca semântica simples (TF-IDF + similaridade de cosseno) sobre a base de artigos."""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_PADRAO = Path(__file__).resolve().parents[1] / "base" / "artigos.json"
STOPWORDS = """a o as os de da do das dos e em no na nos nas um uma para por com sem que se meu minha
nao não esta está estou ao aos é ser foi como qual quando onde porque mais muito já tem ter""".split()


def normalizar(txt: str) -> str:
    return unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().lower()


@dataclass
class Resultado:
    artigo: dict
    score: float


class BaseConhecimento:
    def __init__(self, caminho: Path = BASE_PADRAO):
        self.artigos: list[dict] = json.loads(Path(caminho).read_text(encoding="utf-8"))
        docs = [normalizar(f"{a['titulo']} {a['titulo']} {' '.join(a['tags'])} {a['conteudo']}") for a in self.artigos]
        self.vetorizador = TfidfVectorizer(stop_words=[normalizar(s) for s in STOPWORDS], ngram_range=(1, 2), sublinear_tf=True)
        self.matriz = self.vetorizador.fit_transform(docs)

    def buscar(self, pergunta: str, k: int = 3, minimo: float = 0.08) -> list[Resultado]:
        q = self.vetorizador.transform([normalizar(pergunta)])
        scores = cosine_similarity(q, self.matriz).ravel()
        ordem = scores.argsort()[::-1][:k]
        return [Resultado(self.artigos[i], float(scores[i])) for i in ordem if scores[i] >= minimo]
