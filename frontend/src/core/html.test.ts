import { describe, expect, it } from "vitest";
import { attr, html, raw } from "./html";

describe("html", () => {
  it("escapa valores interpolados", () => {
    const nome = '<img src=x onerror="alert(1)">';
    expect(String(html`<b>${nome}</b>`)).toBe("<b>&lt;img src=x onerror=&quot;alert(1)&quot;&gt;</b>");
  });
  it("não escapa duas vezes trechos seguros nem arrays de html", () => {
    const item = (t: string) => html`<li>${t}</li>`;
    expect(String(html`<ul>${["a", "<b>"].map(item)}</ul>`)).toBe("<ul><li>a</li><li>&lt;b&gt;</li></ul>");
    expect(String(html`${raw("<i>ok</i>")}`)).toBe("<i>ok</i>");
  });
  it("ignora null, undefined e false", () => {
    expect(String(html`a${null}b${undefined}c${false}d`)).toBe("abcd");
  });
  it("atributo booleano", () => {
    expect(String(html`<input${attr("checked", true)}${attr("disabled", false)}>`)).toBe("<input checked>");
  });
});
