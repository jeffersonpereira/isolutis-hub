# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: fluxo-critico.spec.ts >> Multi-aba sync >> criar cliente em aba 1, verificar em aba 2
- Location: tests\fluxo-critico.spec.ts:169:3

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - img "iSolutis" [ref=e6]
        - generic [ref=e7]: Hub Comercial
      - navigation "Áreas do Hub Comercial"
      - generic [ref=e8]: Conectando…
    - main [ref=e10]
  - generic [ref=e12]:
    - generic [ref=e13]:
      - img "iSolutis" [ref=e14]
      - generic [ref=e15]: Hub Comercial
    - generic [ref=e16]:
      - heading "Entrar" [level=1] [ref=e17]
      - generic [ref=e18]: E-mail
      - textbox "E-mail" [ref=e19]: admin@test.example.com
      - generic [ref=e20]: Senha
      - textbox "Senha" [ref=e21]: TestPassword123
      - button "Entrar" [ref=e22] [cursor=pointer]
      - paragraph [ref=e23]: Esqueceu a senha? Peça a um administrador do Hub para definir uma nova.
    - status [ref=e24]: Não foi possível concluir a operação agora. Verifique a conexão e tente de novo.
```