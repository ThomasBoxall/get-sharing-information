import os.path

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
SEARCH_FIELDS = "nextPageToken, files(id, name, mimeType, parents, permissionIds)"

masterList = []

def main():
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
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

  try:
    service = build("drive", "v3", credentials=creds)

    # Call the Drive v3 API
    results = (
        service.files()
        .list(pageSize=1, fields=SEARCH_FIELDS, includeItemsFromAllDrives=True, supportsAllDrives=True, driveId=DRIVE_ID, corpora="drive")
        .execute()
    )
    items = results.get("files", [])

    if not items:
      print("No files found.")
      return
    # print("Files:")
    # for item in items:
    #   print(f"{item['name']} ({item['id']})")
    for item in items:
        masterList.append(File(item['id'], item['mimeType'], item['name'], item['parents'], item['permissionIds']))
        try:
            for permToExamine in masterList[-1].permissionIds:
                permResults = (
                service.permissions()
                .get(fields="id, emailAddress, permissionDetails", supportsAllDrives=True, useDomainAdminAccess=False, fileId=masterList[-1].getId(), permissionId=permToExamine)
                .execute()
                )
                # print(permResults)
                masterList[-1].addPermission(Permission(permResults['id'], permResults['emailAddress'],permResults['permissionDetails']))

        except HttpError as error2:
            print(f"error: {error2}")

    npt = results.get("nextPageToken")

    # while(npt != None):
    #     results = (
    #         service.files()
    #         .list(fields=SEARCH_FIELDS, includeItemsFromAllDrives=True, supportsAllDrives=True, pageToken=npt, driveId=DRIVE_ID, corpora="drive")
    #         .execute()
    #     )   
    #     items = results.get("files", [])

    #     if not items:
    #         print("No files found.")
    #     else:
    #         print(len(items))
    #     npt = results.get("nextPageToken")
    #     for item in items:
    #         masterList.append(item)

    file = open("outputFile.txt", "w")
    for item in masterList:
        file.write(f"{item}\n")
    file.close()
    # print(masterList[0])
    

  except HttpError as error:
    # TODO(developer) - Handle errors from drive API.
    print(f"An error occurred: {error}")

  

if __name__ == "__main__":
  main()