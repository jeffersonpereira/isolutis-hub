import { describe, expect, it } from "vitest";
import { addDias, addMeses, brlCurto, dataBR, iniciais } from "./formato";

describe("datas", () => {
  it("addMeses limita ao último dia do mês", () => {
    expect(addMeses("2026-01-31", 1)).toBe("2026-02-28");
    expect(addMeses("2024-01-31", 1)).toBe("2024-02-29");
    expect(addMeses("2026-11-15", 3)).toBe("2027-02-15");
  });
  it("addDias atravessa meses e anos", () => {
    expect(addDias("2026-12-30", 5)).toBe("2027-01-04");
    expect(addDias("2026-03-01", -1)).toBe("2026-02-28");
  });
  it("dataBR", () => {
    expect(dataBR("2026-03-05")).toBe("05/03/2026");
    expect(dataBR("")).toBe("—");
    expect(dataBR(null)).toBe("—");
  });
});

describe("formatação", () => {
  it("brlCurto", () => {
    expect(brlCurto(1500)).toContain("mil");
    expect(brlCurto(2_500_000)).toContain("mi");
  });
  it("iniciais", () => {
    expect(iniciais("Soraya Sá")).toBe("SS");
    expect(iniciais("")).toBe("");
  });
});
