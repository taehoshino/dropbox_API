# upload to or download from a dropbox folder
import dropbox
from dropbox.exceptions import ApiError
import datetime
import os
from natsort import natsorted
from sys import exit

# OAuth2 authentification
def auth():
    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect('APP_KEY','APP_SECRET') #Enter APP_KEY and APP_SECRET
    authorize_url = auth_flow.start()
    print("Go to {} and Click Allow".format(authorize_url))
    auth_code = input("Enter the authorization code: ").strip()
    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        print('Error: {}'.format(e))

    dbx = dropbox.Dropbox(oauth_result.access_token)
    print(dbx.users_get_current_account())
    
    return dbx

# Check if file path exists or not
def path_exists(path):
    try:
        dbx.files_get_metadata(path)
        return True
    except ApiError as e:
        if e.error.get_path().is_not_found():
            return False
        raise
     
    
# Get current file state in a folder    
def process_folder_entries(current_state,entries):
    for entry in entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            current_state[entry.path_lower]=entry
        elif isinstance(entry, dropbox.files.DeletedMetadata):
            current_state.pop(entry.path_lower,None)
    return current_state


# Upload files in a selected local folder        
def upload(dbx):        

    folder_path = input('Enter folder path to be uploaded from: ')
    folder_list = natsorted(os.listdir(folder_path))
    print('Listing upload files ...')
    for i, l in enumerate(folder_list):
        print('      {}'.format(l))
        if i==len(folder_list)-1:
            print('------- Total {} files'.format(i+1))
    yes_or_no = input('Enter "yes" or "no" to proceed: ').lower()
    if yes_or_no == 'no':
        sys.exit('Stopped by user.')

    dbx_folder_path = input('Enter folder path to upload to: ')
    if not path_exists(dbx_folder_path):
        print('Create {}'.format(dbx_folder_path))
        dbx.files_create_folder(dbx_folder_path)

    print('Uploading files...')
    for l in folder_list:
        print('Uploading {}'.format(l))
        from_path = folder_path+'/'+l
        to_path = dbx_folder_path+'/'+l
        with open(from_path, 'rb') as f:
            data = f.read()
        dbx.files_upload(data,to_path,dropbox.files.WriteMode.add)

    print('Upload Complete!')

# Download files from a selected dropbox folder
def download(dbx):

    dbx_folder_path = input('Enter folder path to download from: ')
    if not path_exists(dbx_folder_path):
        sys.exit('Path not found!')
    
    print('Collecting files...')
    result = dbx.files_list_folder(dbx_folder_path, limit=3)
    files = process_folder_entries({},result.entries)
    
    while result.has_more:
        print('Collecting additional files...')
        result = dbx.files_list_folder_continue(result.cursor)
        files = process_folder_entries(files,result.entries)
    
    print('Listing files...')
    for i, entry in enumerate(files.values()):
        print('file {}:  {}'.format(i, entry.name))
        if i==len(files.values())-1:
            print('------- Total {} files'.format(i+1))
    
    yes_or_no = input('Enter "yes" or "no" to proceed: ').lower()
    if yes_or_no == 'no':
        sys.exit('Stopped by user.')

    folder_path = input('Enter download folder path: ')
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
            print('Creating the directory {}'.format(folder_path))
        except OSError:
            raise

    for entry in files.values():
        to_path = folder_path+'/'+entry.name
        from_path = entry.path_lower
        md = dbx.files_download_to_file(to_path, from_path)
        print('{} bytes downloaded: {}'.format(md.size,entry.name))
    
    print('Download Complete!')

            
# main    
dbx = auth()

up_or_down = input('Upload(U) or Download(D)').lower()
if up_or_down == 'u':
    upload(dbx)
else:
    download(dbx)
