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


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n+", re.S)


def split_front_matter(text):
    """Sépare un éventuel front-matter du corps. Les fichiers de cours n'en ont pas
    tous ; sans ce filtre, celui des fichiers qui en ont s'affiche en clair."""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).split("\n"):
        if ": " not in line:
            continue
        k, v = line.split(": ", 1)
        try:
            meta[k] = json.loads(v)
        except Exception:
            meta[k] = v
    return meta, text[m.end():]


def inline(text):
    esc = ihtml.escape(text)
    esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
    return esc


def table_hint(ncols):
    """Indice de défilement, affiché par le CSS sur petit écran uniquement, et seulement
    pour les tables trop larges pour un téléphone (à partir de 4 colonnes)."""
    if ncols < 4:
        return ""
    return ('<p class="table-hint">Tableau large — faites glisser horizontalement '
            'pour voir toutes les colonnes.</p>')


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
                # --cols : nombre de colonnes, exploite par le CSS pour activer le
                # defilement horizontal sur mobile (min-width proportionnel).
                out.append(f'<div class="table-wrap"><table class="cmp" style="--cols:{len(rows[0])}"><thead><tr>')
                out.append("".join(f"<th>{inline(h)}</th>" for h in rows[0]))
                out.append("</tr></thead><tbody>")
                for r in rows[1:]:
                    out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
                out.append("</tbody></table></div>")
                out.append(table_hint(len(rows[0])))
            continue
        if line.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:|-]+\|?$", lines[i+1].strip()) and "-" in lines[i+1]:
            if in_ul:
                out.append("</ul>"); in_ul = False
            def _cells(s):
                return [c.strip() for c in s.strip().strip("|").split("|")]
            header = _cells(line)
            i += 2  # header + ligne de séparation
            body_rows = []
            while i < n and lines[i].strip().startswith("|"):
                body_rows.append(_cells(lines[i].strip()))
                i += 1
            out.append(f'<div class="table-wrap"><table class="cmp" style="--cols:{len(header)}"><thead><tr>')
            out.append("".join(f"<th>{inline(h)}</th>" for h in header))
            out.append("</tr></thead><tbody>")
            for r in body_rows:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table></div>")
            out.append(table_hint(len(header)))
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
            out.append(f"<li>{inline(line[2:])}</li>")
            i += 1
            continue
        if in_ul:
            out.append("</ul>"); in_ul = False
        if line.startswith(">"):
            content = line.lstrip(">").strip()
            cls = "cite" if content.startswith("📎") else ""
            out.append(f'<p class="{cls}">{inline(content)}</p>')
            i += 1
            continue
        esc = ihtml.escape(line)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        out.append(f"<p>{esc}</p>")
        i += 1
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def validate(bundle):
    warns = []
    chap_ids = {c["id"] for c in bundle["chapitres"]}
    notion_ids = {n["id"] for n in bundle["notions"]}
    fiche_ids = {f["id"] for f in bundle["fiches"]}
    code_titres = {c["titre"] for c in bundle["codes"]}

    for n in bundle["notions"]:
        if n.get("chapitre_id") not in chap_ids:
            warns.append(f"notion '{n['id']}' -> chapitre_id inconnu '{n.get('chapitre_id')}'")
    for f in bundle["fiches"]:
        if f.get("notion_id") not in notion_ids:
            warns.append(f"fiche '{f['id']}' -> notion_id inconnu '{f.get('notion_id')}'")
    for c in bundle["qr_cartes"]:
        if c.get("notion_id") not in notion_ids:
            warns.append(f"carte '{c.get('id')}' -> notion_id inconnu '{c.get('notion_id')}'")
        if c.get("fiche_id") and c["fiche_id"] not in fiche_ids:
            warns.append(f"carte '{c.get('id')}' -> fiche_id inconnu '{c['fiche_id']}'")
    for r in bundle["references_textes"]:
        for fid in (r.get("fiches_liees") or []):
            if fid not in fiche_ids:
                warns.append(f"référence '{r.get('id')}' -> fiche_liee inconnue '{fid}'")
        doc = r.get("document")
        if doc and doc not in code_titres and not any(k in doc.lower() for k in ("texte", "loi", "ordonnance", "directive", "bo", "bulletin", "règlement")):
            warns.append(f"référence '{r.get('id')}' -> document '{doc}' absent de codes.json")
    for t in bundle["tableaux_comparatifs"]:
        if t.get("chapitre_id") not in chap_ids:
            warns.append(f"tableau '{t.get('id')}' -> chapitre_id inconnu '{t.get('chapitre_id')}'")
        for nid in (t.get("notions_liees") or []):
            if nid not in notion_ids:
                warns.append(f"tableau '{t.get('id')}' -> notion_liee inconnue '{nid}'")
        contenu = t.get("contenu") or {}
        cols = contenu.get("colonnes") or []
        for idx, ligne in enumerate(contenu.get("lignes") or [], 1):
            if len(ligne) != len(cols):
                warns.append(
                    f"tableau '{t.get('id')}' -> ligne {idx} : {len(ligne)} cellules "
                    f"pour {len(cols)} colonnes (décalage à l'affichage)")

    for cle in bundle.get("cours_orphelins", []):
        warns.append(f"cours 'content/cours/{cle}.md' -> ne correspond ni à un chapitre "
                     f"ni à une notion : il ne sera affiché nulle part")
    if isinstance(bundle["programme"], dict):
        for p in bundle["programme"].get("parties", []):
            for sp in p.get("sous_parties", []):
                cid = sp.get("chapitre_id")
                if cid and cid not in chap_ids:
                    warns.append(f"programme -> '{sp.get('titre')}' pointe vers chapitre inconnu '{cid}'")

    missing = [f["id"] for f in bundle["fiches"] if f["id"] not in bundle["fiches_full"]]

    if warns:
        print(f"\n⚠ Validation : {len(warns)} incohérence(s) référentielle(s) :")
        for w in warns[:40]:
            print("  -", w)
        if len(warns) > 40:
            print(f"  … (+{len(warns) - 40} autres)")
    else:
        print("✓ Validation : intégrité référentielle OK.")
    if missing:
        print(f"ℹ {len(missing)} fiche(s) de l'index sans contenu .md (l'onglet Cours les ignore).")


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

    # Cours rédigés (onglet "Synthèse").
    #   content/cours/<chapitre_id>.md          -> synthèse du chapitre
    #   content/cours/<suffixe_de_notion>.md    -> synthèse d'une matière du chapitre,
    #                                              rattachée via l'id de notion
    #                                              "<chapitre_id>.<suffixe>"
    cours = {}
    cours_dir = os.path.join(ROOT, "content", "cours")
    cours_meta = {}
    for path in sorted(glob.glob(os.path.join(cours_dir, "*.md"))):
        key = os.path.splitext(os.path.basename(path))[0]
        meta, corps = split_front_matter(open(path, encoding="utf-8").read())
        cours_meta[key] = meta
        cours[key] = md_to_html(corps)
    bundle["cours"] = cours

    # Index : chapitre -> matières disponibles (permet d'afficher les fichiers de cours
    # qui ne portent pas le nom d'un chapitre, sinon jamais rendus).
    chap_ids = {c["id"] for c in bundle["chapitres"]}
    notion_titres = {n["id"]: n.get("titre", n["id"]) for n in bundle["notions"]}
    cours_index = {}
    cours_orphelins = []
    for key in sorted(cours):
        if key in chap_ids:
            continue  # synthèse de chapitre, servie directement par bundle["cours"]
        rattache = False
        for cid in chap_ids:
            nid = f"{cid}.{key}"
            if nid in notion_titres:
                titre = notion_titres[nid] or cours_meta.get(key, {}).get("titre") or key
                cours_index.setdefault(cid, []).append(
                    {"cle": key, "notion_id": nid, "titre": titre})
                rattache = True
                break
        if not rattache:
            cours_orphelins.append(key)
    bundle["cours_index"] = cours_index
    bundle["cours_orphelins"] = cours_orphelins

    validate(bundle)

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
