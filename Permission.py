class Permission:
    def __init__(self, id, emailAddress, permissionDetails):
        self.id = id
        self.emailAddress = emailAddress
        self.permissionType = permissionDetails[0]['permissionType']
        self.role = permissionDetails[0]['role']
        self.inheritedFrom = permissionDetails[0]['inheritedFrom']
        self.inherited = permissionDetails[0]['inherited']

    def __str__(self) -> str:
        output = f"{self.emailAddress} - {self.role} ({self.inherited}) \n"
        return output