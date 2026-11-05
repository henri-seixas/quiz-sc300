# Quiz de certificação

Site estático para praticar questões de prova. Questões mais erradas aparecem com mais frequência (repetição espaçada simples). O progresso fica no `localStorage` do navegador; use "Exportar/Importar progresso" para levar entre navegadores.

## Tipos de questão
| `type` | Como responde | Campos |
|---|---|---|
| `single` | uma alternativa | `options`, `answer: [i]` |
| `multiple` | várias alternativas | `options`, `answer: [i, j]` |
| `dropdown` | lista suspensa por linha (inclui Sim/Não e hotspot) | `rows: [{label, options, answer}]` |
| `dragdrop` | arrastar itens para alvos (item pode repetir) | `items`, `targets`, `answer: [item por alvo]` |
| `ordering` | colocar itens na ordem (sobram distratores) | `items`, `answer: [índices na ordem]` |
| `lab` | laboratório: mostra a solução e você diz se acertou | `explanation` |

Campos comuns: `id`, `n` (número na fonte), `question` (HTML), `case` (id em `cases`), `explanation`, `aviso` (alerta mostrado após responder), `fonte`.
Estudos de caso ficam em `cases: { id: { title, html } }` e aparecem acima da questão.

## Rodar localmente
    python -m http.server
Abra http://localhost:8000

## Novo banco de questões
1. Crie `banks/<prova>.json` seguindo o formato de `banks/sc300.json`.
2. Registre em `banks/index.json`.

## OCR em lote das imagens
`ocr_questoes.py` converte imagens de questões em JSON usando Qwen3-VL via Ollama. Veja o cabeçalho do arquivo.
