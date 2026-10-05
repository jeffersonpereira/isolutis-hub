import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db import SessionLocal, definir_empresa_da_transacao, definir_usuario_da_transacao
from app.models import Usuario, UsuarioEmpresa
from app.realtime import sala
from app.security import ler_token

router = APIRouter(tags=["Tempo real"])

CODIGO_NAO_AUTORIZADO = 4401


@router.websocket("/ws")
async def tempo_real(ws: WebSocket) -> None:
    """Primeira mensagem do cliente: {"tipo": "auth", "token": "<jwt>"}. Depois, presença e avisos de alteração."""
    await ws.accept()
    try:
        primeira = json.loads(await ws.receive_text())
    except (WebSocketDisconnect, ValueError):
        await ws.close(code=CODIGO_NAO_AUTORIZADO)
        return
    identidade = ler_token(str(primeira.get("token", ""))) if primeira.get("tipo") == "auth" else None
    try:
        empresa_id = UUID(str(primeira.get("empresa_id", "")))
    except ValueError:
        empresa_id = None
    usuario_id = identidade[0] if identidade else None
    async with SessionLocal() as sessao:
        usuario = await sessao.get(Usuario, usuario_id) if usuario_id else None
        nome, ativo, versao = (usuario.nome, usuario.ativo, usuario.versao_sessao) if usuario else ("", False, -1)
        membership = None
        if usuario and empresa_id:
            await definir_usuario_da_transacao(sessao, usuario.id)
            membership = await sessao.get(UsuarioEmpresa, (empresa_id, usuario.id))
            if membership and membership.ativo:
                await definir_empresa_da_transacao(sessao, empresa_id)
    if usuario is None or not ativo or identidade is None or versao != identidade[1] or not membership or not membership.ativo:
        await ws.close(code=CODIGO_NAO_AUTORIZADO)
        return

    assert empresa_id is not None  # membership válida só pode existir quando o UUID foi fornecido
    con = await sala.entrar(ws, usuario.id, empresa_id, nome)
    try:
        while True:
            mensagem = json.loads(await ws.receive_text())
            if mensagem.get("tipo") == "presenca":
                await sala.atualizar_presenca(con, str(mensagem.get("area") or ""), mensagem.get("editando"))
    except (WebSocketDisconnect, ValueError):
        pass
    finally:
        await sala.sair(con)
