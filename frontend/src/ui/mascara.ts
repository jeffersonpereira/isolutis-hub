/** Reaplica a máscara mantendo o cursor logo após o mesmo dígito (não salta para o fim ao editar no meio). */
export function reaplicarMascara(campo: HTMLInputElement, mascarar: (valor: string) => string): void {
  const anterior = campo.value;
  const digitosAntes = anterior.slice(0, campo.selectionStart ?? anterior.length).replace(/\D/g, "").length;
  const novo = mascarar(anterior);
  if (novo === anterior) return;
  campo.value = novo;
  if (campo.ownerDocument.activeElement !== campo) return;
  let pos = 0;
  for (let vistos = 0; pos < novo.length && vistos < digitosAntes; pos++) if (/\d/.test(novo.charAt(pos))) vistos++;
  campo.setSelectionRange(pos, pos);
}

/**
 * Reaplica a máscara sempre levando o cursor para o fim do campo. Para máscaras em que os dígitos
 * digitados são reinterpretados por inteiro a cada tecla (ex.: moeda, onde o próprio número de
 * dígitos de preenchimento muda) não existe "o mesmo dígito" de uma formatação para a seguinte —
 * tentar preservar a posição relativa do cursor desloca o valor a cada tecla.
 */
export function reaplicarMascaraAoFim(campo: HTMLInputElement, mascarar: (valor: string) => string): void {
  const novo = mascarar(campo.value);
  if (novo !== campo.value) campo.value = novo;
  if (campo.ownerDocument.activeElement !== campo) return;
  campo.setSelectionRange(novo.length, novo.length);
}
