from fastapi import APIRouter

from app.deps import Sessao
from app.domain.papeis import permissoes_do_papel
from app.schemas.painel import Painel
from app.services import painel as svc

router = APIRouter(prefix="/painel", tags=["Painel"])


@router.get("", response_model=Painel, response_model_exclude_unset=True)
async def painel(sessao: Sessao):
    """Painel por papel: só entram os blocos autorizados (`exclude_unset` omite os demais da resposta)."""
    return await svc.montar(sessao, permissoes_do_papel(sessao.info.get("papel")))
