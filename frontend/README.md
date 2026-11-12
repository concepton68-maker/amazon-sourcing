# Interface web Syllig Vente

React + TypeScript (Vite). Textes dans `src/i18n/fr.json` (D-AMZ-010) ; aucun texte en dur dans les composants.

```bash
npm install
npm run build          # vérifie les types puis construit dist/, servi par l'API
cd ../backend && AMZ_MODE=dev python -m sourcing serveur   # http://127.0.0.1:8820 (données fictives)
npm run dev            # développement : http://localhost:5173, /api relayé vers 8820
```
