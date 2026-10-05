from uuid import uuid4

from app.realtime import Sala


class FalsoWs:
    def __init__(self) -> None:
        self.enviadas: list[dict] = []
        self.caida = False

    async def send_json(self, msg: dict) -> None:
        if self.caida:
            raise RuntimeError("conexão perdida")
        self.enviadas.append(msg)


async def test_presenca_agrupa_abas_da_mesma_pessoa_e_prioriza_quem_edita():
    sala, ana = Sala(), uuid4()
    ws1, ws2, ws3 = FalsoWs(), FalsoWs(), FalsoWs()
    c1 = await sala.entrar(ws1, ana, "Ana")  # type: ignore[arg-type]
    c2 = await sala.entrar(ws2, ana, "Ana")  # type: ignore[arg-type]
    await sala.entrar(ws3, uuid4(), "Beto")  # type: ignore[arg-type]
    await sala.atualizar_presenca(c1, "negocios", None)
    await sala.atualizar_presenca(c2, "clientes", "Alfa Ltda")
    pessoas = {p["nome"]: p for p in sala.pessoas()}
    assert len(pessoas) == 2 and pessoas["Ana"]["editando"] == "Alfa Ltda"
    assert ws3.enviadas[-1]["tipo"] == "presenca"


async def test_alteracao_e_limpeza_de_conexao_caida():
    sala = Sala()
    a, b = FalsoWs(), FalsoWs()
    await sala.entrar(a, uuid4(), "A")  # type: ignore[arg-type]
    await sala.entrar(b, uuid4(), "B")  # type: ignore[arg-type]
    b.caida = True
    await sala.publicar_alteracao({"clientes", "negocios"})
    assert a.enviadas[-1] == {"tipo": "alterado", "recursos": ["clientes", "negocios"]}
    assert len(sala.conexoes) == 1
    await sala.publicar_alteracao(set())  # nada a avisar
    assert len(a.enviadas) == 3
