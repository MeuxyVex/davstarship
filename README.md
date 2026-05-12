# Davstarship

Davstarship est un jeu de vaisseau en 2D inspiré visuellement de Space Invaders. Le joueur pilote un vaisseau spatial en bas de l'écran, évite les astéroïdes qui tombent depuis le haut de l'écran et récupère un maximum de pièces.

Les images et sons définitifs pourront être ajoutés plus tard. Pour l'instant, le jeu utilise des formes simples dessinées avec Pygame afin de rester jouable sans assets externes.

## Fonctionnalités incluses

- Page d'accueil avec bouton pour démarrer le vol.
- Contrôle du vaisseau uniquement de gauche à droite avec les flèches du clavier.
- Astéroïdes générés aléatoirement en haut de l'écran.
- Pièces générées aléatoirement et ajoutées à un compteur visible pendant la partie.
- Vitesse de descente fixe pour les obstacles et les pièces.
- Difficulté progressive : les astéroïdes apparaissent de plus en plus souvent avec le temps.
- Détection de collisions :
  - une pièce augmente le compteur ;
  - un astéroïde termine la partie.
- Écran de résumé après le crash avec le temps de vol et les pièces récoltées.
- Emplacements prévus pour une musique d'ambiance et des sons d'effets.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer le jeu

```bash
python -m davstarship.main
```

## Contrôles

- `Entrée` ou `Espace` : démarrer ou recommencer une partie.
- `Flèche gauche` : déplacer le vaisseau vers la gauche.
- `Flèche droite` : déplacer le vaisseau vers la droite.
- `Échap` : quitter le jeu.

## Ajouter les assets plus tard

Quand les images et sons seront disponibles, ils pourront être placés dans un dossier `assets/` à la racine du projet. Le code charge déjà ces fichiers audio s'ils existent :

```text
assets/sounds/space_music.ogg
assets/sounds/coin.wav
assets/sounds/death.wav
```

Les graphismes temporaires sont centralisés dans `davstarship/main.py` et pourront être remplacés par des images Pygame.

## Tests

```bash
pytest
```
