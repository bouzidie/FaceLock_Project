# 🔐 FaceLock — Facial Recognition for Windows

### Système intelligent de surveillance et de verrouillage de session Windows par reconnaissance faciale

## 📌 Présentation du projet

**FaceLock** est une application Python de reconnaissance faciale conçue pour renforcer la sécurité des sessions Windows. Elle exploite des techniques de vision par ordinateur et de Deep Learning afin d'identifier les utilisateurs autorisés à partir du flux vidéo d'une webcam.

L'application surveille la présence de l'utilisateur, détecte les visages et compare leurs caractéristiques biométriques avec une base de données locale. Lorsqu'une absence est détectée pendant une durée prédéfinie, le système peut déclencher le verrouillage de la session Windows.

Le projet intègre également une approche **Privacy by Design**, privilégiant le traitement local et la gestion sécurisée des données biométriques.

## 🎯 Objectifs du projet

- Développer un pipeline complet de reconnaissance faciale en temps réel.
- Exploiter des modèles de Deep Learning pré-entraînés pour extraire les caractéristiques faciales.
- Identifier les utilisateurs autorisés à partir de leurs empreintes biométriques numériques (*face embeddings*).
- Automatiser le verrouillage de la session Windows.
- Gérer les utilisateurs et leurs données biométriques dans une base de données locale.
- Appliquer les principes de minimisation et de protection des données personnelles.

## 🏗️ Architecture technique

Le projet repose sur plusieurs modules indépendants, chacun assurant une fonction spécifique du processus d'authentification.

### 1. 📷 Acquisition vidéo — Camera Handler

- Capture du flux vidéo en temps réel à partir de la webcam.
- Extraction des images (*frames*) avec OpenCV.
- Préparation des images pour les étapes de détection et de reconnaissance.

### 2. 👤 Détection et alignement facial — Face Detector

- Détection des visages présents dans les images.
- Localisation des régions faciales.
- Préparation et alignement des visages avant l'extraction des caractéristiques.

**Technologie :** InsightFace / modèles de détection faciale.

### 3. 🧠 Extraction des caractéristiques — Face Encoder

Cette étape constitue le cœur du système de reconnaissance faciale.

- Utilisation de modèles de Deep Learning pré-entraînés.
- Extraction d'un vecteur numérique représentant les caractéristiques du visage (*face embedding*).
- Transformation des informations faciales en représentation mathématique exploitable pour la comparaison.

**Technologie :** InsightFace / ArcFace.

### 4. 🔍 Comparaison et authentification — Face Authenticator

- Comparaison de l'embedding capturé avec les embeddings des utilisateurs enregistrés.
- Calcul d'une distance ou d'un score de similarité.
- Application d'un seuil (*threshold*) pour déterminer si le visage correspond à un utilisateur autorisé.
- Gestion des utilisateurs reconnus et non reconnus.

### 5. 🗄️ Gestion des données biométriques — Database

- Stockage local des informations des utilisateurs.
- Conservation des embeddings associés aux identités enregistrées.
- Gestion des opérations d'ajout, de consultation et de suppression des utilisateurs.

**Technologie :** SQLite.

### 6. 🖥️ Contrôle du système Windows — System Controller

- Surveillance de l'état de présence de l'utilisateur.
- Détection d'une absence prolongée.
- Déclenchement du verrouillage de la session Windows via l'API système `LockWorkStation`.

L'intégration d'un véritable mécanisme de déverrouillage au niveau de l'écran sécurisé Windows nécessite une extension spécifique du système d'authentification Windows.

## 🔄 Fonctionnement global

1. L'application démarre et active la webcam.
2. Le module d'acquisition récupère les images en temps réel.
3. Le système détecte et prépare les visages présents dans les images.
4. Le modèle de Deep Learning extrait les embeddings faciaux.
5. Le module d'authentification compare les caractéristiques avec la base de données locale.
6. Le système détermine si le visage correspond à un utilisateur enregistré.
7. En cas d'absence prolongée, le contrôleur système déclenche le verrouillage de la session Windows.

## 🔐 Protection des données biométriques — Privacy by Design

La protection des données personnelles constitue un axe important de la conception de FaceLock.

| Principe | Application dans le projet |
|---|---|
| **Minimisation des données** | Privilégier le stockage des embeddings plutôt que la conservation des photos originales. |
| **Traitement local** | Effectuer les opérations de reconnaissance directement sur la machine Windows. |
| **Protection des données** | Prévoir le chiffrement de la base de données biométriques. |
| **Droit à l'effacement** | Permettre la suppression des données biométriques d'un utilisateur. |
| **Confidentialité** | Éviter la transmission des données faciales vers des services externes. |

*Remarque : un embedding reste une donnée biométrique sensible. Il ne doit pas être considéré comme impossible à exploiter ou à rapprocher d'une identité. Sa protection reste donc essentielle.*

## 🛠️ Technologies utilisées

| Catégorie | Technologies |
|---|---|
| Langage | Python |
| Vision par ordinateur | OpenCV |
| Détection faciale | InsightFace |
| Deep Learning | ArcFace, Face Embeddings |
| Comparaison faciale | Similarité / Distance euclidienne |
| Base de données | SQLite |
| Système d'exploitation | Windows |
| Contrôle système | Windows API, `ctypes` |

## 🚀 Résultats et compétences développées

- Conception d'un pipeline de reconnaissance faciale basé sur le Deep Learning.
- Exploitation de modèles pré-entraînés pour l'extraction des caractéristiques biométriques.
- Développement d'un mécanisme de comparaison et d'identification des visages.
- Gestion locale des identités et des données biométriques.
- Interaction avec les fonctionnalités système de Windows.
- Prise en compte des enjeux de confidentialité et de protection des données biométriques.

## Architecture 
<div align="center">
  <img src="./Facelock.png" alt="Architecture Face Lock" width="100%">
</div>


## 🔮 Perspectives d'amélioration

- Ajouter une interface graphique pour faciliter l'enrôlement et la gestion des utilisateurs.
- Renforcer la sécurité de la base SQLite par le chiffrement des données biométriques.
- Intégrer un mécanisme de détection du vivant (*Liveness Detection*) pour limiter les tentatives d'usurpation par photo ou vidéo.
- Améliorer la reconnaissance dans différentes conditions de luminosité.
- Étudier l'intégration avec Windows Credential Provider pour une authentification faciale au niveau de l'écran de connexion.

## 👩‍💻 Réalisation

**Islem Bouzidi**

- GitHub : [@bouzidie](https://github.com/bouzidie)

---

*Projet académique — Vision par ordinateur, Deep Learning et sécurité des systèmes Windows.*
