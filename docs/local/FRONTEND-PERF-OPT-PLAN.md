FRONTEND-PERF-OPT-PLAN

Objetivo

- Melhorar performance percebida e qualidade de engenharia no frontend.
- Demonstrar conhecimento avancado de Next.js (App Router), otimizacao de bundle, acessibilidade e UX.
- Evitar mudancas desnecessarias (ex.: virtualizacao sem demanda real).

Diagnostico atual (resumo)

- SSR + cache por tags ja implementado.
- Listas paginadas (12 itens por pagina) reduzem impacto de DOM.
- Componentes interativos sao client-side por necessidade.
- Imagens principais migradas para next/image.

Principios

- Medir antes de otimizar (bundle/analyzer + React Profiler).
- Otimizacao incremental e reversivel.
- Evitar complexidade sem ganho claro.

Plano de melhoria (por fases)

Fase 0 - Medicao e baseline

1. Ativar bundle analyzer (somente em dev):
   - Next config com flag ANALYZE=true.
   - Registrar tamanho de bundles (home/library/drive).
2. Medir TTFB/LCP/TTI com Lighthouse (dev e prod build).
3. Medir render do grid com React Profiler (paginacao e selecao).

Status da fase 0

- Bundle analyzer habilitado via env ANALYZE=true.
- Relatorios gerados em:
  - frontend/.next/analyze/client.html
  - frontend/.next/analyze/edge.html
  - frontend/.next/analyze/nodejs.html
- Build atual ok; warnings de lint removidos (resta apenas aviso de configuracao do ESLint do Next).
- outputFileTracingRoot configurado para evitar aviso de lockfiles duplicados.

Fase 1 - Code splitting e carga inicial

1. Dynamic import para componentes pesados:
   - VideoPlayer (modal) e ScreenRecorder.
   - Carregar apenas quando necessario.
2. Suspense em blocos secundarios:
   - Recentes e grids (fallback leve).
3. Ajustar prioridade de imagens:
   - Primeiro card com priority.

Status da fase 1

- VideoPlayer e ScreenRecorder agora carregam via dynamic import com fallback.
- Suspense aplicado em home (recentes) e library/drive (grids) com skeleton leve.
- Priority aplicado ao primeiro card dos grids.

Fase 2 - Re-render e memoizacao

1. React.memo em VideoCard e grid items.
2. Estabilizar handlers (useCallback) e props derivadas.
3. Evitar recomputes de arrays (useMemo em listas filtradas/sorted).

Status da fase 2

- VideoCard memoizado com comparacao de props relevantes.
- Selecoes em grids usam arrays derivados com useMemo.

Fase 3 - Acessibilidade e UX

1. Garantir aria-label em botoes icon-only.
2. Focus visible consistente (keyboard).
3. Validar modais (aria-describedby/aria-labelledby).

Status da fase 3

- Adicionados aria-labels em botoes icon-only (menu, paginacao, player, sync e modais).
- Dialogs com descricoes para leitores de tela em informacoes/compartilhamento.

Fase 4 - Virtualizacao (somente se necessario)
Critério para aplicar:

- Listas com 200+ itens renderizados simultaneamente, ou
- FPS abaixo de 50 em scroll e interacao do grid.
  Se nao bater o criterio, manter paginacao atual.

Se aplicado:

- Usar react-window com grid fixo.
- Confirmar compatibilidade com layout responsivo.
- Testar com 1k itens em dev.

Status da fase 4

- Não aplicada. As listas atuais renderizam 12-16 itens por página, sem indicação de gargalo.
- Reavaliar caso o grid passe de 200+ itens simultâneos ou o FPS caia no scroll.

Fase 5 - Documentacao e boas praticas

1. Atualizar docs com arquitetura e decisoes.
2. Registrar resultados das metricas (antes/depois).

Status da fase 5

- Documentacao atualizada conforme fases 0-3.
- Métricas quantitativas (Lighthouse/Profiler) pendentes de execução manual.

Como medir (manual)

1. Build de producao:
   - cd frontend
   - npm run build
   - npm run start
2. Lighthouse (Chrome DevTools):
   - Abra http://localhost:3000
   - DevTools > Lighthouse > Performance + Best Practices + SEO
   - Rodar em /, /library e /drive
3. React Profiler:
   - Ativar "Profiler" em React DevTools
   - Medir interacao de selecao e abertura do player nos grids

Registro sugerido

- Data:
- Ambiente (dev/prod, maquina):
- LCP/TTI/CLS por pagina:
- Observacoes:

Notas Lighthouse

- Home: 72 Performance com bloqueio de render por Google Fonts.
- Ajuste aplicado: fontes migradas para next/font (display=swap + self-host).
- Home (pos-ajuste): Performance 96; bloqueio residual de CSS local (~20 KB, ~80 ms).
- Record: Performance 93, Acessibilidade 92, Best Practices 96, SEO 100.
- Record metrics: FCP 0.2s, LCP 0.7s, TBT 170ms, CLS 0.09 (aviso de IndexedDB no Lighthouse).
- Library: Performance 95, Acessibilidade 94, Best Practices 96, SEO 100.
- Library metrics: FCP 0.3s, LCP 0.8s, TBT 180ms, CLS 0.00 (aviso de IndexedDB no Lighthouse).
- Drive: Performance 93, Acessibilidade 89, Best Practices 96, SEO 100.
- Drive metrics: FCP 0.2s, LCP 0.7s, TBT 190ms, CLS 0.078 (aviso de IndexedDB no Lighthouse).

Riscos e cuidados

- Dynamic import pode quebrar SSR se usado sem ssr:false em componentes client.
- Excessiva memoizacao pode complicar debug sem ganho real.
- Virtualizacao pode prejudicar acessibilidade e selecao se aplicada cedo.

Checklist de saida

- Bundle reduzido em paginas-chave.
- LCP < 2.5s (local) e TTI melhorado.
- Sem regressao de UX (modais, selecao, player).
