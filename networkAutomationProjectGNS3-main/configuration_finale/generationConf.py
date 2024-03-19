import json, os



#LECTURE DE L'INTENT FILE

#Récupération de l'intent file
f = open("./intentFiles/intentFileTestNetwork.json", "r")
intentFile = json.load(f)
f.close()

outputPath = "./configRouteurTestNetwork"

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
ripName = intentFile["constantes"]["ripName"]
ospfProcess = str(intentFile["constantes"]["ospfPid"])
customerPrefValue = intentFile["constantes"]["customerPref"]
peerPrefValue = intentFile["constantes"]["peerPref"]
providerPrefValue = intentFile["constantes"]["providerPref"]
blockPeerValue = intentFile["constantes"]["blockPeerValue"]
blockRegionValue = intentFile["constantes"]["blockRegionValue"]

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
    res = open(f"{outputPath}/R{id}.txt", "w")

    res.write("enable\nconf t\n")

    #Interface de Loopback
    res.write("interface Loopback0\n"
              f" ipv6 address {id}::{id}/128\n"
              " ipv6 enable\n")
    if(igp == "rip"):
        res.write(f" ipv6 rip {ripName} enable\n")
    elif(igp == "ospf"):
        res.write(f" ipv6 ospf {ospfProcess} area 0\n")
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
                ip = "2001:101:"
                
            #Partie Sufixe
            # Si sous reseau pas encore initialise i.e premiere interface
            if matIdSousReseauxAs[id-1][neighbourID-1] == 0 and matIdSousReseauxAs[neighbourID-1][id-1]==0:                
                if link["protocol-type"] == "igp":
                    dicoSousRes[As] += 1
                    matIdSousReseauxAs[id-1][neighbourID-1], matIdSousReseauxAs[neighbourID-1][id-1] = dicoSousRes[As], dicoSousRes[As]           
                    ip += (str(dicoSousRes[As]) + "::" + str(id))
                else:
                    compteurLienAS += 1
                    matIdSousReseauxAs[id-1][neighbourID-1], matIdSousReseauxAs[neighbourID-1][id-1] = compteurLienAS, compteurLienAS
                    neighborAddress = ip + str(compteurLienAS) + "::2"
                    neighborsAddressList.append([neighborAddress,neighbourAs])
                    ip += str(compteurLienAS) + "::1"            
            else: # sous reseau deja cree
                if link["protocol-type"] == "igp":
                    ip += (str(matIdSousReseauxAs[id-1][neighbourID-1]) + "::" + str(id))
                else:
                    neighborAddress = ip + str(matIdSousReseauxAs[id-1][neighbourID-1]) + "::1"
                    neighborsAddressList.append([neighborAddress,neighbourAs])
                    ip += str(matIdSousReseauxAs[id-1][neighbourID-1]) + "::2"
            
            #Ecriture de l'interface et de son adresse IP dans le fichier de configuration
            # utilisation d'un masque /64 pour les liens IGP et /96 pour les liens EGP
            res.write(f"interface {link['interface']}\n"
                      " no ip address\n")
            if link["protocol-type"] == "egp":
                res.write(f" ipv6 address {ip}/96\n")
            else:
                res.write(f" ipv6 address {ip}/64\n")
            
            res.write(" ipv6 enable\n")

            #Gestion des différences OSPF/RIP
            if link["protocol-type"] == "igp" and igp == "rip":
                res.write(f" ipv6 rip {ripName} enable\n")
            elif igp == "ospf":
                res.write(f" ipv6 ospf {ospfProcess} area 0\n")
                if link["protocol-type"] == "egp":
                    interfacesEGP.append(link['interface'])
                try:
                    res.write(f" ipv6 ospf cost {link['ospfCost']}\n")
                except:
                    pass  
            res.write("!\n")
    
    #EGP
    res.write(f"router bgp {As}\n"
              f" bgp router-id {id}.{id}.{id}.{id}\n"
              " bgp log-neighbor-changes\n"
              " no bgp default ipv4-unicast\n")
    
    #Ajout des voisins IGP
    for router in routers:
        if router["as"] == As:
            routerID = router["id"]
            if routerID != id:                
                res.write(f" neighbor {routerID}::{routerID} remote-as {As}\n")
                res.write(f" neighbor {routerID}::{routerID} update-source Loopback0\n")
    
    #Ajout des voisins EGP
    if isASBR :
        for egpNeighborsAddress in neighborsAddressList:
            ipNeighb = egpNeighborsAddress[0]
            asNeighb = egpNeighborsAddress[1]
            res.write(f" neighbor {ipNeighb} remote-as {asNeighb}\n")
    
    res.write(
              " address-family ipv6\n")

    #Annonce du préfixe de l'AS et donc de tous les sous-réseaux de l'AS
    res.write(f"  network {asPrefix[As]}:/48\n")

    #On active les loopbacks des autres routeurs de l'AS
    for router in routers:
        if router["as"] == As:
            routerID = router["id"]
            if routerID != id:
                res.write(f"  neighbor {routerID}::{routerID} activate\n")
    
    if isASBR:
        #On récupère les infos de l'as auquel appartient le routeur
        for a in asList:                
            if a["id"] == As:
                try:
                    asCustomers = a["customers"]
                except:
                    asCustomers = []
                try:
                    asPeers = a["peers"]
                except:
                    asPeers = []
                try:
                    asProviders = a["providers"]
                except:
                    asProviders = []
                try:
                    asPeerToBlock = a["peerToBlock"]
                except:
                    asPeerToBlock = []
                try:
                    asCommunityToUse = a["community-to-use"]
                except:
                    asCommunityToUse = []
                try:
                    asRegionToBlock = a["regionToBlock"]
                except:
                    asRegionToBlock = []
                break
        
        #Pour chaque voisin EGP
        for egpNeighborsAddress in neighborsAddressList:
            res.write(f"  neighbor {egpNeighborsAddress[0]} activate\n")

            #LocalPref client>peer>provider
            if egpNeighborsAddress[1] in asCustomers:
                res.write(f"  neighbor {egpNeighborsAddress[0]} route-map customer in\n")
            elif egpNeighborsAddress[1] in asPeers:
                res.write(f"  neighbor {egpNeighborsAddress[0]} route-map peer in\n")
            elif egpNeighborsAddress[1] in asProviders:
                res.write(f"  neighbor {egpNeighborsAddress[0]} route-map provider in\n")
            
            #Blocking Peer Community
            if egpNeighborsAddress[1] in asPeerToBlock:
                res.write(f"  neighbor {egpNeighborsAddress[0]} route-map BlockRoutePeer out\n")
                for router in routers:
                    if router["as"] == As:
                        routerID = router["id"]
                        if routerID != id:
                            res.write(f"  neighbor {routerID}::{routerID} send-community\n")
            
            #Blocking Region
            for region in asRegionToBlock:
                if egpNeighborsAddress[1] == region:
                    res.write(f"  neighbor {egpNeighborsAddress[0]} route-map RM_BLOCK_CLIENT_ROUTE_TO_{region} out\n")
            
            if len(asCommunityToUse) > 0:
                for community in asCommunityToUse:
                    res.write(f"  neighbor {egpNeighborsAddress[0]} route-map RM{community[0]} out\n")
            

    
    res.write(" exit-address-family\n")

    if isASBR and len(asPeerToBlock) > 0:
        res.write("ip bgp-community new-format\n"
                  f"ip community-list standard blockPeerPeer permit {As}:{blockPeerValue}\n"
                  f"ip as-path access-list 10 deny _{blockPeerValue}$"
                  "\n!\n")

    if isASBR:
        res.write(f"ipv6 route {asPrefix[As]}:/48 Null0\n")
    # IGP
    if(igp == "rip"):
        res.write(f"ipv6 router rip {ripName}\n"
                  " redistribute connected\n")
                  
    if(igp == "ospf"):
        res.write(f"ipv6 router ospf {ospfProcess}\n"
                  f" router-id {id}.{id}.{id}.{id}\n")
        if isASBR:           
            for interfaceName in interfacesEGP:
                res.write(f" passive-interface {interfaceName}\n")
            #A decocher pour tout annoncer
            #res.write(" redistribute connected\n")
    if isASBR:
        ##Route-maps
        res.write("!\n"
                  "route-map customer permit 10\n"
                  f" set local-preference {customerPrefValue}\n"
                  "!\n"
                  "route-map peer permit 10\n"
                  f" set local-preference {peerPrefValue}\n"
                  "!\n"
                  "route-map provider permit 10\n"
                  f" set local-preference {providerPrefValue}\n"
                  "!\n")
        
        if len(asPeerToBlock) > 0:
            for _ in asPeerToBlock:                
                res.write("route-map BlockRoutePeer permit 10\n"
                        " match as-path 10\n"
                        f" match community {As}:{blockPeerValue}\n"
                        f" set community {As}:{blockPeerValue}\n"
                        "!\n")
        
        if len(asRegionToBlock) > 0:
            stop = False
            for region in asRegionToBlock:
                for router in routers:
                    if router["as"] == region:                
                        for adj in router["adj"]:
                            neighbourID = adj["neighbor"]                            
                            if neighbourID == id:                
                                res.write(f"exit\nipv6 prefix-list PL_BLOCK_CLIENT_ROUTE_TO_{region} seq 10 deny ::/0\n"
                                        f"route-map RM_BLOCK_CLIENT_ROUTE_TO_{region} permit 10\n"
                                        f" match community {As}:{blockRegionValue}\n"
                                        f" match ipv6 address prefix-list PL_BLOCK_CLIENT_ROUTE_TO_{region}\n"
                                        "!\n")
                                stop = True
                                break
                    if stop:
                        break
                if stop:
                    break
        
        if len(asCommunityToUse) > 0:
            for community in asCommunityToUse:
                res.write(f"ipv6 prefix-list PL{community[0]} seq 10 permit {asPrefix[As]}:/48\n"
                          f"route-map RM{community[0]} permit 10\n"
                          f" match ip address prefix-list PL{community[0]}\n"
                          f" set community {As}:{community[1]}\n"
                          "!\n")
    
                
    res.write("!\n")
    
    res.close()

    print(f"Configuration du routeur {id} generee !")