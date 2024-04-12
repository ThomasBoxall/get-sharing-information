class File:
    def __init__(self, id, mimeType, name, parents, permissionIds, modifiedTime, size):
        self.id = id
        self.mimeType = mimeType
        self.name = name
        self.parents = parents
        self.permissionIds = permissionIds
        self.permissions = []
        self.modifiedTime = modifiedTime
        self.size = size

    def __str__(self):
        output = f"+ {self.name} ({self.id})\n"
        output += f" - {self.mimeType}\n"
        output += f" - {self.parents}\n"
        output += f" - {self.permissionIds}\n"
        output += f" - {self.modifiedTime}\n"
        output += f" - {self.size}\n"
        output += f"+ Permissions \n"
        for i in range(len(self.permissions)):
            output += f" - {self.permissions[i]}"
        return output
    
    def getId(self):
        return self.id

    def getFirstPerm(self):
        return self.permissionIds[0]
    
    def addPermission(self, permission):
        self.permissions.append(permission)

    def getUserPermissions(self, inherited, permissionType):
        returnStr = ""
        match permissionType:
            case "edit":
                validPermissions = ['organizer', 'fileOrganizer', 'writer']
            case "view":
                validPermissions = ['commenter', 'reader']
            case _:
                validPermissions = []
        for currentPerm in self.permissions:
            if currentPerm.role in validPermissions:
                # we are dealing with an "editor" permission
                if inherited:
                    if(currentPerm.emailAddress and currentPerm.inherited):
                        # we have an email address added permission & a inherited permission
                        returnStr = returnStr + f"{currentPerm.name} <{currentPerm.emailAddress}> ({currentPerm.role})\n"
                else:
                    # not inherited
                    if(currentPerm.emailAddress and not currentPerm.inherited):
                        # we have an email address added permission & a not inherited permission
                        returnStr = returnStr + f"{currentPerm.name} <{currentPerm.emailAddress}> ({currentPerm.role})\n"
        return returnStr

    def getTypedPermissions(self):
        returnStr = ""
        for currentPerm in self.permissions:
            if currentPerm.type != "user" and currentPerm.type != "group":
                returnStr = returnStr + f"{currentPerm.type}:{currentPerm.role}\n"
        return returnStr