export function toast(mensagem: string): void {
  const el = document.createElement("div");
  el.className = "toast";
  el.setAttribute("role", "status");
  el.textContent = mensagem;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2400);
}

/** Mostra uma mensagem de validação e devolve null (para `return avisar("...")` em coletores de formulário). */
export const avisar = (mensagem: string): null => {
  toast(mensagem);
  return null;
};
