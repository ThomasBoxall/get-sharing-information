# Get Sharing Information

> Gets sharing information of a Google Drive Shared Drive

This was supposed to be a quick and dirty solution to the problem, however the further I got into it, the more fun I was having and the more interesting I wanted to make it for myself. Which is why we are here - with a relatively full-fledged Python app to do it. This is the second iteration of a solution to the problem - the first was done in Google Apps Script which it turns out isn't powerful enough for some of the Shared Drives I needed to investigate - so we are here, with a questionably better solution. 

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