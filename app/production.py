"""Render an editorial batch from reviewed, local production assets."""
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
import textwrap
from datetime import date
from pathlib import Path

FORMATS = {
    "principal": (1920, 1080, 285, 315, "Segunda, 19h"),
    "impacto": (1080, 1920, 30, 45, "Terça, 12h"),
    "reflexao": (1080, 1920, 60, 90, "Quinta, 19h"),
    "superacao": (1080, 1920, 120, 175, "Sábado, 9h"),
}
RIGHTS = ("nome", "titular", "fonte", "licenca", "atribuicao", "territorio",
          "verificado_em", "comprovante", "alteracoes")
SEO = ("titulo", "alternativos", "descricao", "hashtags", "palavras_chave", "comentario")


def run(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True)


def probe(path):
    return json.loads(run("ffprobe", "-v", "error", "-show_format", "-show_streams",
                          "-of", "json", str(path)))


def duration(path):
    return float(probe(path)["format"]["duration"])


def stamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def load_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if set(data["videos"]) != set(FORMATS):
        raise ValueError("Informe os quatro formatos do lote.")
    assets = data["midias"]
    used = {data["miniatura"]}
    narrations = set()
    for name, video in data["videos"].items():
        if type(video["conteudo_sintetico"]) is not bool:
            raise ValueError(f"{name}: informe se exige declaração de conteúdo sintético.")
        if any(not video["seo"].get(key) for key in SEO) or len(video["seo"]["alternativos"]) != 3:
            raise ValueError(f"{name}: metadados incompletos.")
        if not video["cenas"]:
            raise ValueError(f"{name}: faltam cenas.")
        narration = " ".join(scene["texto"].strip() for scene in video["cenas"])
        if not narration or narration in narrations:
            raise ValueError(f"{name}: a narração precisa ser própria para este formato.")
        narrations.add(narration)
        if name == "principal" and not narration.endswith("Domine sua mente. Transforme sua vida."):
            raise ValueError("O vídeo principal precisa terminar com o slogan.")
        used.add(video["trilha"])
        for scene in video["cenas"]:
            if not scene["texto"].strip() or not scene["direcao"].strip():
                raise ValueError(f"{name}: cada cena precisa de texto e direção visual.")
            used.update((scene["video"], scene["voz"]))
    for key in used:
        asset = assets[key]
        if any(not isinstance(asset.get(field), str) or not asset[field].strip() for field in RIGHTS):
            raise ValueError(f"{key}: registro de direitos incompleto.")
        if any(asset.get(field) is not True for field in ("comercial", "edicao", "distribuicao")):
            raise ValueError(f"{key}: permissões não comprovadas no manifesto.")
        if date.fromisoformat(asset["verificado_em"]) > date.today():
            raise ValueError(f"{key}: data de verificação futura.")
        for field in ("arquivo", "comprovante"):
            local = (path.parent / asset[field]).resolve()
            if not local.is_file() or not local.stat().st_size:
                raise ValueError(f"{key}: faltam os bytes de {field}.")
            asset[field] = local
    return data, sorted(used)


