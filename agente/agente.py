"""Agente de suporte de 1º nível: busca na base, tria e responde (com LLM opcional).

Sem chave de API ele responde com o artigo mais relevante (modo offline).
Com ANTHROPIC_API_KEY definida, usa o Claude para redigir a resposta
*somente* a partir dos artigos encontrados (RAG), evitando inventar informação.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .base_conhecimento import BaseConhecimento, Resultado
from .triagem import Triagem, triar

PROMPT_SISTEMA = """Você é um agente de suporte técnico de 1º nível, educado e objetivo.
Responda em português, em no máximo 6 linhas, usando APENAS as informações dos artigos fornecidos.
Se os artigos não resolverem, diga que vai encaminhar para um analista. Nunca invente procedimentos.
Cite o ID do artigo usado no final, entre colchetes."""


@dataclass
class Resposta:
    texto: str
    triagem: Triagem
    fontes: list[str] = field(default_factory=list)


class AgenteSuporte:
    def __init__(self, base: BaseConhecimento | None = None, usar_llm: bool | None = None):
        self.base = base or BaseConhecimento()
        self.usar_llm = bool(os.getenv("ANTHROPIC_API_KEY")) if usar_llm is None else usar_llm

    def responder(self, mensagem: str) -> Resposta:
        resultados = self.base.buscar(mensagem)
        melhor = resultados[0].score if resultados else 0.0
        tri = triar(mensagem, melhor)
        fontes = [r.artigo["id"] for r in resultados]

        if tri.escalar:
            texto = (f"Vou encaminhar seu caso para um analista ({tri.motivo}). "
                     f"Prioridade definida: {tri.prioridade}.")
            if resultados:
                texto += f"\nEnquanto isso, este artigo pode ajudar: {resultados[0].artigo['titulo']} [{fontes[0]}]"
            return Resposta(texto, tri, fontes)

        texto = self._gerar_llm(mensagem, resultados) if self.usar_llm else self._gerar_offline(resultados[0])
        return Resposta(texto, tri, fontes)

    @staticmethod
    def _gerar_offline(r: Resultado) -> str:
        a = r.artigo
        return f"{a['titulo']}:\n{a['conteudo']}\n[{a['id']}]"

    @staticmethod
    def _gerar_llm(mensagem: str, resultados: list[Resultado]) -> str:
        import anthropic  # dependência opcional

        contexto = "\n\n".join(f"[{r.artigo['id']}] {r.artigo['titulo']}\n{r.artigo['conteudo']}" for r in resultados)
        cliente = anthropic.Anthropic()
        msg = cliente.messages.create(
            model=os.getenv("MODELO_LLM", "claude-sonnet-4-5"),
            max_tokens=400,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": f"Artigos:\n{contexto}\n\nPergunta do usuário: {mensagem}"}],
        )
        return msg.content[0].text


def main() -> None:
    agente = AgenteSuporte()
    print("Agente de suporte (digite 'sair' para encerrar)\n")
    while (pergunta := input("Você: ").strip()).lower() not in {"sair", "exit", "q"}:
        r = agente.responder(pergunta)
        print(f"\nAgente: {r.texto}\n  ↳ prioridade={r.triagem.prioridade} escalar={r.triagem.escalar} fontes={r.fontes}\n")


if __name__ == "__main__":
    main()
