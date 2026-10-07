/**
 * Tela "Em qual empresa quer trabalhar?", exibida após o login (e ao trocar de empresa), mesmo com uma única empresa.
 * Também a tela "sem acesso" para quem não tem nenhuma empresa ativa. Usa o visual do login.
 */
import type { EmpresaAcesso } from "@/api/tipos";
import { esc } from "@/core/html";
import { rotuloDoPapel } from "@/domain/papeis";

const ID = "escolhaEmpresa";

function montarRaiz(): HTMLElement {
  document.getElementById(ID)?.remove();
  const raiz = document.createElement("div");
  raiz.className = "login";
  raiz.id = ID;
  document.body.append(raiz);
  return raiz;
}

const topo = `<div class="lg-topo"><img src="/logo-horizontal.png" alt="iSolutis" width="200" height="77"><span>Hub Comercial</span></div>`;

/** Resolve com a empresa escolhida e remove a tela. `sugerida` (a última usada) vem pré-selecionada. */
export function escolherEmpresa(empresas: readonly EmpresaAcesso[], sugerida: string | null, aoSair: () => void): Promise<EmpresaAcesso> {
  const raiz = montarRaiz();
  return new Promise((resolve) => {
    const cartoes = empresas
      .map((e) => {
        const ultima = e.id === sugerida;
        return `<button type="button" class="emp-card${ultima ? " ultima" : ""}" data-id="${esc(e.id)}"${ultima ? ' aria-describedby="empUltima"' : ""}>
          <span class="emp-nome">${esc(e.nome)}</span>
          <span class="emp-papel">${esc(rotuloDoPapel(e.papel))}</span>
          ${ultima ? '<span class="emp-ultima" id="empUltima">Última usada</span>' : ""}
        </button>`;
      })
      .join("");
    raiz.innerHTML = `<div class="lg-box" role="dialog" aria-modal="true" aria-labelledby="empTitulo">${topo}
      <div class="lg-form">
        <h1 id="empTitulo">Em qual empresa quer trabalhar?</h1>
        <p class="sub" style="margin:0 0 8px">Você pode trocar de empresa a qualquer momento pelo menu do seu usuário.</p>
        <div class="emp-lista" role="group" aria-label="Empresas">${cartoes}</div>
        <button class="lg-link" type="button" id="empSair">Sair</button>
      </div></div>`;
    const botoes = [...raiz.querySelectorAll<HTMLButtonElement>(".emp-card")];
    botoes.forEach((b) =>
      b.addEventListener("click", () => {
        const escolhida = empresas.find((e) => e.id === b.dataset.id);
        if (!escolhida) return;
        raiz.remove();
        resolve(escolhida);
      }),
    );
    // Setas percorrem os cartões (além do Tab), como numa lista de opções.
    raiz.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      const i = botoes.indexOf(document.activeElement as HTMLButtonElement);
      if (i === -1) return;
      e.preventDefault();
      botoes[(i + (e.key === "ArrowDown" ? 1 : -1) + botoes.length) % botoes.length]?.focus();
    });
    raiz.querySelector("#empSair")?.addEventListener("click", aoSair);
    setTimeout(() => (botoes.find((b) => b.classList.contains("ultima")) ?? botoes[0])?.focus(), 50);
  });
}

/** Conta autenticada sem nenhuma empresa ativa: explica e só oferece sair (nenhum dado é carregado). */
export function telaSemAcesso(aoSair: () => void): void {
  const raiz = montarRaiz();
  raiz.innerHTML = `<div class="lg-box" role="alertdialog" aria-modal="true" aria-labelledby="empTitulo">${topo}
    <div class="lg-form">
      <h1 id="empTitulo">Sem acesso a nenhuma empresa</h1>
      <p class="sub" style="margin:0">Sua conta não tem acesso ativo a nenhuma empresa. Peça a um administrador para incluir você na equipe e entre de novo.</p>
      <button class="btn primary" type="button" id="empSair">Sair</button>
    </div></div>`;
  const sair = raiz.querySelector<HTMLButtonElement>("#empSair");
  sair?.addEventListener("click", aoSair);
  setTimeout(() => sair?.focus(), 50);
}
