#!/usr/bin/env python3
"""
Reconstruit le site complet (public/index.html) à partir de :
  - content/fiches/*.md   (une fiche = un fichier Markdown avec front-matter)
  - data/*.json            (chapitres, notions, fiches (index), qr_cartes, references_textes)
  - templates/index_template.html  (gabarit HTML avec le marqueur __BUNDLE_JSON__)

Ce script est appelé automatiquement par le workflow GitHub Actions
(.github/workflows/deploy.yml) à chaque push sur la branche principale.
Il peut aussi être lancé à la main : `python3 scripts/build.py`
"""
import json
import re
import glob
import os
import shutil
import html as ihtml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content", "fiches")
DATA_DIR = os.path.join(ROOT, "data")
STATIC_DIR = os.path.join(ROOT, "static")
TEMPLATE_PATH = os.path.join(ROOT, "templates", "index_template.html")
OUT_DIR = os.path.join(ROOT, "public")
OUT_PATH = os.path.join(OUT_DIR, "index.html")


def parse_fiche_md(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"Fiche sans front-matter valide : {path}")
    fm_raw, body = m.group(1), m.group(2)
    meta = {}
    for line in fm_raw.split("\n"):
        if ": " not in line:
            continue
        k, v = line.split(": ", 1)
        try:
            meta[k] = json.loads(v)
        except Exception:
            meta[k] = v
    return meta, body


def md_to_html(body):
    lines = body.split("\n")
    out = []
    in_ul = False
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.strip()
        if not line:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            i += 1
            continue
        if line.startswith(":::table"):
            if in_ul:
                out.append("</ul>"); in_ul = False
            i += 1
            rows = []
            while i < n and lines[i].strip() != ":::":
                row_line = lines[i].strip()
                if row_line:
                    rows.append([c.strip() for c in row_line.split("|")])
                i += 1
            i += 1  # skip closing :::
            if rows:
                out.append('<div class="table-wrap"><table class="cmp"><thead><tr>')
                out.append("".join(f"<th>{ihtml.escape(h)}</th>" for h in rows[0]))
                out.append("</tr></thead><tbody>")
                for r in rows[1:]:
                    out.append("<tr>" + "".join(f"<td>{ihtml.escape(c)}</td>" for c in r) + "</tr>")
                out.append("</tbody></table></div>")
            continue
        if line.startswith("::correction::"):
            content = line[len("::correction::"):].strip()
            out.append(f'<div class="correction-box"><strong>⚠️ Correction</strong><p>{ihtml.escape(content)}</p></div>')
            i += 1
            continue
        if line.startswith("::caution::"):
            content = line[len("::caution::"):].strip()
            out.append(f'<div class="caution-box"><strong>🔍 À prendre avec des pincettes</strong><p>{ihtml.escape(content)}</p></div>')
            i += 1
            continue
        if line.startswith("# "):
            i += 1
            continue
        if line.startswith("### "):
            if in_ul:
                out.append("</ul>"); in_ul = False
            out.append(f"<h4>{ihtml.escape(line[4:])}</h4>")
            i += 1
            continue
        if line.startswith("## "):
            if in_ul:
                out.append("</ul>"); in_ul = False
            out.append(f"<h3>{ihtml.escape(line[3:])}</h3>")
            i += 1
            continue
        if line.startswith("- "):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{ihtml.escape(line[2:])}</li>")
            i += 1
            continue
        if in_ul:
            out.append("</ul>"); in_ul = False
        if line.startswith(">"):
            content = line.lstrip(">").strip()
            cls = "cite" if content.startswith("📎") else ""
            out.append(f'<p class="{cls}">{ihtml.escape(content)}</p>')
            i += 1
            continue
        esc = ihtml.escape(line)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        out.append(f"<p>{esc}</p>")
        i += 1
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def main():
    fiches_full = {}
    for path in sorted(glob.glob(os.path.join(CONTENT_DIR, "*.md"))):
        meta, body = parse_fiche_md(path)
        fid = meta.get("id")
        if not fid:
            raise ValueError(f"Fiche sans champ 'id' : {path}")
        fiches_full[fid] = {**meta, "body_html": md_to_html(body)}

    bundle = {"fiches_full": fiches_full}
    for name in ["chapitres", "notions", "fiches", "qr_cartes", "references_textes",
                 "programme", "changelog", "tableaux_comparatifs", "codes", "points_attention",
                 "annales", "liens_utiles"]:
        path = os.path.join(DATA_DIR, f"{name}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                bundle[name] = json.load(f)
        else:
            bundle[name] = []

    bo_path = os.path.join(STATIC_DIR, "bo-ue1-dscg.pdf")
    bundle["has_bo_pdf"] = os.path.exists(bo_path)
    bundle["static_bo_path"] = "static/bo-ue1-dscg.pdf"

    template = open(TEMPLATE_PATH, encoding="utf-8").read()
    bundle_json = json.dumps(bundle, ensure_ascii=False)
    out_html = template.replace("__BUNDLE_JSON__", bundle_json)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(out_html)

    # Copy static assets (images, PDFs) as-is into public/static/
    static_out = os.path.join(OUT_DIR, "static")
    if os.path.exists(STATIC_DIR):
        if os.path.exists(static_out):
            shutil.rmtree(static_out)
        shutil.copytree(STATIC_DIR, static_out)

    print(f"OK — {len(fiches_full)} fiches, {len(bundle['qr_cartes'])} cartes Q/R, "
          f"{len(bundle['references_textes'])} références.")
    print(f"Site généré : {OUT_PATH}")


if __name__ == "__main__":
    main()
