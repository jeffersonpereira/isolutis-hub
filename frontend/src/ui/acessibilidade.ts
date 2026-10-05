/**
 * Utilitários de acessibilidade para melhorar WCAG compliance.
 * Garante que inputs têm labels semânticos corretos, roles apropriados, etc.
 */

/**
 * Associa label com input via atributo "for".
 * Se a label não tem "for", cria com ID automático.
 */
export function associarLabel(
  inputElement: HTMLInputElement,
  labelElement?: HTMLLabelElement | undefined,
): void {
  let label = labelElement;
  if (!label) {
    // Encontrar label anterior
    label = inputElement.previousElementSibling as HTMLLabelElement | undefined;
    if (label?.tagName !== "LABEL") {
      const pai = inputElement.parentElement;
      label = pai?.querySelector("label") as HTMLLabelElement | undefined;
    }
  }

  if (!label) return;

  // Garantir que input tem ID
  if (!inputElement.id) {
    inputElement.id = `f-${inputElement.name || Math.random().toString(36).slice(2)}`;
  }

  // Associar label ao input
  label.htmlFor = inputElement.id;
}

/**
 * Melhorar acessibilidade de inputs em formulários.
 * - Associa labels com "for"
 - Adiciona aria-required se obrigatório
 - Adiciona aria-invalid se tem erro
 */
export function melhorarFormulario(form: HTMLFormElement): void {
  const inputs = form.querySelectorAll("input, select, textarea");

  for (const input of inputs) {
    const element = input as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

    // Associar com label
    const label = form.querySelector(`label[for="${element.id}"], label:has(+ [name="${element.name}"])`) as HTMLLabelElement | null;
    if (label && !element.id) {
      element.id = `f-${element.name || Math.random().toString(36).slice(2)}`;
      label.htmlFor = element.id;
    }

    // Marcar como requerido se necessário
    if (element.hasAttribute("required")) {
      element.setAttribute("aria-required", "true");
    }

    // Adicionar role apropriado em inputs customizados
    if (element.type === "checkbox") {
      element.setAttribute("role", "checkbox");
    } else if (element.type === "radio") {
      element.setAttribute("role", "radio");
    }
  }
}

/**
 * Marcar um input como tendo erro e associar mensagem de erro.
 */
export function marcarComErro(
  input: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement,
  mensagem: string,
): void {
  input.setAttribute("aria-invalid", "true");

  // Criar ID para mensagem de erro se não existir
  const erroId = `${input.id || input.name}-erro`;
  let erroMsg = document.getElementById(erroId) as HTMLElement | null;

  if (!erroMsg) {
    erroMsg = document.createElement("span");
    erroMsg.id = erroId;
    erroMsg.className = "erro-msg";
    input.parentElement?.appendChild(erroMsg);
  }

  erroMsg.textContent = mensagem;
  input.setAttribute("aria-describedby", erroId);
}

/**
 * Remover marcação de erro de um input.
 */
export function removerErro(input: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement): void {
  input.removeAttribute("aria-invalid");
  const erroId = input.getAttribute("aria-describedby");
  if (erroId) {
    document.getElementById(erroId)?.remove();
    input.removeAttribute("aria-describedby");
  }
}

/**
 * Adicionar estilos para elementos com erro.
 */
export function estilosErro(): void {
  const style = document.createElement("style");
  style.textContent = `
    input[aria-invalid="true"],
    select[aria-invalid="true"],
    textarea[aria-invalid="true"] {
      border-color: var(--bad);
      background-color: var(--bad-bg);
    }

    .erro-msg {
      color: var(--bad);
      font-size: 12px;
      margin-top: 4px;
      display: block;
    }
  `;
  document.head.appendChild(style);
}

/**
 * Inicializar estilos de acessibilidade (chamar uma vez ao startup).
 */
export function inicializarAcessibilidade(): void {
  estilosErro();
}
