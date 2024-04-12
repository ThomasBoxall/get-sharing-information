import os.path
from datetime import datetime
import csv

from File import *
from Permission import *

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
DRIVE_ID = "0AEiNjzyhwT5NUk9PVA"
SEARCH_FIELDS = "nextPageToken, files(id, name, mimeType, parents, permissionIds, modifiedTime, size)"
PAGE_SIZE = 100

masterList = []

totalApiCalls = 0

def main():
    global totalApiCalls

    startTime = datetime.now()
    log(f"Starting Execution")

    log(f"Beginning Credentials Validation")

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    log(f"Credentials Validated")

    log(f"Beginning Drive API Calls")

    try:
        service = build("drive", "v3", credentials=creds)

        # Call the Drive v3 API
        totalApiCalls = totalApiCalls + 1 
        results = (
            service.files()
            .list(pageSize=PAGE_SIZE, fields=SEARCH_FIELDS, includeItemsFromAllDrives=True, supportsAllDrives=True, driveId=DRIVE_ID, corpora="drive")
            .execute()
        )
        items = results.get("files", [])
        npt = results.get("nextPageToken")

        if not items:
            print("No files found.")
            return
        else:
            appendFileToMasterList(items, service)
            log(f"Page Completed. masterList now contains {len(masterList)} items")
        
        # Now we want to continually iterate until npt is None getting the remainder of the files from the drive
        while(npt != None):
            totalApiCalls = totalApiCalls + 1 
            results = (
                service.files()
                .list(pageSize=PAGE_SIZE, fields=SEARCH_FIELDS, includeItemsFromAllDrives=True, supportsAllDrives=True, pageToken=npt, driveId=DRIVE_ID, corpora="drive")
                .execute()
            )   
            items = results.get("files", [])
            npt = results.get("nextPageToken")

            if not items:
                print("No files found.")
            else:
                appendFileToMasterList(items, service)
            log(f"List now contains {len(masterList)} items")
        log(f"Completed Drive API use. (Total Calls: {totalApiCalls})")

        log(f"Beginning processing of data for CSV export")
        outputArr = []
        for currentFile in masterList:
            outputArr.append(exportFileToCSVFormat(currentFile))
        
        # sort the outputArr by filepath [x][0] (0th element of inner arrays)
        outputArr.sort(key=lambda x:x[0])

        outputArr.insert(0, ['FILEPATH', 'NAME', 'MIME TYPE', 'EDITORS (INHERITED)', 'EDITORS (ADDED)', 'VIEWERS (INHERITED)', 'VIEWERS (ADDED)', 'LINK PERMISSIONS', 'LAST MODIFIED', 'SIZE (BYTES)'])
        
        log(f"Writing to CSV")
        with open("./output/master-output.csv", "w", newline='') as csvFile:
            writer = csv.writer(csvFile)
            for currentRow in outputArr:
                writer.writerow(currentRow)
        
        log(f"Written to CSV")
        
        endTime = datetime.now()
        log(f"Main Execution Complete. Total time elapsed: {(endTime - startTime)}")

        # finally (for debug) write out the nice looking view of masterList to file. 
        file = open("./output/outputFile.txt", "w")
        for item in masterList:
            file.write(f"{item}\n")
        file.close()

        log("Written to Debug File")
    

    except HttpError as error:
        log(f"main: {error}", "ERROR")

  
def appendFileToMasterList(items, service):
    global totalApiCalls
    for item in items:
        if 'size' in item:
            size = item['size']
        else:
            size = "n/a"
        masterList.append(File(item['id'], item['mimeType'], item['name'], item['parents'], item['permissionIds'], item['modifiedTime'], size))
        try:
            for permToExamine in masterList[-1].permissionIds:
                totalApiCalls = totalApiCalls + 1 
                permResults = (
                  service.permissions()
                  .get(fields="id, emailAddress, permissionDetails, type, displayName", supportsAllDrives=True, useDomainAdminAccess=False, fileId=masterList[-1].getId(), permissionId=permToExamine)
                  .execute()
                )
                # now add to permission list
                # initially categories that everyone has
                masterList[-1].addPermission(Permission(permResults['id'], permResults['type'],permResults['permissionDetails']))
                # now add email if type is group or user
                if(masterList[-1].permissions[-1].type == "group" or masterList[-1].permissions[-1].type == "user"):
                  masterList[-1].permissions[-1].addEmail(permResults['emailAddress'],permResults['displayName'])
                # now add inheritedFrom if inherited
                if(masterList[-1].permissions[-1].inherited):
                    masterList[-1].permissions[-1].addInheritedFrom(permResults['permissionDetails'][0]['inheritedFrom'])

        except HttpError as error:
            log(f"appendFileToMasterList: {error}", "ERROR")

def exportFileToCSVFormat(file: File):
    thisRow = []
    
    # filepath, for now add a placeholder
    thisRow.append(displayFilepath(file))
    # name
    thisRow.append(file.name)
    # mime type
    thisRow.append(file.mimeType)
    # Editors (inherited)
    thisRow.append(file.getUserPermissions(inherited=True, permissionType="edit"))
    # Editors (not inherited)
    thisRow.append(file.getUserPermissions(inherited=False, permissionType="edit"))
    # viewers (inherited)
    thisRow.append(file.getUserPermissions(inherited=True, permissionType="view"))
    # viewers (not inherited)
    thisRow.append(file.getUserPermissions(inherited=False, permissionType="view"))
    # link permissions
    thisRow.append(file.getTypedPermissions())
    # last modified
    thisRow.append(file.modifiedTime)
    #size
    thisRow.append(file.size)
    return thisRow

def getFilepath(currentFile: File):
    if currentFile.parents[0] == DRIVE_ID:
        return "/"
    else:
        # we need to find the thing in the array then recurse
        for examineFile in masterList:
            if (examineFile.id == currentFile.parents[0]):
                return  getFilepath(examineFile) + f"{examineFile.name}/"

def displayFilepath(currentFile: File):
    # call this one to get filepath as it adds the currentFile's name and potentially a slash on the end
    if currentFile.mimeType == "application/vnd.google-apps.folder":
        currFileString = f"{currentFile.name}/"
    else:
        currFileString = f"{currentFile.name}"
    return getFilepath(currentFile) + currFileString
    

def log(message, logType="INFO"):
    print(f"{logType} [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]: {message}")

if __name__ == "__main__":
  main()
