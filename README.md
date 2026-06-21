# Base documentaire — DSCG UE1

Ce dépôt contient tout le contenu du site de révision (fiches, cartes Q/R,
références juridiques) et un robot de construction qui régénère le site
automatiquement à chaque modification.

---

## 1. Mise en place (à faire une seule fois)

### Étape A — Créer le dépôt GitHub
1. Va sur [github.com](https://github.com) et crée un compte gratuit si tu n'en as pas.
2. Clique sur **"New repository"** (bouton vert en haut à droite, ou + → New repository).
3. Donne-lui un nom, par exemple `dscg-ue1` — laisse-le en **Public** (nécessaire pour la version gratuite de GitHub Pages) ou en **Private** si tu as un compte qui le permet pour Pages.
4. Ne coche aucune case d'initialisation (pas de README, pas de .gitignore) — on va tout uploader nous-mêmes.
5. Clique sur **"Create repository"**.

### Étape B — Uploader ce dossier
1. Sur la page du dépôt vide, clique sur le lien **"uploading an existing file"**.
2. Glisse-dépose **l'ensemble du contenu de ce dossier** (pas le dossier lui-même, son contenu : `content/`, `data/`, `templates/`, `scripts/`, `.github/`, ce `README.md`) dans la zone d'upload. La plupart des navigateurs modernes conservent l'arborescence des sous-dossiers lors d'un glisser-déposer.
3. En bas de page, écris un message de commit (ex. "Premier import") et clique sur **"Commit changes"**.

> Si le glisser-déposer ne conserve pas les sous-dossiers chez toi, la solution la plus fiable est d'installer **GitHub Desktop** (gratuit, interface graphique, pas de ligne de commande) : tu cloues le dépôt vide, tu copies-colles ce dossier dedans, puis tu cliques sur "Commit" puis "Push" dans l'appli.

### Étape C — Activer GitHub Pages
1. Dans le dépôt, va dans **Settings → Pages**.
2. Sous "Build and deployment", choisis **Source : GitHub Actions**.
3. Retourne dans l'onglet **Actions** du dépôt : un workflow nommé "Build and deploy site" devrait se lancer automatiquement (déclenché par ton upload). Attends qu'il passe au vert (1-2 minutes).
4. Reviens dans **Settings → Pages** : l'adresse de ton site apparaît en haut (du type `https://<ton-nom-utilisateur>.github.io/dscg-ue1/`).

C'est fait — le site est en ligne, à cette adresse, accessible à toi et à qui tu veux partager le lien.

---

## 2. Modifier le contenu (au quotidien, sans repasser par Claude)

Chaque modification d'un fichier déclenche **automatiquement** une reconstruction
et republication du site (1-2 minutes). Tu n'as jamais besoin d'utiliser un
terminal.

### Modifier une fiche existante
1. Va dans `content/fiches/` et clique sur le fichier `.md` à modifier (le nom du fichier correspond au titre de la fiche).
2. Clique sur l'icône crayon (✏️) en haut à droite du fichier pour l'éditer.
3. Modifie le texte (format expliqué dans la section 3 ci-dessous).
4. En bas de page, clique sur **"Commit changes…"**.
5. Le site se mettra à jour seul — vérifie dans l'onglet **Actions** que le workflow est passé au vert.

### Ajouter une nouvelle fiche
1. Dans `content/fiches/`, clique sur **"Add file" → "Create new file"**.
2. Nomme-le `mon-nouveau-slug.md` (sans espace, sans accent, en minuscules, tirets pour séparer les mots — ce nom devient l'identifiant de la fiche).
3. Reprends le modèle de la section 3.
4. N'oublie pas d'ajouter son identifiant dans `data/fiches.json` et `data/qr_cartes.json` si tu veux qu'elle apparaisse dans les listes et qu'une carte Q/R lui soit associée (modèle en section 4).

### Ajouter un chapitre ou une notion
- `data/chapitres.json` : ajoute un objet `{ "id": "...", "titre": "...", "ordre": N, "description": "..." }`.
- `data/notions.json` : ajoute un objet `{ "id": "...", "chapitre_id": "...", "titre": "...", "description": "", "mots_cles": [] }` — `chapitre_id` doit correspondre à un `id` existant dans `chapitres.json`.

### Donner l'accès en modification à un camarade
Settings → Collaborators → "Add people" → entre son nom d'utilisateur GitHub.
Sans ça, les autres peuvent seulement **voir** le site publié, pas modifier le contenu source.

---

## 3. Format d'une fiche (`content/fiches/*.md`)

```markdown
---
id: "cessation-des-paiements"
notion_id: "entreprise-difficulte.notions-fondamentales"
titre: "Cessation des paiements"
mots_cles: []
importance: "★★★"
references: ["ref-art-l-631-1-c-com-1"]
---

# Cessation des paiements

## Définition / Réponse
État du débiteur **dans l'impossibilité de faire face au passif exigible
avec son actif disponible**.

> 📎 Art. L. 631-1 al. 1 C. com.

- Condition : passif exigible (dettes certaines, liquides, échues).
- Condition : actif disponible (liquidités immédiatement mobilisables).
```

Règles :
- Le bloc entre `---` (front-matter) est obligatoire et doit rester au même format.
- `##` = grand titre de section dans la fiche, `###` = sous-titre, `- ` = puce, `> 📎 ...` = référence (s'affiche en italique avec l'icône trombone), `**texte**` = mots-clés/formulations à restituer en gras doré.
- Ne mets pas de bloc "correction" — comme convenu, les corrections sont directement intégrées au texte final, pas affichées séparément.

---

## 4. Format d'une carte Q/R (`data/qr_cartes.json`)

```json
{
  "id": "qr-046",
  "notion_id": "entreprise-difficulte.notions-fondamentales",
  "fiche_id": "cessation-des-paiements",
  "type_question": "definition",
  "difficulte": "moyen",
  "question": "Cessation des paiements : définition exacte ?",
  "reponse": "Impossibilité de faire face au passif exigible avec l'actif disponible (Art. L. 631-1 C. com.).",
  "mots_cles": [],
  "source": "fiche interne"
}
```

---

## 5. Ce que je (Claude) continue à faire de mon côté

- Vérifier chaque nouvelle fiche par rapport aux codes officiels avant qu'elle soit intégrée ici (process inchangé).
- T'aider à rédiger les fichiers `.md`/`.json` correctement formatés à partir de tes envois — tu peux continuer à m'envoyer tes Q/A comme avant, je préparerai les fichiers prêts à coller dans `content/fiches/` et `data/`.
- Faire évoluer le gabarit du site (`templates/index_template.html`) et le script de build quand on ajoute des fonctionnalités.

Ce que tu peux désormais faire sans moi : corriger une coquille, ajuster une formulation,
réorganiser l'ordre, ajouter un chapitre vide en attendant son contenu — tout ce qui ne
demande pas de vérification juridique.
