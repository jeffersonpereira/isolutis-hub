"""Erros de aplicação com formato único de resposta: {"erro": {"codigo": ..., "mensagem": ...}}."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErroApp(Exception):
    status = 400
    codigo = "erro"

    def __init__(self, mensagem: str, *, codigo: str | None = None, status: int | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        if codigo:
            self.codigo = codigo
        if status:
            self.status = status


class NaoEncontrado(ErroApp):
    status = 404
    codigo = "nao_encontrado"

    def __init__(self, o_que: str = "Registro") -> None:
        super().__init__(f"{o_que} não encontrado.")


class NaoAutenticado(ErroApp):
    status = 401
    codigo = "nao_autenticado"


class SemPermissao(ErroApp):
    status = 403
    codigo = "sem_permissao"


class Conflito(ErroApp):
    status = 409
    codigo = "conflito"


class RegraDeNegocio(ErroApp):
    status = 422
    codigo = "regra_de_negocio"


def _resposta(status: int, codigo: str, mensagem: str, detalhes: object | None = None) -> JSONResponse:
    corpo: dict[str, object] = {"erro": {"codigo": codigo, "mensagem": mensagem}}
    if detalhes is not None:
        corpo["erro"]["detalhes"] = detalhes  # type: ignore[index]
    return JSONResponse(status_code=status, content=corpo)


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(ErroApp)
    async def _erro_app(_: Request, e: ErroApp) -> JSONResponse:
        return _resposta(e.status, e.codigo, e.mensagem)

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, e: RequestValidationError) -> JSONResponse:
        campos = [{"campo": ".".join(str(p) for p in err["loc"][1:]), "mensagem": err["msg"]} for err in e.errors()]
        return _resposta(422, "validacao", "Alguns campos estão inválidos.", campos)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException) -> JSONResponse:
        return _resposta(e.status_code, "http", str(e.detail))
