class File:
    def __init__(self, id, mimeType, name, parents, permissionIds):
        self.id = id
        self.mimeType = mimeType
        self.name = name
        self.parents = parents
        self.permissionIds = permissionIds
        self.permissions = []

    def __str__(self):
        output = f"+ {self.name} ({self.id})\n"
        output += f" - {self.mimeType}\n"
        output += f" - {self.parents}\n"
        output += f" - {self.permissionIds}\n"
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