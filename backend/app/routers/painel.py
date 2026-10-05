from fastapi import APIRouter

from app.deps import Sessao
from app.schemas.painel import Painel
from app.services import painel as svc

router = APIRouter(prefix="/painel", tags=["Painel"])


@router.get("", response_model=Painel)
async def painel(sessao: Sessao):
    return await svc.montar(sessao)
