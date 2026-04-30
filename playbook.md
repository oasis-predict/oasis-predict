========================================
PLAYBOOK - WEATHER AI AGENT
========================================

[OBJECTIVE]

Construire un système de trading basé sur les probabilités météo
avec edge et gestion du risque.

----------------------------------------

[CURRENT MODE]

Mode: LEARNING (Paper Trading)

- Multi-city actif
- Tous les types actifs:
  - greater_than
  - less_than
  - between
- Filtrage allégé
- Objectif: accumuler des trades et apprendre

----------------------------------------

[DAILY ROUTINE]

1. Lancer le système:

python scripts/kalshi_signal_engine.py
python scripts/kalshi_position_sizer.py
python scripts/kalshi_trade_sheet_generator.py
python scripts/kalshi_trade_blotter.py

2. Observer les trades

3. Prendre décision (paper trading):
- YES ou NO

4. Enregistrer les résultats (plus tard)

5. Écrire dans learning.md

----------------------------------------

[TRADE RULES - CURRENT]

- TOP → prendre
- HIGH → prendre
- MEDIUM → prendre
- LOW → optionnel (apprentissage)

- Pas de limite stricte pour l’instant
- Objectif = volume + observation

----------------------------------------

[RISK MODE]

- Paper trading uniquement
- Pas de risque réel
- Erreurs autorisées

----------------------------------------

[EVOLUTION PLAN]

Phase 1: Apprentissage (30 trades)
Phase 2: Validation (30 trades)
Phase 3: Optimisation (filtrage intelligent)
Phase 4: Semi-automatique
Phase 5: Autonomie

----------------------------------------

[CORE PRINCIPLES]

- Ne pas forcer les conclusions
- Laisser les données parler
- Ne pas optimiser trop tôt
- Observer avant de modifier
- Discipline > émotion

----------------------------------------

[SYSTEM PHILOSOPHY]

Le système apprend avec le volume
puis devient performant avec le filtrage
