# Weather AI Agent - Kalshi Weather Trading System

## Overview

Ce projet est un pipeline de trading semi-automatisé pour les marchés météo Kalshi sur 3 villes:

- Los Angeles
- New York
- Miami

Le système fait 5 choses principales:

1. récupère les marchés météo Kalshi
2. estime une probabilité pour chaque marché
3. applique un sizing discipliné
4. génère une shortlist de trades
5. suit le journal d'exécution et le bankroll

## Setup

1. crée un fichier `.env` à partir de `.env.example`
2. renseigne `OPENWEATHER_API_KEY`
3. ajuste `STARTING_BANKROLL_USD` si besoin
4. choisis `TRADE_SELECTION_MODE=balanced` ou `high_precision`

Exemple:

```bash
cp .env.example .env
```

## Entrypoints

Le repo a maintenant un vrai point d'entrée unique dans [main.py](/home/hugmu/weather_ai_agent/main.py).

Pipeline de trading:

```bash
python main.py daily
```

Collecte météo:

```bash
python main.py collect-weather
```

Evaluation du système:

```bash
python main.py evaluate-system
```

Agent Oasis high temperature:

```bash
python main.py oasis-weather --question "Highest temperature in LA today?"
python main.py oasis-weather --question "Highest temperature in NYC today?"
python main.py oasis-weather --question "Highest temperature in Miami today?"
```

`Oasis__Duc_Haven_Weather` utilise NOAA/NWS comme source officielle USA principale, puis Open-Meteo, MET Norway et NASA POWER comme consensus. Le signal `BUY_YES` n'est autorise que si NOAA est present, au moins trois sources repondent, et l'ecart type du consensus est inferieur ou egal a 0.50 F.

## Trade Selection Modes

- `balanced`: mode par défaut, plus permissif, plus proche de ton process actuel
- `high_precision`: mode beaucoup plus sélectif, conçu pour pousser le win rate vers le haut au prix d'un volume beaucoup plus faible

Le mode `high_precision` est basé sur les motifs les plus propres vus dans le backtest actuel:

- seulement `BUY_NO` ou `BUY_NO_STRONG`
- seulement `between`
- `ai_probability_yes <= 5`
- `yes_ask_percent <= 20`
- `edge >= 10`

C'est un mode expérimental orienté précision, pas un miracle garanti.

## Core Scripts

- `scripts/kalshi_signal_engine.py`: récupère les marchés et produit `data/kalshi_signals.csv`
- `scripts/kalshi_position_sizer.py`: calcule le risque et produit `data/kalshi_sized_signals.csv`
- `scripts/kalshi_trade_sheet_generator.py`: filtre les trades disciplinés et produit `data/kalshi_trade_sheet.csv`
- `scripts/kalshi_trade_blotter.py`: affiche le blotter final
- `scripts/kalshi_trade_logger.py`: logge un trade choisi depuis le trade sheet
- `scripts/kalshi_trade_settler.py`: règle un trade ouvert
- `scripts/kalshi_bankroll_updater.py`: calcule un snapshot bankroll
- `scripts/kalshi_portfolio_summary.py`: résume le portefeuille
- `scripts/kalshi_daily_runner.py`: lance le pipeline quotidien
- `scripts/kalshi_system_evaluator.py`: consolide backtest, calibration et live performance
- `scripts/kalshi_selection_rules.py`: règles réutilisables de sélection balanced / high_precision

## Position Semantics

Le projet distingue maintenant clairement deux notions:

- `recommended_stake_usd`: notionnel recommandé, c'est-à-dire l'exposition cible en dollars de payout
- `estimated_entry_cost_usd`: coût estimé pour entrer en position au prix affiché

## Evaluation Framework

La commande:

```bash
python main.py evaluate-system
```

produit:

- un résumé console de la qualité du système
- `data/kalshi_probability_calibration.csv`
- `data/kalshi_segment_performance.csv`
- `data/kalshi_system_eval_report.txt`

Elle compare maintenant aussi:

- backtest brut
- backtest discipliné
- backtest `high_precision`
- live tracker
- trades réellement exécutés

## Testing

Tests unitaires actuels:

```bash
python3 -m unittest tests/test_trading_pipeline.py tests/test_system_evaluator.py
```

