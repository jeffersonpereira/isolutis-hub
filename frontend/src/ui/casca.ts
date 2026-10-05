/** Barra lateral: "Usando agora", indicador de sincronização e conta. */
import { obrigatorio } from "@/core/dom";
import { esc, html } from "@/core/html";
import { iniciais, primeiroNome } from "@/core/formato";
import { AREA_NOME } from "@/domain/constantes";
import { eu } from "@/state/estado";
import type { PessoaOnline } from "@/state/realtime";

export function desenharOnline(pessoas: PessoaOnline[]): void {
  const el = obrigatorio("#online");
  const lista = [...pessoas].sort((a, b) => Number(b.usuario_id === eu.id) - Number(a.usuario_id === eu.id));
  el.hidden = !lista.length;
  el.innerHTML = String(
    html`<div class="on-t">Usando agora · ${lista.length}</div>${lista.map((p) => {
      const souEu = p.usuario_id === eu.id;
      const nome = souEu ? `${primeiroNome(eu.nome)} (você)` : p.nome || "Pessoa da equipe";
      const onde = p.editando ? "editando " + p.editando : (AREA_NOME[p.area] ?? "");
      return html`<div class="on-p" title="${nome + (onde ? " · " + onde : "")}"><i class="av"><span>${iniciais(p.nome)}</span></i><div class="on-n"><b>${nome}</b><small>${onde}</small></div></div>`;
    })}`,
  );
}

type Situacao = "conectando" | "on" | "off";
export function indicarSincronizacao(situacao: Situacao, texto: string): void {
  const el = obrigatorio("#sync");
  el.className = situacao === "conectando" ? "sync" : `sync ${situacao}`;
  el.innerHTML = `<span class="dot"></span>${esc(texto)}`;
}

export function mostrarConta(): void {
  obrigatorio("#contaEmail").textContent = `${eu.nome} · ${eu.email}`;
  obrigatorio("#conta").hidden = false;
}
