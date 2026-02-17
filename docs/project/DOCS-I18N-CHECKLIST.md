# Checklist Operacional de Sync PT-BR | EN

Use este checklist em qualquer PR que altere documentação core.

## Paridade de arquivos

- [ ] Cada arquivo core PT alterado tem seu correspondente EN alterado.
- [ ] Não há arquivo core PT sem par EN.
- [ ] Não há arquivo EN sem par PT.

## Navegação e links

- [ ] Headers de idioma estão presentes e corretos nos arquivos alterados.
- [ ] `README.md` referencia `docs/project/INDEX.md` e `docs/project/en/INDEX.md`.
- [ ] `README.en.md` referencia `docs/project/en/INDEX.md`.
- [ ] `docs/project/INDEX.md` referencia `docs/project/en/INDEX.md`.
- [ ] Links locais funcionam em PT e EN (`npm run docs:check-links`).

## Estrutura equivalente

- [ ] Seções principais (H2/H3) mantêm equivalência estrutural PT/EN.
- [ ] Fluxos, comandos, endpoints e paths seguem o mesmo inventário funcional.
- [ ] Mudanças de comportamento descritas em PT foram refletidas em EN.

## Verificação final

- [ ] `npm run docs:check-i18n` sem erro.
- [ ] `npm run docs:check-links` sem erro.
- [ ] Revisão humana rápida para terminologia e clareza.
