import gns3fy
import telnetlib
from tabulate import tabulate
import time

# definir le serveur gns3 sur lequel on veut travailler -> voir dans les settings de gns3 pour changer le port
gns3_server = gns3fy.Gns3Connector("http://127.0.0.1:3080")

# montrer les projets sur le serveur, sous ce format : 
#   Project Name    Project ID                              Total Nodes    Total Links  Status
#   --------------  ------------------------------------  -------------  -------------  --------
#   NAP             df1698dc-ac80-43c2-a8d9-43e8323e3d08              0              0  closed
#   TEST            5a66f525-0d9f-4c30-8fa5-6f181053c821              0              0  closed
#   VRRP            816f3051-0a13-4401-8687-dba740fa3324              0              0  closed
#   VRRP-Lab        6e1e38cc-5140-46d0-9911-9deb6cb42871              0              0  closed
#   telnetTEST      6b6c934c-caaf-4f19-b536-f04262591543              3              2  opened
print(
    tabulate(
        gns3_server.projects_summary(is_print=False),
        headers=["Project Name", "Project ID", "Total Nodes", "Total Links", "Status"],
    )
)
# Definir le projet sur lequel on veut travailler
lab = gns3fy.Project(name="testNetwork", connector=gns3_server)

# voir si le projet existe
lab.get()

print("----------------------------------------------------")

# Demander à l'utilisateur combien de routeurs il y a dans le projet
num_routers = int(input("Combien de routeurs y a-t-il dans le projet ? "))
# Générer les noms des routeurs
routers = [f"R{i+1}" for i in range(num_routers)]

for router in routers: 
    router_node = lab.get_node(router)
    print(router_node)
    if router_node:  # si le noeud existe
        telnet_port = router_node.console  # on récupère le port telnet du noeud
        telnet_host = "127.0.0.1"
        telnet_timeout = 10
        tn = telnetlib.Telnet(telnet_host, telnet_port, timeout=telnet_timeout)  # connexion au routeur par telnet
        tn.write(b"\r\n")  # Envoyer une commande "Entrée" au début de la connexion -> car prompte pas encore pret
        time.sleep(0.2)  # import time
        with open(f'./configRouteurTestNetwork/{router}.txt', 'r') as file:
            for line in file:
                line = line.strip()  # Supprime les espaces blancs en début et fin de ligne
                tn.expect([b"#"])  # Attendre le prompt du routeur
                command = line  # Mettez à jour la commande
                tn.write(command.encode('ascii') + b"\r\n")  # Envoyez la commande au serveur Telnet
        tn.close()
    else:
        print(f"Node {router} not found in the project.")