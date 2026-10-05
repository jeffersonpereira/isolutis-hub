"""Dados de demonstração via API (usa o administrador criado por app.scripts.criar_admin)."""
import datetime as d
import os

import httpx

B=os.environ.get("HUB_URL","http://localhost:8000")+"/api/v1"
c=httpx.Client(base_url=B)
t=c.post("/auth/login",json={"email":"admin@isolutis.com.br","senha":os.environ.get("HUB_SENHA","senha-segura-123")}).json()["access_token"]
c.headers["Authorization"]=f"Bearer {t}"
hoje=d.date.today()
eu=c.get("/auth/eu").json()
c.post("/usuarios",json={"nome":"Jefferson Pereira","email":"jefferson@isolutis.com.br","senha":"outra-senha-123"})
cli=[c.post("/clientes",json=x).json() for x in [
 {"nome":"Distribuidora Alfa","contato":"Maria Souza","telefone":"(71) 99239-0992","origem":"Indicação","segmento":"distribuição"},
 {"nome":"Clínica Beta","contato":"João Lima","origem":"Site"},
 {"nome":"Indústria Gama","contato":"Ana Paula","telefone":"71988887777","origem":"LinkedIn"}]]
c.post("/produtos/catalogo")
prods=c.get("/produtos").json()
for p in prods[:3]: c.put(f"/produtos/{p['id']}",json={**{k:p[k] for k in('nome','tipo','unidade','descricao','ativo')},"preco":[8000,18000,45000][prods.index(p)] ,"versao":p["versao"]})
def neg(t,ci,e,v,m,dias,**k): return c.post("/negocios",json={"titulo":t,"cliente_id":cli[ci]["id"],"etapa":e,"valor":v,"mensal":m,"previsao":(hoje+d.timedelta(days=dias)).isoformat(),"responsavel_id":eu["id"],**k}).json()
n1=neg("Portal do cliente",0,"negociacao",18000,1200,10)
n2=neg("Sistema de agendamento",1,"proposta",8000,600,-3)
n3=neg("App de pedidos",2,"lead",45000,2500,30)
n4=neg("ERP leve",0,"ganho",30000,1500,-20)
neg("Dashboard BI",1,"perdido",12000,0,-40,motivo_perda="Preço")
o=c.post("/orcamentos",json={"cliente_id":cli[0]["id"],"negocio_id":n1["id"],"data":hoje.isoformat(),"status":"enviado","itens":[{"descricao":"Sistema sob medida · Média","qtd":1,"preco_unitario":18000},{"descricao":"Manutenção mensal · Média","qtd":1,"preco_unitario":1200,"mensal":True}],"obs":"Pagamento em 3 parcelas."}).json()
c.post("/orcamentos",json={"cliente_id":cli[1]["id"],"negocio_id":n2["id"],"data":hoje.isoformat(),"status":"rascunho","itens":[{"descricao":"Agendamento","preco_unitario":8000}]})
for i in range(0,8):
    mes=(hoje.replace(day=1)-d.timedelta(days=30*i)).replace(day=10)
    c.post("/faturamento",json={"cliente_id":cli[0]["id"],"tipo":"mensal" if i%2 else "projeto","descricao":f"Lançamento {i}","valor":3000+i*450,"vencimento":mes.isoformat(),"status":"recebido" if i>0 else "previsto"})
cat=c.get("/despesas/opcoes").json()
c.post("/despesas",json={"data":hoje.replace(day=5).isoformat(),"descricao":"Hospedagem","valor":420,"categoria_id":cat["categorias"][0]["id"],"status":"pago","repetir":3,"fornecedor":"AWS"})
c.post("/investimentos",json={"data":hoje.replace(day=2).isoformat(),"descricao":"Aporte inicial","valor":10000,"investidor":"Soraya Sá","forma":"Dinheiro (aporte)"})
pr=c.post("/projetos",json={"titulo":"ERP leve","cliente_id":cli[0]["id"],"negocio_id":n4["id"],"status":"construcao","responsavel_id":eu["id"],"inicio":(hoje-d.timedelta(days=20)).isoformat(),"entrega":(hoje+d.timedelta(days=40)).isoformat(),"objetivo":"Centralizar pedidos e estoque.","escopo":"• Pedidos\n• Estoque","etapas":[{"titulo":"Diagnóstico","status":"concluida"},{"titulo":"Desenvolvimento","status":"andamento","inicio":(hoje-d.timedelta(days=10)).isoformat(),"fim":(hoje+d.timedelta(days=20)).isoformat()},{"titulo":"Validação","status":"a_fazer"}]}).json()
for ti,col,pri in [("Enviar proposta revisada","a_fazer","alta"),("Preparar diagnóstico","fazendo","media"),("Revisar contrato","revisao","baixa"),("Ligar para a Clínica","concluido","media")]:
    c.post("/tarefas",json={"titulo":ti,"coluna":col,"prioridade":pri,"responsavel_id":eu["id"],"prazo":(hoje+d.timedelta(days=2)).isoformat(),"checklist":[{"texto":"Passo 1","feito":True},{"texto":"Passo 2"}]})
print("seed ok")
