# Davstarship

Davstarship est un jeu de vaisseau en 2D inspiré visuellement de Space Invaders. Le joueur pilote un vaisseau spatial en bas de l'écran, évite les astéroïdes qui tombent depuis le haut de l'écran et récupère un maximum de pièces.

Le jeu utilise automatiquement les images et les sons placés dans le dossier `assets/`. Si un fichier manque, une forme simple dessinée avec Pygame reste utilisée pour que le jeu puisse quand même se lancer.

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

## Assets du jeu

Le dossier `assets/` peut contenir les images et sons du jeu. Le code cherche automatiquement les fichiers dont le nom contient ces mots-clés, même s'ils sont rangés dans des sous-dossiers :

- vaisseau : `ship`, `vaisseau` ou `davstarship` ;
- météorite petite : `little`, `small`, `petit` ou `mini` ;
- météorite moyenne : `mid`, `medium` ou `moyen` ;
- météorite grande : `big`, `large`, `grand` ou `gros` ;
- son des pièces : `coin`, `piece` ou `pièce` ;
- son de collision : `explosion`, `collision`, `colision`, `meteor`, `meteorite`, `météor`, `météorite`, `death` ou `crash` ;
- musique du jeu : `soundtrack`, `music`, `musique`, `space`, `jeu` ou `game`.

Les formats d'images acceptés sont `.png`, `.jpg`, `.jpeg`, `.bmp` et `.gif`. Les formats audio acceptés sont `.wav`, `.ogg` et `.mp3`. Par exemple, `soundtrack.mp3` sera joué en boucle au lancement du jeu, et `explosion.mp3` sera joué quand le vaisseau se crash.

## Tests pour le développement

Si tu veux lancer les tests, installe aussi `pytest`, puis lance :

```bash
python -m pytest tests
```
