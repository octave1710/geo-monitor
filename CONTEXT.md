# GEO Monitor — Contexte de développement

## C'est quoi ce projet
Agent TinyFish qui navigue Perplexity, ChatGPT et Bing en parallèle
pour mesurer la visibilité d'une marque dans les moteurs de recherche AI.
Projet soumis au TinyFish Accelerator Hackathon.

## Stack technique
- Backend : Python + FastAPI + TinyFish SDK + Anthropic API
- Frontend : Next.js 16 + React 19 + Tailwind CSS 4
- Deploy : Vercel (frontend) + Railway (backend)
- Repo GitHub : https://github.com/octave1710/geo-monitor

## Structure des fichiers
```
geo-monitor/
├── backend/
│   ├── .env.example        ← template clés API
│   ├── requirements.txt    ← dépendances pinnées
│   ├── geo_agent.py        ← agents TinyFish + validation
│   ├── synthesizer.py      ← scoring Claude
│   ├── server.py           ← FastAPI SSE endpoint
│   └── debug.py            ← tests manuels
├── frontend/
│   ├── app/page.tsx        ← dashboard SSE temps réel
│   └── ...
├── presentation.html       ← slide deck hackathon
├── .gitignore
├── README.md
└── CONTEXT.md              ← ce fichier
```

## Statut
- [x] Agents TinyFish — 3 plateformes (Perplexity, ChatGPT, Bing)
- [x] Serveur FastAPI SSE (port 8000)
- [x] Frontend Next.js — dashboard complet
- [x] Slide deck présentation
- [ ] Deploy Vercel + Railway
- [ ] Démo vidéo + soumission

## Commandes
```bash
# Backend
cd backend
venv\Scripts\activate
uvicorn server:app --reload --port 8000

# Frontend
cd frontend
npm run dev

# Test
http://localhost:8000/api/scan/Nike
http://localhost:3000
```

## Plateformes testées
- Perplexity : OK
- ChatGPT : OK
- Bing : OK
- You.com : timeout, abandonné
- Copilot : timeout, abandonné
