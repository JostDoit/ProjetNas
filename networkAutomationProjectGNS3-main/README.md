# Projet GNS3
> ***Le projet GNS3 à regarder en priorité est dans le dossier "configuration_finale"***
## Table des matières

- [IGP](#IGP)
  - [Interfaces passives](#Interfaces_passives)
- [BGP](#BGP)
  - [iBGP](#iBGP)
  - [eBGP](#eBGP)
- [Type de déploiement](#contribuer)
  - [Configuration finale](#configuration_finale)
  - [Explication de l'architecture](#Explication)
- [BGP Local-Preference](#localPref)
- [Règles de commununautés](#Policies)
  - [Routes entre Deux AS en Relation PEER-PEER](#PEER)
  - [Contrôle Régional des Routes](#regional)
  - [Remarque importante](#remarque)
- [Telnet](#telnet)
- [Métriques OSPF](#metric)
- [Explication de l'intent file](#intent)


## Dossier "RIP_OSPF" : 
> Ce dossier contient la première configuration requise dans le projet. On y retrouve les IGP RIP et OSPF.

### IGP

Dans la première configuration, on se propose d’étudier deux domaines voisins : L’AS A configuré selon le protocole RIP et le second AS B sous OSPF. Il communiquent entre eux par le protocole BGP. Le but de cette configuration est d’implémenter ces protocoles de routage dans des réseaux de petites tailles. Pour vérifier les performances de chacun en matière de convergence, vous pouvez supprimer ou ajouter des liens. RIP, de part sa philosophie de protocole à vecteur de distance est difficilement contrôlable lorsque le réseau commence à prendre de l’ampleur.

#### Interfaces passives

Comme dit précédemment, le réseau implémente plusieurs protocoles et le but est que chacun n’influence pas la perspective de son voisin. Pour cela, on utilise des passives interfaces sur les routeurs de bordures. Cela nos permet de bloquer l’envoie de paquet iBGP à travers le réseau eBGP. L’AS A est configuré selon RIPv3 donc la passive-interface est obtenu en désactivant ce protocole sur l’interface sortante du routeur de bordure. Pour l’AS B, on a OSPFv3 donc on introduit sur l’interface sortante du routeur la commande associée :

```bash

		R1(config-if)#passive-interface *interface*

```

### BGP

Ce protocole intra-domaine fait la jonction entre les deux vus précédemment. Il permet de lier deux AS voisins selon des politiques personnalisées.

#### iBGP 

Ce sous-protocole de BGP s’installe sur tous les routeurs de l’AS et permet de rediriger les paquets vers la sortie la plus approprié (le routeur de bordure). Nous avons choisis la stratégie « full mesh » qui nous garantit que tous les routeurs de l’AS sont voisins les uns des autres. Ainsi, on limite les erreurs de configuration sur un routeurs particulier (problème de next-hop non atteignable), on augmente la stabilité des routes et on obtient une meilleure répartition du traffic.

#### eBGP

Ce sous protocole est cette-fois-ci configuré que sur les routeurs de bordures et s’occupe uniquement de communiquer avec l’AS voisin en fournissant des nouvelles routes, des préférences de routage ou encore des intentions de rupture de liens. 

### Type de déployement

Pour déployer ce réseau :
- Nous avons utilisé un premier script permettant d'exploiter le fichier d'intention dans le but de générer les fichiers .cfg de chacun des routeurs.
- Puis dans un second temps, nous avons un script utilisant la méthode **Drag and drop bot** qui copie les fichiers .cfg dans le dossier de configurations de chaque routeur.

## Dossier "configuration_finale"
> Ce dossier contient un réseau PROVIDER-PEER-CLIENT utilisant en grande partie OSPF (car nous avions déjà démontré la configuration RIP précédemment).

### Explication de l'architecture
- Notre dossier GNS3 est composé de 9 AS, toutes utilisant des numéros d'AS privées.
- Nos AS sont reliées par le protocole de routage inter-AS BGP et dans les AS, nous utilisons OSPF (sauf dans l'AS au sud-ouest, mais cela, n'importe peu.).

### BGP Local-Preference 
Nous avons mis en place des **local preferences** spécifiques. Étant donné que nous sommes dans un réseau composé de provider-client-peer, nous devons préférer certains liens à d'autres pour joindre une destination. Dans notre intent file, nous définissons si l'AS est un PEER par exemple ce qui nous permet de prendre des décisions sur la valeur de la local preference définit au début de notre intent file. Par exemple, les liens :
- entre **client - peer** : ont une local preference définit à 200 afin de prioriser ce lien
- entre **peer - peer** : ont une local preference définit à 100
- entre **provider - peer** : ont une local preference définit à 50

En effet, dans notre architecture on **priorise** les liens clients, puis peer et enfin provider.

### Règles de Communautés CISCO

Ce projet met en avant dans deux situations distinctes l'utilisation efficace des politiques de routage BGP et des valeurs de communautés.

#### Contexte

##### 1. Routes entre Deux AS en Relation PEER-PEER

Dans cette première situation, nous abordons le scénario où deux Autonomous Systems (AS) maintiennent une relation PEER-PEER. Les AS impliqués ont décidé de ne pas échanger les routes de leurs clients et celles apprises de leurs fournisseurs de services respectifs. Pour atteindre cet objectif, chaque AS définit une règle de communauté spécifique qu'il propage à ses routeurs de bordure. Cette communauté est ensuite associée à une route qui bloque l'envoi des routes concernées.

##### 2. Contrôle Régional des Routes

La deuxième situation se concentre sur un contexte régional. Dans cet exemple, un client souhaite communiquer uniquement avec un AS voisin de son fournisseur de services, excluant les autres AS. Pour réaliser cela, le client associe ses routes à une communauté spécifique définie par son fournisseur de services. Ce dernier autorise uniquement l'envoi des routes du client à l'AS concerné, c'est-à-dire dans la région spécifiée. Ce type de contrat est souvent établi entre un fournisseur de services et son pair. Il est important de noter que si un client envoie sa route avec une étiquette, le pair intermédiaire avec le fournisseur de services étiquettera également sa route avec la même valeur de communauté.

#### Comment Utiliser ce Projet

Pour implémenter ces règles de communauté CISCO dans votre propre infrastructure, suivez ces étapes simples :

1. **Configuration PEER-PEER :** Adaptez les règles de communauté pour répondre à vos besoins spécifiques, en prenant en compte les AS impliqués et les politiques de non-partage de routes clients.

2. **Contrôle Régional des Routes :** Personnalisez les valeurs de communauté associées aux routes pour définir des contrôles régionaux, permettant une communication sélective entre clients et AS voisins.

#### Remarque Importante

Assurez-vous de comprendre les implications de chaque règle de communauté avant de les déployer dans votre infrastructure. Certaines règles bloquent le traffic dans certaines directions donc les communanautés sont à utiliser en connaissance de cause.

### Telnet
- Afin de réaliser le déploiement Telnet, nous avons modifié le fichier de création de fichier de configuration afin qu'il génère des fichiers comportant uniquement les commandes que l'utilisateur a besoin d'entrer et en les appelant R1.txt, R2.txt ...
- Pour réaliser le déploiement Telnet, nous utilisons "script.py" qui va choisir un fichier GNS3 et lister tous les nœuds configurables dans ce dernier.
- Nous nous connectons à chaque nœud en Telnet et écrivons automatiquement les commandes ligne à ligne pour chaque routeur des fichiers .txt correspondants.
- Il faut savoir qu'avant d'écrire une commande, nous nous assurons que le prompt commence par # afin d'éviter toute erreur.

### Métriques OSPF
- Nous avons manipulé les métriques OSPF, ces dernières nous permettent de prioriser des liens dans notre routage OSPF (lors du calcul de Dijkstra). Dans notre cas, nous avons utilisé les métriques OSPF dans l'AS du nord-est afin de le traffic d'optimiser le traffic. 

En effet, dans un sens nous passons par un lien tandis que dans l'autre sens, nous priorisons le traffic par un autre lien (en réalité on ajoute du poids à un liens pour passer par l'autre, on ne le priorise pas directement).

## Explication de l'intent file
- L'intent file est divisé est 3 sous-parties.
- La première contient les constantes utilisées dans le réseau, comme la version de rip ou d'ospf utilsés.
- La deuxième contient les descriptions des différents AS : leur numéro d'AS, le type d'IGP utilisé (rip ou ospf) et le préfix réseau utilisé dans l'AS. Par la suite, nous avons rajouté dans l'intent file du deuxième réseau les relations entre un AS et ses voisins (customer/peer/provider), ainsi que les communautés qu'il utilise ou bien qu'il propose.
- La troisième partie contient la description de chacun des routeurs. On y retrouve l'id du routeur, l'AS auquel il appartient et une liste décrivant ses différentes interfaces. Cette liste contient l'id du routeur voisin auquel cette interface est connectée, le nom de cette interface et si elle est connectée en igp ou en egp.
