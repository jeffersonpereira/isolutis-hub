/**
 * Campos do cadastro de parceiro, compartilhados pelas telas Clientes (papel fixo "cliente") e
 * Financeiro › Parceiro de Negócio (hub com escolha de papéis). Cada tela monta a gaveta e salva pela
 * sua própria API; aqui ficam só o HTML dos campos, a leitura do formulário e o carregamento de municípios.
 */
import { html, raw, type Safe } from "@/core/html";
import { ORIGENS } from "@/domain/constantes";
import { apiFinanceiro } from "@/features/financeiro/api";
import { formatarCep, formatarDocumento } from "@/features/financeiro/comum";
import { campo, fv, inp, sel, area } from "@/ui/campos";
import { tentar } from "@/ui/erros";
import { avisar } from "@/ui/toast";

export const UFS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"] as const;

/** O que os formulários precisam saber de um parceiro já existente (compatível com cliente e parceiro da API). */
export interface ValoresParceiro {
  tipo_pessoa?: string;
  cpf_cnpj?: string | null;
  nome?: string;
  segmento?: string | null;
  contato?: string | null;
  cargo?: string | null;
  telefone?: string | null;
  email?: string | null;
  origem?: string | null;
  obs?: string | null;
  endereco?: string | null;
  cep?: string | null;
  municipio_id?: string | null;
  uf?: string | null;
  papeis?: string[];
}

export interface PapelDisponivel {
  codigo: string;
  nome: string;
}

export interface CamposLidos {
  tipo_pessoa: "PJ" | "PF";
  cpf_cnpj: string | null;
  nome: string;
  segmento: string | null;
  contato: string | null;
  cargo: string | null;
  telefone: string | null;
  email: string | null;
  origem: (typeof ORIGENS)[number] | null;
  obs: string | null;
  endereco: string | null;
  cep: string | null;
  municipio_id: string | null;
  papeis: string[];
}

/** HTML dos campos. Com `papeis` (lista de papéis disponíveis) mostra as caixas de escolha de papel; sem, o papel é fixo. */
export function camposDoParceiro(v: ValoresParceiro = {}, papeis?: readonly PapelDisponivel[]): Safe {
  const marcados = new Set(v.papeis ?? []);
  return html`<div class="fields">
    ${
      papeis
        ? html`<div class="field full"><label>Papéis</label><div class="papeis" style="display:flex;gap:16px;flex-wrap:wrap">${papeis.map((p) => html`<label class="check"><input type="checkbox" name="papel" value="${p.codigo}"${raw(marcados.has(p.codigo) ? " checked" : "")}> ${p.nome}</label>`)}</div></div>`
        : ""
    }
    ${campo("Nome / Razão social", inp("nome", v.nome, 'maxlength="150" required'), true)}
    ${campo("Tipo de pessoa", sel("tipo_pessoa", [["PJ", "Pessoa jurídica (CNPJ)"], ["PF", "Pessoa física (CPF)"]], v.tipo_pessoa ?? "PJ"))}
    ${campo("CPF / CNPJ", inp("cpf_cnpj", v.cpf_cnpj ? formatarDocumento(v.cpf_cnpj) : "", 'inputmode="numeric" maxlength="18"'))}
    ${campo("Contato principal", inp("contato", v.contato))}${campo("Cargo", inp("cargo", v.cargo))}
    ${campo("Telefone / WhatsApp", inp("telefone", v.telefone, 'inputmode="tel"'))}${campo("E-mail", inp("email", v.email, 'type="email"'))}
    ${campo("Segmento", inp("segmento", v.segmento, 'placeholder="Ex.: distribuição, saúde, indústria"'))}${campo("Origem", sel("origem", [["", "—"], ...ORIGENS.map((o) => [o, o] as const)], v.origem))}
    ${campo("Endereço", inp("endereco", v.endereco, 'maxlength="150" placeholder="Rua, número, bairro"'), true)}
    ${campo("CEP", inp("cep", formatarCep(v.cep), 'inputmode="numeric" maxlength="9" placeholder="00000-000"'))}
    <div class="field"><label for="f-uf">UF</label><select name="uf" id="f-uf"><option value="">UF</option>${UFS.map((u) => html`<option value="${u}"${raw(u === v.uf ? " selected" : "")}>${u}</option>`)}</select></div>
    ${campo("Município", html`<select name="municipio_id" id="f-municipio_id"><option value="">Escolha a UF primeiro</option></select>`, true)}
    ${campo("Observações", area("obs", v.obs), true)}
  </div>`;
}

/** Liga o carregamento de municípios por UF e, se o parceiro já tem município, o pré-seleciona. */
export function ligarCamposDoParceiro(form: HTMLFormElement, v: ValoresParceiro = {}): void {
  const uf = form.elements.namedItem("uf") as HTMLSelectElement;
  const municipio = form.elements.namedItem("municipio_id") as HTMLSelectElement;
  const carregar = async (selecionado?: string | null): Promise<void> => {
    municipio.innerHTML = '<option value="">Carregando…</option>';
    const lista = uf.value ? await tentar(() => apiFinanceiro.municipios(uf.value)) : [];
    municipio.innerHTML = String(
      html`<option value="">${uf.value ? "Sem município" : "Escolha a UF primeiro"}</option>${(lista ?? []).map((m) => html`<option value="${m.id}"${raw(m.id === selecionado ? " selected" : "")}>${m.nome}</option>`)}`,
    );
  };
  uf.addEventListener("change", () => void carregar());
  if (v.municipio_id && v.uf) void carregar(v.municipio_id);
}

/** Lê e valida o formulário; devolve null (já avisando) se faltar algo. `papelFixo` evita exigir a escolha de papéis. */
export function lerCamposDoParceiro(form: HTMLFormElement, papelFixo?: string): CamposLidos | null {
  const nome = fv(form, "nome");
  if (!nome) return avisar("Informe o nome.");
  const papeis = papelFixo ? [papelFixo] : [...form.querySelectorAll<HTMLInputElement>('input[name="papel"]:checked')].map((i) => i.value);
  if (!papeis.length) return avisar("Escolha pelo menos um papel (cliente, fornecedor, funcionário…).");
  const municipio = fv(form, "municipio_id");
  return {
    tipo_pessoa: fv(form, "tipo_pessoa") as "PJ" | "PF", cpf_cnpj: fv(form, "cpf_cnpj") || null, nome,
    segmento: fv(form, "segmento") || null, contato: fv(form, "contato") || null, cargo: fv(form, "cargo") || null,
    telefone: fv(form, "telefone") || null, email: fv(form, "email") || null,
    origem: (fv(form, "origem") || null) as CamposLidos["origem"], obs: fv(form, "obs") || null,
    endereco: fv(form, "endereco") || null, cep: fv(form, "cep") || null, municipio_id: municipio || null, papeis,
  };
}
