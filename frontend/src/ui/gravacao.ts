import { recarregar } from "@/state/nucleo";
import { gavetaAberta } from "./gaveta";
import { tentar } from "./erros";
import { toast } from "./toast";

interface OpcoesGravar<T> {
  /** Recursos a recarregar depois de gravar (ex.: ["clientes"]). */
  recarregar: string[];
  mensagem: string;
  operacao: () => Promise<T>;
  /** Fecha a gaveta ao terminar (omita para manter aberta). */
  fechar?: () => void;
}

/** Fluxo padrão de gravação: executa, avisa erro, recarrega, confirma e fecha. Devolve o resultado ou null. */
export async function gravar<T>(o: OpcoesGravar<T>): Promise<T | null> {
  const resultado = await tentar(o.operacao);
  if (resultado === null) return null;
  const versao = (resultado as { versao?: number }).versao;
  if (gavetaAberta && versao) gavetaAberta.minhaVersao = versao;
  await recarregar(...o.recarregar);
  if (o.mensagem) toast(o.mensagem);
  o.fechar?.();
  return resultado;
}

export async function excluir(o: { recarregar: string[]; mensagem: string; operacao: () => Promise<void>; fechar: () => void }): Promise<boolean> {
  if (gavetaAberta) gavetaAberta.excluidoPorMim = true;
  const ok = (await tentar(async () => (await o.operacao(), true))) !== null;
  if (!ok) {
    if (gavetaAberta) gavetaAberta.excluidoPorMim = false;
    return false;
  }
  await recarregar(...o.recarregar);
  toast(o.mensagem);
  o.fechar();
  return true;
}
