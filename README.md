# Quiz de certificação

Site estático para praticar questões (única escolha, múltipla escolha, estudo de caso e arrastar e soltar). Questões mais erradas aparecem com mais frequência.

## Rodar localmente
    python -m http.server
Abra http://localhost:8000

## Novo banco de questões
1. Crie `banks/<prova>.json` seguindo o formato de `banks/sc300.json`.
2. Registre em `banks/index.json`.

## OCR em lote das imagens
`ocr_questoes.py` converte imagens de questões em JSON usando Qwen3-VL via Ollama. Veja o cabeçalho do arquivo.
