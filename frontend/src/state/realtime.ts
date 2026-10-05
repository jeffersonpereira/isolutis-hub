/** Cliente do WebSocket: presença ("Usando agora") e avisos de que dados mudaram no servidor. */
import { sessaoToken, urlWebSocket } from "@/api/http";

export interface PessoaOnline {
  usuario_id: string;
  nome: string;
  area: string;
  editando: string | null;
}

interface Ouvintes {
  presenca: (pessoas: PessoaOnline[]) => void;
  alterado: (recursos: string[]) => void;
  conexao: (conectado: boolean) => void;
}

let ws: WebSocket | null = null;
let ouvintes: Ouvintes | null = null;
let tentativas = 0;
let area = "";
let editando: string | null = null;
let encerrado = false;

function abrir(): void {
  if (encerrado || !ouvintes) return;
  const socket = new WebSocket(urlWebSocket());
  ws = socket;
  socket.onopen = () => {
    socket.send(JSON.stringify({ tipo: "auth", token: sessaoToken.obter(), empresa_id: sessaoToken.empresa() }));
    tentativas = 0;
    ouvintes?.conexao(true);
    enviarPresenca();
  };
  socket.onmessage = (ev: MessageEvent<string>) => {
    const m = JSON.parse(ev.data) as { tipo: string; pessoas?: PessoaOnline[]; recursos?: string[] };
    if (m.tipo === "presenca") ouvintes?.presenca(m.pessoas ?? []);
    if (m.tipo === "alterado") ouvintes?.alterado(m.recursos ?? []);
  };
  socket.onclose = (ev) => {
    ouvintes?.conexao(false);
    if (encerrado || ev.code === 4401) return;
    // reconecta com espera crescente (1s, 2s, 4s ... até 15s)
    const espera = Math.min(15000, 1000 * 2 ** tentativas++);
    setTimeout(abrir, espera);
  };
}

function enviarPresenca(): void {
  if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ tipo: "presenca", area, editando }));
}

export const tempoReal = {
  iniciar(o: Ouvintes): void {
    ouvintes = o;
    encerrado = false;
    abrir();
  },
  parar(): void {
    encerrado = true;
    ws?.close();
  },
  /** Informa onde a pessoa está e o que está editando. */
  presenca(patch: { area?: string; editando?: string | null }): void {
    if (patch.area !== undefined) area = patch.area;
    if (patch.editando !== undefined) editando = patch.editando;
    enviarPresenca();
  },
};
