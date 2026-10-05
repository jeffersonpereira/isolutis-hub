import { brl, brlCurto } from "@/core/formato";
import { esc, html, raw, type Safe } from "@/core/html";

export interface PontoGrafico {
  rotulo: string;
  recebido: number;
  previsto: number;
  atual: boolean;
}

/** Escolhe um passo "redondo" (1, 2, 2,5, 5, 10 × 10ⁿ) para ~4 linhas de grade. */
export function passoDaEscala(max: number): number {
  const bruto = max / 4;
  const p = Math.pow(10, Math.floor(Math.log10(bruto)));
  const f = bruto / p;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
}

/** Gráfico de barras empilhadas (recebido + previsto) em SVG, nas cores da identidade. */
export function graficoFaturamento(serie: readonly PontoGrafico[], rotuloAcessivel = "Faturamento mensal"): Safe {
  const W = 720, H = 230, L = 64, R = 8, T = 12, B = 28;
  const iw = W - L - R, ih = H - T - B;
  const max = Math.max(...serie.map((s) => s.recebido + s.previsto));
  const passo = passoDaEscala(max || 1000);
  const topo = Math.max(passo, Math.ceil((max || 1) / passo) * passo);
  const y = (v: number): number => T + ih - (v / topo) * ih;
  const bw = iw / serie.length;
  let g = "";
  for (let v = 0; v <= topo + 1e-9; v += passo) {
    g += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)" stroke-width="1"/><text x="${L - 8}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="var(--muted)" font-family="IBM Plex Mono,monospace">${brlCurto(v).replace("R$ ", "")}</text>`;
  }
  serie.forEach((s, i) => {
    const rotulo = esc(s.rotulo);
    const x = L + i * bw + bw * 0.18, w = bw * 0.64;
    const hr = (s.recebido / topo) * ih, hp = (s.previsto / topo) * ih;
    if (hp > 0) g += `<rect x="${x}" y="${y(s.recebido + s.previsto)}" width="${w}" height="${hp}" fill="var(--bar-b)" rx="2"><title>${rotulo}: ${brl(s.previsto)} previsto</title></rect>`;
    if (hr > 0) g += `<rect x="${x}" y="${y(s.recebido)}" width="${w}" height="${hr}" fill="var(--bar-a)" rx="2"><title>${rotulo}: ${brl(s.recebido)} recebido</title></rect>`;
    g += `<text x="${x + w / 2}" y="${H - 8}" text-anchor="middle" font-size="11" fill="${s.atual ? "var(--ink)" : "var(--muted)"}" font-weight="${s.atual ? 600 : 400}">${rotulo}</text>`;
  });
  return html`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${rotuloAcessivel}">${raw(g)}</svg>`;
}

export const legendaFaturamento = raw(
  '<div class="legend"><span><i style="background:var(--bar-a)"></i>Recebido</span><span><i style="background:var(--bar-b)"></i>Previsto</span></div>',
);
