# GEO Monitor — Contexte de développement

## C'est quoi ce projet
Agent TinyFish qui navigue Perplexity, Bing, Brave et DuckDuckGo en parallèle
pour mesurer la visibilité d'une marque dans les moteurs de recherche AI.
Projet soumis au TinyFish Accelerator Hackathon (deadline 29 mars).

## Stack technique
- Backend : Python + FastAPI + TinyFish SDK + Anthropic API
- Frontend : Next.js (pas encore commencé)
- Deploy : Vercel (frontend) + Railway (backend)
- Repo GitHub : https://github.com/octave1710/geo-monitor

## Structure des fichiers
geo-monitor/
├── backend/
│   ├── .env               ← clés API (jamais sur GitHub)
│   ├── requirements.txt
│   ├── geo_agent.py       ← 4 agents TinyFish parallèles ✅
│   ├── synthesizer.py     ← scoring Claude ✅
│   └── server.py          ← FastAPI SSE endpoint ✅
├── frontend/              ← pas encore créé
├── .gitignore
├── README.md
└── CONTEXT.md             ← ce fichier

## Ce qui est fait ✅
- Étape 1 : Environnement (Python, Node, Cursor) ✅
- Étape 2 : Structure projet + GitHub ✅
- Étape 3 : Agents TinyFish — 4 plateformes confirmées ✅
  - Perplexity ✅ (marche bien)
  - Bing ✅ (marche bien)
  - Brave ✅ (marche bien)
  - DuckDuckGo ✅ (marche bien)
  - You.com ✗ (timeout)
  - Copilot ✗ (timeout)
- Étape 4 : Serveur FastAPI SSE ✅ (tourne sur port 8000)
  - geo_agent.py ✅
  - synthesizer.py ✅ (fix compute_score en cours)
  - server.py ✅

## Ce qui reste à faire
- Étape 4 : Finaliser le fix synthesizer.py (event "complete" manquant)
- Étape 5 : Frontend Next.js — dashboard SSE en temps réel
- Étape 6 : Deploy Vercel + Railway
- Étape 7 : Démo vidéo + soumission X + email accelerator@tinyfish.io

## Commandes importantes
# Activer le venv (à faire à chaque nouveau terminal)
cd C:\Users\Alliot\OneDrive\Documents\tinyfish\geo-monitor\backend
venv\Scripts\activate

# Lancer le serveur backend
uvicorn server:app --reload --port 8000

# Tester dans le navigateur
http://127.0.0.1:8000
http://127.0.0.1:8000/api/scan/Nike

## Niveau d'assistance requis
Ultra-assisté, étape par étape. Octave n'est pas expert en création d'agents.
Utilise Claude Code / Cursor AI pour les gros blocs de code.
Toujours dire QUOI faire, OÙ, et DANS QUEL ORDRE.
Ne jamais donner plusieurs étapes en même temps.

## Plateformes testées et résultats
- Perplexity : timeout 300s requis, marche bien
- Bing : marche bien
- Brave Search : marche bien  
- DuckDuckGo : marche bien
- You.com : timeout systématique, abandonné
- Copilot : timeout systématique, abandonné
```

Sauvegarde, puis push sur GitHub :
```
cd ..
git add .
git commit -m "add CONTEXT.md and fix synthesizer"
git push origin main
```

---

### Crée le Claude Project

Dans Claude, clique sur **"Projects"** dans le menu de gauche → **"New Project"** → nomme-le `GEO Monitor — TinyFish Hackathon`.

Dans les instructions du projet, colle ceci :
```
Tu m'accompagnes dans le développement de GEO Monitor, 
un agent TinyFish pour le TinyFish Accelerator Hackathon.
Niveau d'assistance : ultra-assisté, étape par étape.
Toujours dire quoi faire, où, et dans quel ordre.
Ne jamais donner plusieurs étapes en même temps.
Le fichier CONTEXT.md du repo GitHub contient l'état exact du projet.
