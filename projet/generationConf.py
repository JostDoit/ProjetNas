import json, os

#LECTURE DE L'INTENT FILE

#Récupération de l'intent file
f = open("./intentFile.json", "r")
intentFile = json.load(f)
f.close()

outputPath = "./configRouteur"

#Routeurs
routers = intentFile["routers"]
nbRouter = len(routers)

#AS
asList = intentFile["as"]
nbAs = len(asList)

#Dictionnaire contenant les couples idAs / Préfixe réseau associé
asPrefix = {}
for i in range(nbAs):
    asInfos = asList[i]
    asPrefix[asInfos["id"]] = asInfos["ip-prefix"]

#Dictionnaire contenant les index des derniers sous-reseaux utilises pour chaque AS.
#Utilsé pour la generation des adresses IP des liens IGP
dicoSousRes = {} 
for id in asPrefix:
    dicoSousRes[id] = 0

#Initialisation d'une matrice contenant les numeros des sous-reseaux entre chaque routeur
#Utilsé pour la generation des adresses IP des liens IGP
matIdSousReseauxAs = [] 
for i in range(0,nbRouter):
    matIdSousReseauxAs.append([])
    for j in range(nbRouter):
        matIdSousReseauxAs[i].append(0)

#Variable utilisé pour compter le nombre de sous-réseau entre AS
#Utilisé pour la generation des adresses IP des liens EGP
compteurLienAS = 0

#Constantes
egp = intentFile["constantes"]["egp"]
ospfProcess = str(intentFile["constantes"]["ospfPid"])

#Ecriture de la configuration pour chaque routeur
for router in routers:
    
    #Recuperation des infos du routeur
    id = router["id"]
    As = router["as"]
    neighborsAddressList = []   #Liste qui contiendra les adresses IP des voisins EGP du routeur
    interfacesEGP = []          #Liste qui contiendra les noms des interfaces EGP du routeur, afin de les déclarer plus tard en passives intarfaces dans le processus OSPF
    isASBR = False

    #Recuperation de l'IGP utilise par l'AS (RIP ou OSPF)
    for i in asList:
        if i["id"] == As:
            igp = i["igp"]
    
    #Creation du fichier de configuration du routeur sous la même forme que les fichiers de configuration de GNS3
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    res = open(f"{outputPath}/i{id}_startup-config.cfg", "w")

    res.write("enable\nconf t\n")

    #Interface de Loopback
    res.write("interface Loopback0\n"
              f" ip address {id}.{id}.{id}.{id} 255.255.255.255\n"
              " ip enable\n")
    if(igp == "ospf"):
        res.write(f" ip ospf {ospfProcess} area 0\n")
    res.write("!\n")

    #Interfaces
    for adj in router["adj"]:
        
        #Recuperation de l'AS du routeur connecte a l'interface
        neighbourID = adj["neighbor"]
        for router in routers:
            if router["id"]==neighbourID:           
                neighbourAs = router["as"]
        
        for link in adj["links"]:
            #Generation de l'addresse IP

            #Partie Prefixe
            if link["protocol-type"] == "igp":
                ip = asPrefix[As]
            else:
                isASBR = True                
                ip = "192.168." 
                
            #Partie Sufixe
            # Si sous reseau pas encore initialise i.e premiere interface
            if matIdSousReseauxAs[id-1][neighbourID-1] == 0 and matIdSousReseauxAs[neighbourID-1][id-1]==0:                
                if link["protocol-type"] == "igp":
                    dicoSousRes[As] += 1
                    matIdSousReseauxAs[id-1][neighbourID-1], matIdSousReseauxAs[neighbourID-1][id-1] = dicoSousRes[As], dicoSousRes[As]           
                    ip += (str(dicoSousRes[As]) + "." + str(id))
                else:
                    compteurLienAS += 1
                    matIdSousReseauxAs[id-1][neighbourID-1], matIdSousReseauxAs[neighbourID-1][id-1] = compteurLienAS, compteurLienAS
                    neighborAddress = ip + str(compteurLienAS) + ".2" 
                    neighborsAddressList.append([neighborAddress,neighbourAs])
                    ip += str(compteurLienAS) + ".1"      
            else: # sous reseau deja cree
                if link["protocol-type"] == "igp":
                    ip += (str(matIdSousReseauxAs[id-1][neighbourID-1]) + "." + str(id))
                else:
                    neighborAddress = ip + str(matIdSousReseauxAs[id-1][neighbourID-1]) + ".1" 
                    neighborsAddressList.append([neighborAddress,neighbourAs])
                    ip += str(matIdSousReseauxAs[id-1][neighbourID-1]) + ".2" 
            
            #Ecriture de l'interface et de son adresse IP dans le fichier de configuration
            res.write(f"interface {link['interface']}\n"
                      " no ip address\n")
          
            res.write(f" ip address {ip} 255.255.255.252\n")

            #OSPF
            if igp == "ospf":
                res.write(f" ip ospf {ospfProcess} area 0\n")
                if link["protocol-type"] == "egp":
                    interfacesEGP.append(link['interface'])

            res.write(f" mpls ip\n mpls label protocol ldp\n")
            res.write("!\n")
    
    #EGP
    res.write(f"router bgp {As}\n"
              f" bgp router-id {id}.{id}.{id}.{id}\n"
              " bgp log-neighbor-changes\n")
    
    #Ajout des voisins IGP
    for router in routers:
        if router["as"] == As:
            routerID = router["id"]
            if routerID != id:                
                res.write(f" neighbor {routerID}.{routerID}.{routerID}.{routerID} remote-as {As}\n")
                res.write(f" neighbor {routerID}.{routerID}.{routerID}.{routerID} update-source Loopback0\n")
    
    #Ajout des voisins EGP
    if isASBR :
        for egpNeighborsAddress in neighborsAddressList:
            ipNeighb = egpNeighborsAddress[0]
            asNeighb = egpNeighborsAddress[1]
            res.write(f" neighbor {ipNeighb} remote-as {asNeighb}\n")
    
    res.write(" address-family ipv4\n")

    #Annonce du préfixe de l'AS et donc de tous les sous-réseaux de l'AS
    res.write(f"  network {asPrefix[As]}0.0\n")

    #On active les loopbacks des autres routeurs de l'AS
    for router in routers:
        if router["as"] == As:
            routerID = router["id"]
            if routerID != id:
                res.write(f"  neighbor {routerID}.{routerID}.{routerID}.{routerID} activate\n")
    
    if isASBR:
        #Pour chaque voisin EGP
        for egpNeighborsAddress in neighborsAddressList:
            res.write(f"  neighbor {egpNeighborsAddress[0]} activate\n")
    
    res.write(" exit-address-family\n")

    if isASBR:
        res.write(f"ipv6 route {asPrefix[As]}:/48 Null0\n") # MODIF
    
    # IGP
                  
    if(igp == "ospf"):
        res.write(f"router ospf {ospfProcess}\n" 
                  f" router-id {id}.{id}.{id}.{id}\n")
        if isASBR:           
            for interfaceName in interfacesEGP:
                res.write(f" passive-interface {interfaceName}\n")
            #A decocher pour tout annoncer
            #res.write(" redistribute connected\n")
    
    res.close()

    print(f"Configuration du routeur {id} generee !")