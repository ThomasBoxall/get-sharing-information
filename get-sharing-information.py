import os.path
from datetime import datetime
import csv
import yaml
import sys
import requests

from File import *
from Permission import *

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError



# Declare constant constants
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
SEARCH_FIELDS = "nextPageToken, files(id, name, mimeType, parents, permissionIds, modifiedTime, size)"
PAGE_SIZE = 100
OUTPUT_DIR = "./output/" # this isn't a config option because of logging funsies. Maybe something to look at improving in the future for this "quick and dirty" script...

# declare 'constants' which get set from config.yml
DRIVE_ID = ""
SERVICE_ACCOUNT_KEY_FILE = ""
IGNORE_EMAILS = []
DISPLAY_LOGGING_TO_CONSOLE = False
DEBUG_OUTPUT_FILE = False
NTFY_URL = ""

# declare global variables
masterList = []
filesToExamine = []
totalApiCalls = 0

def initialise():
    log("Starting Initialisation")
    global DRIVE_ID, SERVICE_ACCOUNT_KEY_FILE, IGNORE_EMAILS, OUTPUT_DIR, DISPLAY_LOGGING_TO_CONSOLE, DEBUG_OUTPUT_FILE, NTFY_URL
    # initialise configuration options
    try:
        with open('config.yml', 'r') as configYml:
            configData = yaml.safe_load(configYml)
    except FileNotFoundError as fnfError:
        print("config.yml not found - see README for instructions")
        sys.exit()
    DRIVE_ID = configData['drive_id']
    SERVICE_ACCOUNT_KEY_FILE = configData['service_account_key_filepath']
    IGNORE_EMAILS = configData['ignore_emails']
    DISPLAY_LOGGING_TO_CONSOLE = configData['logging']['display_to_console']
    DEBUG_OUTPUT_FILE = configData['logging']['debug_output_file']
    NTFY_URL = configData['logging']['ntfy_url']
    log("Configuration Options Initialised")

    # initialise output directory
    if not os.path.exists(OUTPUT_DIR):
        log("Creating output Directory")
        os.makedirs(OUTPUT_DIR)
    
    # if log file exists - empties it, if not - creates it
    open(f"{OUTPUT_DIR}get-sharing-information.log", 'w').close()

    log("Initialisation complete")


def main():
    global totalApiCalls

    startTime = datetime.now()
    log(f"Starting Main Execution", ntfy=True)

    log(f"Beginning Credentials Validation")

    creds = None
    creds = service_account.Credentials.from_service_account_file(
                              filename=SERVICE_ACCOUNT_KEY_FILE, 
                              scopes=SCOPES)

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
            for currentItem in items:
                filesToExamine.append(currentItem)
            log(f"File Page Retrieved. Contained {len(items)} files")
        
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
                for currentItem in items:
                    filesToExamine.append(currentItem)
            log(f"File Page Retrieved. Contained {len(items)} files")

        # now we have appended all the files to filesToExamine, so we can do some useful logging
        log(f"Retrieved all files. (Total Files: {len(filesToExamine)})")

        examineFiles(service)

        log(f"Completed Drive API use. (Total Calls: {totalApiCalls})")

        log(f"Beginning processing of data for CSV export")
        outputArr = []
        for currentFile in masterList:
            outputArr.append(exportFileToCSVFormat(currentFile))
        
        # sort the outputArr by filepath [x][0] (0th element of inner arrays)
        outputArr.sort(key=lambda x:x[0])

        outputArr.insert(0, ['FILEPATH', 'NAME', 'MIME TYPE', 'EDITORS (INHERITED)', 'EDITORS (ADDED)', 'VIEWERS (INHERITED)', 'VIEWERS (ADDED)', 'LINK PERMISSIONS', 'LAST MODIFIED', 'SIZE (BYTES)', 'CHILDREN (ALL)', 'CHILDREN (FILES)', 'CHILDREN (FOLDERS)'])
        
        log(f"Writing to CSV")
        with open(f"{OUTPUT_DIR}master-output.csv", "w", newline='') as csvFile:
            writer = csv.writer(csvFile)
            for currentRow in outputArr:
                writer.writerow(currentRow)
        
        log(f"Written to CSV")
        
        endTime = datetime.now()
        log(f"Main Execution Complete. Total time elapsed: {(endTime - startTime)}", ntfy=True)

        if DEBUG_OUTPUT_FILE:
            # finally (for debug) write out the nice looking view of masterList to file. 
            file = open(f"{OUTPUT_DIR}outputFile.txt", "w")
            for item in masterList:
                file.write(f"{item}\n")
            file.close()

            log("Written to Debug File")
    

    except HttpError as error:
        log(f"main: {error}", "ERROR")

  
