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

## Installation sur Mac avec Thonny

1. Installe Python et Thonny si ce n'est pas déjà fait.
2. Ouvre Thonny.
3. Installe Pygame dans l'interpréteur utilisé par Thonny :
   - menu `Tools` > `Manage packages...` ;
   - recherche `pygame` ;
   - clique sur `Install`.
4. Ouvre le fichier `main.py` situé à la racine de ce dossier.
5. Clique sur le bouton vert `Run` de Thonny.

## Lancer le jeu depuis un terminal

```bash
python main.py
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

## Tests pour le développement

Si tu veux lancer les tests, installe aussi `pytest`, puis lance :

```bash
python -m pytest tests
```