def render(name, video, assets, output):
    width, height, minimum, maximum, schedule = FORMATS[name]
    elapsed = 0
    captions, clips = [], []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for index, scene in enumerate(video["cenas"], 1):
            voice = assets[scene["voz"]]["arquivo"]
            footage = assets[scene["video"]]["arquivo"]
            spoken = duration(voice)
            frames = math.ceil((spoken + 0.15) * 30)
            length = frames / 30
            start = float(scene.get("inicio", 0))
            if not math.isfinite(start) or start < 0 or start + length > duration(footage):
                raise ValueError(f"{name}, cena {index}: filmagem insuficiente para a fala.")
            lines = "\n".join(textwrap.wrap(scene["texto"], width=36 if width < height else 54))
            if len(lines.splitlines()) > 2:
                raise ValueError(f"{name}, cena {index}: divida a fala em trechos de até duas linhas.")
            captions.append(f"{index}\n{stamp(elapsed)} --> {stamp(elapsed+spoken)}\n{lines}\n")
            (work / "scene.srt").write_text(f"1\n{stamp(0)} --> {stamp(spoken)}\n{lines}\n",
                                            encoding="utf-8")
            elapsed += length
            clip = f"{index}.mov"
            clips.append(clip)
            vf = (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                  f"crop={width}:{height},setsar=1,fps=30,"
                  "eq=contrast=1.05:saturation=0.92,"
                  "subtitles=scene.srt:force_style='FontName=DejaVu Sans,"
                  "FontSize=16,Outline=1.4,Shadow=0,Alignment=2,MarginV=70,MarginL=35,MarginR=45'")
            run("ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", str(footage),
                "-i", str(voice), "-map", "0:v:0", "-map", "1:a:0", "-vf", vf,
                "-af", "apad", "-t", f"{length:.6f}", "-c:v", "libx264", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", clip, cwd=work)
        if not minimum <= elapsed <= maximum:
            raise ValueError(f"{name}: {elapsed:.2f}s, esperado de {minimum} a {maximum}s.")
        (work / "concat.txt").write_text("".join(f"file '{clip}'\n" for clip in clips))
        track = assets[video["trilha"]]["arquivo"]
        mp4 = output / f"{name}.mp4"
        run("ffmpeg", "-nostdin", "-v", "error", "-f", "concat", "-safe", "1",
            "-i", "concat.txt", "-stream_loop", "-1", "-i", str(track), "-filter_complex",
            "[1:a]volume=0.12[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
            "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(mp4), cwd=work)
    info = probe(mp4)
    picture = next(s for s in info["streams"] if s["codec_type"] == "video")
    sound = next(s for s in info["streams"] if s["codec_type"] == "audio")
    seconds = float(info["format"]["duration"])
    if (picture["width"], picture["height"], picture["codec_name"], picture["r_frame_rate"],
            sound["codec_name"]) != (width, height, "h264", "30/1", "aac") or not minimum <= seconds <= maximum:
        raise ValueError(f"{name}: MP4 fora das especificações.")
    (output / f"{name}.srt").write_text("\n".join(captions), encoding="utf-8")
    (output / f"{name}.txt").write_text(
        "\n\n".join(scene["texto"] for scene in video["cenas"]) + "\n", encoding="utf-8")
    credits = dict.fromkeys([video["trilha"], *(s[k] for s in video["cenas"] for k in ("video", "voz")),
                             *([video["miniatura"]] if name == "principal" else [])])
    seo = dict(video["seo"])
    seo["descricao"] += "\n\nCréditos\n" + "\n".join(assets[k]["atribuicao"] for k in credits
                                                       if assets[k]["atribuicao"] != "dispensada")
    seo.update(horario=schedule, fuso="America/Sao_Paulo", conteudo_sintetico=video["conteudo_sintetico"])
    save(output / f"{name}.seo.json", seo)
    return {"duracao": seconds, "resolucao": [width, height], "fps": 30, "sha256": sha256(mp4),
            "tecnico": "aprovado", "revisao_editorial": "pendente", "youtube_id": None,
            "copyright_youtube": "nao_enviado", "publicacao": "bloqueada"}


def main():
    parser = argparse.ArgumentParser(description="Produz um lote para revisão privada no YouTube Studio.")
    parser.add_argument("manifesto", type=Path)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--validar", action="store_true")
    args = parser.parse_args()
    data, used = load_manifest(args.manifesto.resolve())
    if args.validar:
        print(f"Manifesto completo. {len(used)} registros de direitos preenchidos.")
        return
    output = args.saida.resolve()
    if output.exists():
        raise FileExistsError(f"Escolha uma pasta nova: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    assets = data["midias"]
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        package = Path(tmp) / "lote"
        package.mkdir()
        proof = package / "comprovantes"
        proof.mkdir()
        report = {}
        for number, key in enumerate(used, 1):
            asset = assets[key]
            copy = proof / f"{number}{asset['comprovante'].suffix}"
            copy.write_bytes(asset["comprovante"].read_bytes())
            report[key] = {field: value for field, value in asset.items()
                           if field not in ("arquivo", "comprovante")}
            report[key].update(comprovante=copy.relative_to(package).as_posix(),
                               sha256_material=sha256(asset["arquivo"]))
        save(package / "licencas.json", report)
        thumbnail = assets[data["miniatura"]]["arquivo"]
        run("ffmpeg", "-nostdin", "-v", "error", "-i", str(thumbnail), "-frames:v", "1",
            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
            "-update", "1", str(package / "thumbnail.jpg"))
        data["videos"]["principal"]["miniatura"] = data["miniatura"]
        save(package / "controle.json", {name: render(name, data["videos"][name], assets, package)
                                         for name in FORMATS})
        package.rename(output)


if __name__ == "__main__":
    main()
