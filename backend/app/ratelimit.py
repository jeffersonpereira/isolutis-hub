"""Freio a tentativas de login (força bruta): janela deslizante em memória, por e-mail + IP."""

import time
from collections import defaultdict, deque

from app.errors import ErroApp


class MuitasTentativas(ErroApp):
    status = 429
    codigo = "muitas_tentativas"

    def __init__(self) -> None:
        super().__init__("Muitas tentativas de login. Aguarde alguns minutos e tente de novo.")


class LimitadorDeLogin:
    def __init__(self, maximo: int = 8, janela_segundos: int = 300) -> None:
        self.maximo, self.janela = maximo, janela_segundos
        self._falhas: dict[str, deque[float]] = defaultdict(deque)

    def _limpar(self, chave: str, agora: float) -> deque[float]:
        fila = self._falhas[chave]
        while fila and agora - fila[0] > self.janela:
            fila.popleft()
        return fila

    def verificar(self, chave: str) -> None:
        if len(self._limpar(chave, time.monotonic())) >= self.maximo:
            raise MuitasTentativas

    def registrar_falha(self, chave: str) -> None:
        self._limpar(chave, time.monotonic()).append(time.monotonic())

    def zerar(self, chave: str) -> None:
        self._falhas.pop(chave, None)


limitador_de_login = LimitadorDeLogin()
