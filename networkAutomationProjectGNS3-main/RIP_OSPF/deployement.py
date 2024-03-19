import os, shutil

configDir = "./configRouteurTestNetwork"
dynamipsDir = "../testNetwork/project-files/dynamips/"

routersDir = []

for file in os.listdir(dynamipsDir):
    dir = os.path.join(dynamipsDir, file)
    if os.path.isdir(dir):
        print(dir)
        routersDir.append(dir)

routersConfigFilePath = {}

for routerDir in routersDir:
    for fileName in os.listdir(routerDir + "/configs/"):
        if fileName.endswith("_startup-config.cfg"):
            if fileName[1:3].isdigit() :
                id = fileName[1:3]
            else:
                id = fileName[1]
            routersConfigFilePath[id] = routerDir + "/configs/"
            print(routersConfigFilePath[id])

for id in routersConfigFilePath:   
    shutil.copy2(f"{configDir}/i{id}_startup-config.cfg", routersConfigFilePath[id])

print(f"{len(routersConfigFilePath)} config files copied from {configDir} to their GNS directories!")