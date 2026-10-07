"""Cria ou redefine um administrador de empresa usando a credencial migradora.

Exemplo: python -m app.scripts.criar_admin --email voce@empresa.com.br --nome "Seu Nome" --empresa-nome "iSolutis"
A senha é pedida no terminal. HUB_MIGRATION_DATABASE_URL deve apontar para a credencial de provisionamento.
"""

import argparse
import asyncio
import getpass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import get_settings
from app.db import criar_engine
from app.models import Empresa, Usuario, UsuarioEmpresa
from app.security import TAMANHO_MINIMO_SENHA, gerar_hash


async def criar(email: str, nome: str, senha: str, empresa_id: UUID | None, empresa_nome: str | None) -> bool:
    url = get_settings().migration_database_url
    if not url:
        raise SystemExit("Defina HUB_MIGRATION_DATABASE_URL; este script não usa a credencial runtime.")
    engine = criar_engine(url)
    SessaoMigracao = async_sessionmaker(engine, expire_on_commit=False)
    async with SessaoMigracao() as sessao:
        usuario = await sessao.scalar(select(Usuario).where(Usuario.email == email))
        novo = usuario is None
        if usuario is None:
            usuario = Usuario(email=email.lower(), nome=nome)
            sessao.add(usuario)
            await sessao.flush()
        else:
            usuario.nome = nome
            usuario.ativo = True
        usuario.senha_hash = gerar_hash(senha)
        usuario.versao_sessao += 1

        empresa = await sessao.get(Empresa, empresa_id) if empresa_id else None
        if empresa is None and empresa_nome:
            empresa = await sessao.scalar(select(Empresa).where(Empresa.nome == empresa_nome))
            if empresa is None:
                empresa = Empresa(nome=empresa_nome.strip())
                sessao.add(empresa)
                await sessao.flush()
        if empresa is None:
            raise SystemExit("Empresa não encontrada; informe --empresa-id ou --empresa-nome.")
        membership = await sessao.get(UsuarioEmpresa, (empresa.id, usuario.id))
        if membership is None:
            sessao.add(UsuarioEmpresa(empresa_id=empresa.id, usuario_id=usuario.id, papel="admin", ativo=True))
        else:
            membership.papel, membership.ativo = "admin", True
        await sessao.commit()
    await engine.dispose()
    return novo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email", required=True)
    ap.add_argument("--nome", required=True)
    destino = ap.add_mutually_exclusive_group(required=True)
    destino.add_argument("--empresa-id", type=UUID)
    destino.add_argument("--empresa-nome")
    ap.add_argument("--senha")
    args = ap.parse_args()
    senha = args.senha or getpass.getpass("Senha: ")
    if len(senha) < TAMANHO_MINIMO_SENHA:
        raise SystemExit(f"A senha precisa ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")
    novo = asyncio.run(criar(args.email, args.nome, senha, args.empresa_id, args.empresa_nome))
    print("Administrador criado." if novo else "Administrador atualizado.")


if __name__ == "__main__":
    main()
