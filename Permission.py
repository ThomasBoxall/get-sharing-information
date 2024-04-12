class Permission:
    def __init__(self, id, type, permissionDetails):
        self.id = id
        self.type = type
        self.permissionType = permissionDetails[0]['permissionType']
        self.role = permissionDetails[0]['role']
        self.inherited = permissionDetails[0]['inherited']
        self.emailAddress = None
        self.name = None

    def addEmail(self, email, name):
        self.emailAddress = email
        self.name = name
    
    def addInheritedFrom(self, inheritedFrom):
        self.inheritedFrom = inheritedFrom

    def __str__(self) -> str:
        if self.type == "user":
            output = f"{self.emailAddress} - {self.role} ({self.inherited}) \n"
        else:
            output = f"{self.type} - {self.role} ({self.inherited})\n"
        return output