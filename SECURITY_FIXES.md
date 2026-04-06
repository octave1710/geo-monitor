# Security Fixes & Manual Actions

## Actions manuelles OBLIGATOIRES (Claude ne peut pas les faire)

### 1. ROTATE TES CLÉS API — URGENT
Tes clés sont potentiellement exposées via `debug.py` et `raw_output.txt` qui étaient sur GitHub.

- **Anthropic** : https://console.anthropic.com/settings/keys → Supprimer l'ancienne clé, en créer une nouvelle
- **TinyFish** : Depuis ton dashboard TinyFish → Régénérer la clé API
- **Mettre à jour** : Copie les nouvelles clés dans `backend/.env`

### 2. NETTOYER L'HISTORIQUE GIT
Les fichiers sensibles (`__pycache__/`, `raw_output.txt`) sont dans l'historique Git même après suppression.

```bash
cd geo-monitor

# Supprimer __pycache__ du repo (déjà dans .gitignore, mais traqué)
git rm -r --cached backend/__pycache__/ 2>/dev/null

# Supprimer raw_output.txt du repo
git rm --cached backend/raw_output.txt 2>/dev/null

# Commit le nettoyage
git add .gitignore
git commit -m "chore: clean tracked files and fix .gitignore"
git push
```

Pour purger complètement l'historique (optionnel mais recommandé) :
```bash
# Installer git-filter-repo si besoin : pip install git-filter-repo
git filter-repo --path backend/__pycache__/ --path backend/raw_output.txt --invert-paths
git push --force
```

### 3. ACTIVER LA PROTECTION DE BRANCHE SUR GITHUB
- GitHub → Settings → Branches → Add rule
- Branch name pattern : `main`
- Cocher : "Require a pull request before merging"
- Cocher : "Require status checks to pass"

### 4. AJOUTER TON DOMAINE VERCEL AU CORS (si déployé)
Dans `backend/server.py`, la liste `allow_origins` contient déjà `https://geo-monitor-coral.vercel.app`.
Si ton URL Vercel est différente, modifie-la :
```python
allow_origins=[
    "http://localhost:3000",
    "https://ton-vrai-domaine.vercel.app",
]
```

### 5. VÉRIFIER LE CONTEXT.MD
Le fichier `CONTEXT.md` expose ton path Windows `C:\Users\Alliot\...`.
Supprime ou nettoie ce path avant de push si tu veux garder le fichier public.

---

## Fixes déjà appliqués par Claude

| Fix | Fichier | Détail |
|-----|---------|--------|
| .gitignore UTF-8 + enrichi | `.gitignore` | Ré-encodé en UTF-8, ajouté `venv/`, `*.pyc`, `raw_output.txt`, `.env.*`, etc. |
| Validation brand name | `geo_agent.py` | Regex `[a-zA-Z0-9\s\-\.&']` + limite 100 chars |
| CORS restreint | `server.py` | Limité à `localhost:3000` + domaine Vercel |
| Fix compute_score filtre | `synthesizer.py` | `queries_tested > 0` au lieu de `"error" not in r` |
| Fix fallback score | `synthesizer.py` | Score 0 au lieu de 65 quand l'analyse échoue |
| Fix appels sync bloquants | `server.py` | `generate_queries` et `compute_score` via `run_in_executor` |
| Fix SSE parser frontend | `page.tsx` | Buffer-based parsing, gère les chunks coupés |
| Fix res.body! crash | `page.tsx` | Vérifie `res.ok` et `res.body` avant d'utiliser |
| Fix division par zéro | `geo_agent.py` | Guard `if total_queries > 0` |
| Validation output LLM | `geo_agent.py` | Vérifie que Claude retourne bien 3 strings |
| Normalisation résultats | `geo_agent.py` | Chaque scan retourne un format cohérent |
| Imports propres | `geo_agent.py` | Tous en haut du fichier, pas d'import inline |
| Timeouts en constantes | `geo_agent.py` + `server.py` | `QUERY_TIMEOUT`, `PLATFORM_TIMEOUT`, `SSE_POLL_TIMEOUT` |
| Suppression dead code | `geo_agent.py` | `scan_all()` supprimé |
| debug.py nettoyé | `debug.py` | Plus de leak de clé API |
| raw_output.txt supprimé | `backend/` | Fichier debug avec traces supprimé |
| .env.example ajouté | `backend/` | Template sans vraies clés |
| Dépendances pinnées | `requirements.txt` | Versions exactes fixées |
| Erreurs génériques client | `geo_agent.py` | `type(e).__name__` au lieu de `str(e)` |
| Platforms dynamiques | `page.tsx` | Utilise `totalPlatforms` du backend au lieu de hardcoder 3 |
| Détection connexion perdue | `page.tsx` | Affiche un message si `complete` jamais reçu |
