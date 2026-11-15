import pytest

from agente.agente import AgenteSuporte
from agente.base_conhecimento import BaseConhecimento


@pytest.fixture(scope="module")
def agente():
    return AgenteSuporte(BaseConhecimento(), usar_llm=False)


@pytest.mark.parametrize("pergunta,artigo", [
    ("esqueci minha senha e não consigo entrar", "KB-001"),
    ("o painel está com dados desatualizados", "KB-002"),
    ("deu erro ao importar a planilha de lançamentos", "KB-003"),
    ("como exporto a tabela para o excel?", "KB-005"),
])
def test_busca_encontra_artigo_certo(agente, pergunta, artigo):
    assert agente.base.buscar(pergunta)[0].artigo["id"] == artigo


def test_resposta_offline_cita_fonte(agente):
    r = agente.responder("como redefinir a senha")
    assert not r.triagem.escalar
    assert "[KB-001]" in r.texto


def test_incidente_vai_para_humano_com_prioridade_critica(agente):
    r = agente.responder("o sistema está fora do ar para todos os usuários")
    assert r.triagem.escalar and r.triagem.prioridade == "Crítica"


def test_pergunta_fora_da_base_escala(agente):
    r = agente.responder("qual a previsão do tempo amanhã?")
    assert r.triagem.escalar
    assert "nenhum artigo" in r.triagem.motivo


def test_pedido_de_humano(agente):
    assert agente.responder("quero falar com atendente").triagem.escalar
