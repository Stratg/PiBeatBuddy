# PiBeatBuddy
Drum machine for guitarists, based on a raspberry pi zero and a python script and footswitchable

Boite à rythme ou batteur virtuel pour musiciens.

La solution se base sur un raspberry pizero, un écran lcd et des commutateurs au pied, comme sur les pédales de guitare. Un encodeur rotatif permet de sélectionner le morceau à jouer, ou à régler le tempo.
Une sortie audio jack 6.35 permet de brancher la boite  rythme sur un ampli ou une sono.

Les rythmes sont créés au format texte (fichier de config). 

Pendant la sessiion, le musicien peut choisir entre trois pattern rythmique et une outtro, ou mettre en pause.

Un jeu de leds indique la posiution dans la mesure.

Chaque changement de pattern entraîne la lecture d'un shéma de transition, calé sur le rythme, afin d'amener une transition réaliste. 

Un kit de samples au format wav est utilisé, avec de variations aléatoires pour plus de réalisme.
