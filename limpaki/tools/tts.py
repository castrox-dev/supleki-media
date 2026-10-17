#!/usr/bin/env python3
"""Narração via ElevenLabs. A chave NUNCA vai pro repositório: vem da variável de
ambiente ELEVENLABS_API_KEY ou de um arquivo passado em --key-file (linha
ELEVENLABS_API_KEY=...).

Uso:
  python3 tts.py roteiro.txt saida.mp3 [--voice Roberta] [--model eleven_v3] [--key-file .env.local]

O roteiro usa linha em branco entre falas; cada fala vira uma pausa que o
make_reel.py detecta pra sincronizar os cards.
"""
import argparse, json, os, sys, urllib.request

API = "https://api.elevenlabs.io/v1"


def load_key(path):
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k and path and os.path.exists(path):
        for ln in open(path):
            if ln.startswith("ELEVENLABS_API_KEY="):
                k = ln.split("=", 1)[1].strip().strip('"')
    if not k:
        sys.exit("ELEVENLABS_API_KEY não encontrada")
    return k


def req(key, path, data=None, accept="application/json"):
    r = urllib.request.Request(API + path, data=json.dumps(data).encode() if data else None,
                               headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": accept})
    return urllib.request.urlopen(r, timeout=120).read()


def find_voice(key, name):
    voices = json.loads(req(key, "/voices"))["voices"]
    for v in voices:
        if v["name"].lower().startswith(name.lower()):
            return v["voice_id"]
    sys.exit(f"voz '{name}' não está na sua biblioteca; disponíveis: " + ", ".join(v["name"] for v in voices))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("out")
    ap.add_argument("--voice", default="Roberta")
    ap.add_argument("--model", default="eleven_v3")
    ap.add_argument("--key-file", default=None)
    a = ap.parse_args()
    key = load_key(a.key_file)
    vid = find_voice(key, a.voice)
    text = open(a.script, encoding="utf-8").read().strip()
    body = {"text": text, "model_id": a.model,
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.75, "style": 0.0, "speed": 1.05}}
    audio = req(key, f"/text-to-speech/{vid}?output_format=mp3_44100_128", body, accept="audio/mpeg")
    open(a.out, "wb").write(audio)
    print("ok", a.out, len(audio), "bytes")


if __name__ == "__main__":
    main()
