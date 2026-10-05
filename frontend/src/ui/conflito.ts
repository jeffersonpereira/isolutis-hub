/**
 * Aviso de edição concorrente: se outra pessoa alterar ou excluir o registro enquanto a gaveta está aberta,
 * mostra o banner (o servidor também barra a gravação com 409 se a versão mudou).
 */
import { esc } from "@/core/html";
import { $ } from "@/core/dom";
import { aoRecarregar } from "@/state/nucleo";
import { eu, nomeDe } from "@/state/estado";
import { gavetaAberta } from "./gaveta";

interface RegistroVersionado {
  id: string;
  versao: number;
  atualizado_por: string | null;
}
type Consulta = (id: string) => RegistroVersionado | undefined;
const consultas = new Map<string, Consulta>();

export const registrarConsulta = (recurso: string, consulta: Consulta): void => void consultas.set(recurso, consulta);

export function iniciarAvisoDeConflito(): void {
  aoRecarregar((recurso) => {
    const aberta = gavetaAberta;
    const box = $("#conflito");
    if (!aberta || aberta.recurso !== recurso || !box) return;
    const atual = consultas.get(recurso)?.(aberta.id);
    if (!atual) {
      if (aberta.excluidoPorMim) return;
      box.hidden = false;
      box.innerHTML = "Outra pessoa da equipe <b>excluiu este registro</b> enquanto você estava com ele aberto. Ele não pode mais ser salvo.";
      return;
    }
    if (atual.versao !== aberta.versao && atual.versao !== aberta.minhaVersao && atual.atualizado_por !== eu.id) {
      box.hidden = false;
      box.innerHTML = `<b>${esc(nomeDe(atual.atualizado_por))}</b> acabou de alterar este registro. Feche e abra de novo para ver a versão atual. Se tentar salvar agora, o sistema vai pedir que você recarregue.`;
    }
  });
}
