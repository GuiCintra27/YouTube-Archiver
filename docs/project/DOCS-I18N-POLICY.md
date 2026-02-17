# Política de Documentação Bilíngue (PT-BR | EN)

## Objetivo

Definir como manter a documentação oficial do projeto em português e inglês com consistência, rastreabilidade e baixo atrito no dia a dia.

## Escopo coberto

Esta política vale para os **docs core oficiais**:

- `README.md` e `README.en.md`
- `docs/project/INDEX.md` e `docs/project/en/INDEX.md`
- `docs/project/QUICK-START.md` e `docs/project/en/QUICK-START.md`
- `docs/project/ARCHITECTURE.md` e `docs/project/en/ARCHITECTURE.md`
- `docs/project/TECHNICAL-REFERENCE.md` e `docs/project/en/TECHNICAL-REFERENCE.md`
- `docs/project/OBSERVABILITY.md` e `docs/project/en/OBSERVABILITY.md`
- `docs/project/GOOGLE-DRIVE-SETUP.md` e `docs/project/en/GOOGLE-DRIVE-SETUP.md`
- `docs/project/GOOGLE-DRIVE-FEATURES.md` e `docs/project/en/GOOGLE-DRIVE-FEATURES.md`
- `docs/project/GLOBAL-PLAYER.md` e `docs/project/en/GLOBAL-PLAYER.md`
- `docs/project/BUGS.md` e `docs/project/en/BUGS.md`

## Fonte de verdade

- **PT-BR é a fonte primária** para conteúdo dos docs core.
- A versão EN deve ser atualizada no mesmo ciclo de mudança dos arquivos PT-BR correspondentes.

## Regras de manutenção

1. Toda alteração em doc core PT-BR deve alterar o par EN equivalente.
2. Todo doc core deve conter seletor de idioma no topo:
   - PT: `[**PT-BR**](./<ARQUIVO>.md) | [EN](./en/<ARQUIVO>.md)`
   - EN: `[PT-BR](../<ARQUIVO>.md) | **EN**`
3. Links internos em EN devem priorizar docs EN.
4. `docs/local/` e `docs/local/archive/` permanecem internos (PT-BR, fora do escopo bilíngue).
5. `docs/project/archive/` permanece histórico público (sem espelho obrigatório EN).

## Validação local obrigatória

Antes de abrir PR com mudança de docs core:

```bash
npm run docs:check-i18n
npm run docs:check-links
```

Se houver inconsistência, corrigir antes do merge.
