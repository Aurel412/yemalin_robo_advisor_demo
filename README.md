
# YEMALIN Robo-Advisor – Démo investisseur (Streamlit)

Ce dépôt contient une **version démo** du robo-advisor YEMALIN permettant aux investisseurs
de tester l'interface et la logique générale d'allocation, sans exposer le cœur du modèle propriétaire.

## Structure du projet

```text
.
├── app.py                 # Application Streamlit (interface)
├── demo_model.py          # Moteur démo simplifié (à distinguer du vrai modèle)
├── requirements.txt       # Dépendances pour Streamlit Cloud
└── .streamlit
    └── config.toml        # Configuration optionnelle de Streamlit
```

## Lancement en local

1. Créer un environnement virtuel (optionnel mais recommandé)
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Lancer l'application :
   ```bash
   streamlit run app.py
   ```

## Déploiement sur Streamlit Cloud

1. Pousser ce dossier sur un dépôt GitHub public ou privé.
2. Aller sur <https://share.streamlit.io>, connecter votre compte GitHub.
3. Créer une nouvelle app et sélectionner votre dépôt + branche + `app.py` comme fichier principal.
4. Streamlit installera automatiquement les dépendances définies dans `requirements.txt`.

## Protection du modèle propriétaire

- Cette version **démo** utilise `demo_model.py` qui contient une logique volontairement
  simplifiée (score rendement/risque avec contraintes de liquidité, nombre maximal d'actifs, etc.).
- Le **vrai moteur d'optimisation** (Markowitz complet, Monte Carlo, signaux, etc.) doit rester
  dans un dépôt privé et/ou derrière une API sécurisée.
- Pour les démonstrations investisseurs, vous pouvez :
  - Garder cette version démo publique.
  - Afficher dans la documentation que les résultats définitifs proviennent d'un moteur avancé propriétaire.

## Avertissement

Cette application est fournie à des fins de **démonstration** uniquement et ne constitue pas
un conseil en investissement. Les performances passées ne préjugent pas des performances futures.
