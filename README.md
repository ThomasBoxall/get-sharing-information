# Get Sharing Information

> Gets sharing information of a Google Drive Shared Drive

This was supposed to be a quick and dirty solution to the problem, however the further I got into it, the more fun I was having and the more interesting I wanted to make it for myself. Which is why we are here - with a relatively full-fledged Python app to do it. This is the second iteration of a solution to the problem - the first was done in Google Apps Script which it turns out isn't powerful enough for some of the Shared Drives I needed to investigate - so we are here, with a questionably better solution. 

## Configuration Options
There exists a `config.yml` file which houses the configuration options. These options are **not** optional and the script will throw a variety of unhandled errors if you don't include them. An example `config.yml` is shown below, with an explanation of each option below that:
```yml
drive_id: 'superDooperAwesomeSharedDrive'
service_account_key_filepath: './top_secret_key.json'
ignore_emails: ['i-am-an@email-address.com']
logging:
  display_to_console: True
  debug_output_file: True
```
* `drive_id`: the ID of the shared drive you wish to examine.
* `service_account_key_filepath`: the filepath to the file containing the Service Account (see below)
* `ignore_emails`: a list of emails not to include in the outputted CSV (you'll probably want to include your service account email address here)]
* `logging`
  * `display_to_console`: controls if the log messages are displayed to the console or just written to a file
  * `debug_output_file`: controls if the 'debug output' is printed to a file or not.
Note that boolean options have to be in Python's boolean format (capital initials)

## Running The Script
These are really notes for me, but if you've stumbled across this piece of highly questionable code on the internet and think it might work for you - here's some loose instructions.
1. Make sure Python 3.x is installed
2. Run following PIP command to install dependencies (might also need to install pip) 
```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
3. Create a new Google Cloud Project & enable the 'Google Drive API'
4. Sort out Authentication (as below)
5. Make sure all your Configuration options are placed in a file called `config.yml` in the project's folder
6. Run the project using the command `python3 get-sharing-information.py`


## Authentication
Uses a *Service Account* for authentication, because I wanted to be able to run it on a headless device and Oauth requires a Prompt to click on.

### Setting up Service Account
Instructions adapted from [Matheo Daly's Medium article on this](https://medium.com/@matheodaly.md/create-a-google-cloud-platform-service-account-in-3-steps-7e92d8298800)
1. Go to the Cloud Project and in the left hand menu click on 'IAM and admin' > 'Service accounts'
2. Click 'Create Service Account' at the top
3. Give it a name, ID and description. Then click 'Done' 
4. At the list of service accounts, click on the three dots for the account you want to get the key for, then click on 'Manage Keys'. 
5. Then click on 'Add Key', then 'Create New Key', Select 'JSON' then press done. It will download the new key in a `.json` file for you.
6. Place this in the project directory and call it `service_account_key.json`. **Confirm that this is being ignored by Git correctly!**

Then, for the script to be able to work, it needs to be granted access to the shared drive (done through sharing the Shared Drive with the service account's email address). View only access is fine for the Service Account to be able to do what it needs to. 

## Disclaimer
I am not a Computer Science Professional, just a student who is still learning and potentially making mistakes. I don't expect this script to work for *every* case, but it works for mine. Use at your own risk.

Be aware that this script takes ages to run on anything more than a few files - considering running in a cloud container of some description and / or overnight on your machine.

Developed on Fedora 39 so might have some quirks on Windows.