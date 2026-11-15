"""Regras de triagem: prioridade e decisão de escalar para um humano."""
from __future__ import annotations

from dataclasses import dataclass

from .base_conhecimento import normalizar

URGENTE = ["fora do ar", "parado", "ninguem consegue", "todos os usuarios", "urgente", "erro 500", "indisponivel"]
ALTA = ["nao consigo", "bloqueado", "erro", "falha", "nao funciona"]
PEDE_HUMANO = ["falar com atendente", "falar com humano", "abrir chamado", "atendente"]


@dataclass
class Triagem:
    prioridade: str
    escalar: bool
    motivo: str


def triar(mensagem: str, melhor_score: float, limiar_confianca: float = 0.2) -> Triagem:
    t = normalizar(mensagem)
    if any(p in t for p in PEDE_HUMANO):
        return Triagem("Média", True, "usuário pediu atendimento humano")
    if any(p in t for p in URGENTE):
        return Triagem("Crítica", True, "possível incidente afetando vários usuários")
    prioridade = "Alta" if any(p in t for p in ALTA) else "Baixa"
    if melhor_score < limiar_confianca:
        return Triagem(prioridade, True, "nenhum artigo da base responde com confiança")
    return Triagem(prioridade, False, "respondido pela base de conhecimento")
