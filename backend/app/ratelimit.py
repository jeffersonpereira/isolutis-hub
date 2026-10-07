"""Freio a tentativas de login (força bruta): janela deslizante em memória, por e-mail + IP."""

import time
from collections import defaultdict, deque

from app.errors import ErroApp


class MuitasTentativas(ErroApp):
    status = 429
    codigo = "muitas_tentativas"

    def __init__(self, mensagem: str = "Muitas tentativas de login. Aguarde alguns minutos e tente de novo.") -> None:
        super().__init__(mensagem)


class LimitadorDeLogin:
    def __init__(
        self,
        maximo: int = 8,
        janela_segundos: int = 300,
        mensagem: str = "Muitas tentativas de login. Aguarde alguns minutos e tente de novo.",
    ) -> None:
        self.maximo, self.janela, self.mensagem = maximo, janela_segundos, mensagem
        self._falhas: dict[str, deque[float]] = defaultdict(deque)

    def _limpar(self, chave: str, agora: float) -> deque[float]:
        fila = self._falhas[chave]
        while fila and agora - fila[0] > self.janela:
            fila.popleft()
        return fila

    def verificar(self, chave: str) -> None:
        if len(self._limpar(chave, time.monotonic())) >= self.maximo:
            raise MuitasTentativas(self.mensagem)

    def registrar_falha(self, chave: str) -> None:
        self._limpar(chave, time.monotonic()).append(time.monotonic())

    def zerar(self, chave: str) -> None:
        self._falhas.pop(chave, None)


limitador_de_login = LimitadorDeLogin()

# Segundo fator: limite por usuário (o atacante já tem um token parcial e pode trocar de IP).
limitador_de_2fa = LimitadorDeLogin(
    maximo=10,
    janela_segundos=300,
    mensagem="Muitas tentativas de código. Aguarde alguns minutos e tente de novo.",
)


class ControleTokenParcial:
    """Erros por token parcial (jti) e tokens revogados; em memória, com a validade do token (5 min)."""

    def __init__(self, max_erros: int = 5, validade_segundos: int = 300) -> None:
        self.max_erros, self.validade = max_erros, validade_segundos
        self._erros: dict[str, tuple[int, float]] = {}  # jti -> (erros, expira_em)
        self._revogados: dict[str, float] = {}  # jti -> expira_em

    def _expirar(self) -> None:
        agora = time.monotonic()
        self._erros = {j: v for j, v in self._erros.items() if v[1] > agora}
        self._revogados = {j: ate for j, ate in self._revogados.items() if ate > agora}

    def revogado(self, jti: str) -> bool:
        self._expirar()
        return jti in self._revogados

    def revogar(self, jti: str) -> None:
        self._revogados[jti] = time.monotonic() + self.validade
        self._erros.pop(jti, None)

    def registrar_erro(self, jti: str) -> bool:
        """Conta um erro; devolve True (e revoga o jti) ao atingir o máximo."""
        self._expirar()
        erros, expira = self._erros.get(jti, (0, time.monotonic() + self.validade))
        erros += 1
        if erros >= self.max_erros:
            self.revogar(jti)
            return True
        self._erros[jti] = (erros, expira)
        return False


controle_token_parcial = ControleTokenParcial()
