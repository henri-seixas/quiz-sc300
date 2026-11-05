#!/usr/bin/env python3
"""Converte imagens de questões em JSON para o quiz, usando Qwen3-VL no Ollama.

Estrutura esperada da pasta "imagens":
  imagens/
    001.png                questão avulsa
    contoso/               um estudo de caso
      caso.png             cenário (o nome do arquivo começa com "caso")
      q1.png, q2.png       questões desse caso

Uso:
  pip install ollama pillow
  ollama pull qwen3-vl:4b-instruct
  python ocr_questoes.py

Pode ser interrompido e rodado de novo: o que já foi lido fica em saida/raw.
"""
import io
import json
import re
import sys
from pathlib import Path

import ollama
from PIL import Image

MODEL = "qwen3-vl:4b-instruct"   # se a tag não existir, use "qwen3-vl:4b"
INPUT, OUTPUT = Path("imagens"), Path("saida")
MAX_SIDE = 1400                  # reduz a imagem: mais rápido e usa menos VRAM
EXTS = {".png", ".jpg", ".jpeg", ".webp"}

PROMPT = """Transcreva esta imagem de questão de prova exatamente como está, sem traduzir nem resumir.
- type: "single" (uma resposta), "multiple" (várias respostas), "dragdrop" (arrastar e soltar) ou "scenario" (imagem que traz só o texto de um estudo de caso).
- scenario: coloque o texto completo em "question".
- options: só o texto de cada alternativa, sem a letra.
- dragdrop: "items" são os itens a arrastar e "targets" são os destinos, na ordem em que aparecem.
- Se a imagem mostrar a resposta correta, preencha "answer_letters" (ex.: ["B"]) ou, em dragdrop, "answer_dragdrop" (para cada destino, o índice do item correto, começando em 0).
- Se a imagem não mostrar a resposta, deixe esses campos vazios. Nunca invente a resposta."""

SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"enum": ["single", "multiple", "dragdrop", "scenario"]},
        "question": {"type": "string"},
        "options": {"type": "array", "items": {"type": "string"}},
        "items": {"type": "array", "items": {"type": "string"}},
        "targets": {"type": "array", "items": {"type": "string"}},
        "answer_letters": {"type": "array", "items": {"type": "string"}},
        "answer_dragdrop": {"type": "array", "items": {"type": "integer"}},
        "explanation": {"type": "string"},
    },
    "required": ["type", "question"],
}


def preparar(path):
    img = Image.open(path).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def ler(path):
    nome = path.relative_to(INPUT).as_posix().replace("/", "__") + ".json"
    cache = OUTPUT / "raw" / nome
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    r = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT, "images": [preparar(path)]}],
        format=SCHEMA,
        options={"temperature": 0, "num_ctx": 6144},
        keep_alive="30m",
    )
    dados = json.loads(r["message"]["content"])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return dados


def montar(d, qid, caso, path):
    q = {"id": qid, "type": d["type"], "question": d["question"]}
    if caso:
        q["case"] = caso
    if d["type"] == "dragdrop":
        q["items"] = d.get("items", [])
        q["targets"] = d.get("targets", [])
        q["answer"] = d.get("answer_dragdrop", [])
        ok = len(q["answer"]) == len(q["targets"]) > 0 and all(
            0 <= a < len(q["items"]) for a in q["answer"]
        )
    else:
        q["options"] = d.get("options", [])
        q["answer"] = [
            ord(x.strip().upper()[0]) - 65 for x in d.get("answer_letters", []) if x.strip()
        ]
        ok = bool(q["answer"]) and all(0 <= a < len(q["options"]) for a in q["answer"])
    if d.get("explanation"):
        q["explanation"] = d["explanation"]
    q["_arquivo"] = str(path)  # para achar a imagem na revisão; o quiz ignora este campo
    return q, ok


def tarefas():
    for p in sorted(INPUT.iterdir()):
        if p.is_file() and p.suffix.lower() in EXTS:
            yield p, None
        elif p.is_dir():
            fs = sorted(f for f in p.iterdir() if f.suffix.lower() in EXTS)
            for f in sorted(fs, key=lambda f: not f.stem.lower().startswith("caso")):
                yield f, p.name


def main():
    if not INPUT.is_dir():
        sys.exit(f"Pasta '{INPUT}' não encontrada.")
    try:
        ollama.show(MODEL)
    except Exception:
        sys.exit(f"Modelo não encontrado. Rode: ollama pull {MODEL}")

    OUTPUT.mkdir(exist_ok=True)
    cases, certas, pendentes = {}, [], []
    for path, caso in tarefas():
        print(path, flush=True)
        try:
            d = ler(path)
        except Exception as e:
            pendentes.append({"_arquivo": str(path), "erro": str(e)})
            continue
        if d["type"] == "scenario":
            cases[caso or path.stem] = d["question"]
            continue
        qid = re.sub(r"\W+", "-", path.relative_to(INPUT).with_suffix("").as_posix()).strip("-")
        q, ok = montar(d, qid, caso, path)
        (certas if ok else pendentes).append(q)

    def gravar(nome, obj):
        (OUTPUT / nome).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    gravar("banco.json", {"cases": cases, "questions": certas})
    gravar("pendentes.json", pendentes)
    print(f"\n{len(certas)} questões em saida/banco.json")
    print(f"{len(pendentes)} para revisar em saida/pendentes.json (sem resposta ou com erro)")


if __name__ == "__main__":
    main()