def examineFiles(service):
    global totalApiCalls
    counter = 0
    examineBatch = 100
    for currentFile in filesToExamine:
        if 'size' in currentFile:
            size = currentFile['size']
        else:
            size = "n/a"
        masterList.append(File(currentFile['id'], currentFile['mimeType'], currentFile['name'], currentFile['parents'], currentFile['permissionIds'], currentFile['modifiedTime'], size))
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
            log(f"examineFiles: {error}", "ERROR")

        counter = counter + 1
        if(counter == examineBatch):
            log(f"Examined {examineBatch} Files. (Total examined: {len(masterList)})")
            counter = 0
    log(f"Completed Examining Files. (Total examined: {len(masterList)})")
    

def exportFileToCSVFormat(file: File):
    thisRow = []
    
    # filepath, for now add a placeholder
    thisRow.append(displayFilepath(file))
    # name
    thisRow.append(file.name)
    # mime type
    thisRow.append(file.mimeType)
    # Editors (inherited)
    thisRow.append(file.getUserPermissions(inherited=True, permissionType="edit", ignore=IGNORE_EMAILS))
    # Editors (not inherited)
    thisRow.append(file.getUserPermissions(inherited=False, permissionType="edit", ignore=IGNORE_EMAILS))
    # viewers (inherited)
    thisRow.append(file.getUserPermissions(inherited=True, permissionType="view", ignore=IGNORE_EMAILS))
    # viewers (not inherited)
    thisRow.append(file.getUserPermissions(inherited=False, permissionType="view", ignore=IGNORE_EMAILS))
    # link permissions
    thisRow.append(file.getTypedPermissions())
    # last modified
    thisRow.append(file.modifiedTime)
    #size
    thisRow.append(file.size)
    # children
    thisRow.append(getCountChildren(file, "all"))
    # children (files)
    thisRow.append(getCountChildren(file, "file"))
    # children (folders)
    thisRow.append(getCountChildren(file, "folder"))
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

def getCountChildren(file: File, filter: str):
    children = 0
    if filter == "all":
        for examineFile in masterList:
            if(examineFile.parents[0] == file.id):
                children = children + 1
    elif filter == "file":
        for examineFile in masterList:
            if examineFile.mimeType != "application/vnd.google-apps.folder":
                if(examineFile.parents[0] == file.id):
                    children = children + 1
    elif filter == "folder":
        for examineFile in masterList:
            if examineFile.mimeType == "application/vnd.google-apps.folder":
                if(examineFile.parents[0] == file.id):
                    children = children + 1
    return children


def log(message, logType="INFO", ntfy=False):
    logTime = datetime.now()
    # first we check and potentially print to the console
    if DISPLAY_LOGGING_TO_CONSOLE:
        print(f'{logType} [{logTime.strftime("%Y-%m-%d %H:%M:%S")}]: {message}')
    # now we write to file
    with open(f"{OUTPUT_DIR}get-sharing-information.log", "a") as logFile:
        logFile.write(f'{logType} [{logTime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]}]: {message}\n')
    logFile.close()
    # now deal with ntfy, if this fails - oh well
    if(ntfy==True or logType=="ERROR"):
        try: 
            requests.post(NTFY_URL,
            data=f'{logType} [{logTime.strftime("%Y-%m-%d %H:%M:%S")}]: {message}',
            headers={
                "Title": f"{logType} from GetSharingInformation",
            })
        except :
            log(f"NTFY Failed for previous error", "WARN")

if __name__ == "__main__":
  initialise()
  main()
