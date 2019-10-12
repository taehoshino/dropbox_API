# Classify photo files (.jpg) to folders according to location & time taken
import dropbox
from dropbox.exceptions import ApiError
import pathlib
import datetime
import os
from geopy.geocoders import Nominatim
import time

# OAuth2 authentification
auth_flow = dropbox.DropboxOAuth2FlowNoRedirect('APP_KEY','APP_SECRET')
authorize_url = auth_flow.start()
print("Go to {} and Click Allow".format(authorize_url))
auth_code = input("Enter the authorization code: ").strip()

try:
    oauth_result = auth_flow.finish(auth_code)
except Exception as e:
    print('Error: {}'.format(e))
    
dbx = dropbox.Dropbox(oauth_result.access_token)
print(dbx.users_get_current_account())

# Get current file state in a folder
def process_folder_entries(current_state,entries):
    for entry in entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            current_state[entry.path_lower]=entry
        elif isinstance(entry, dropbox.files.DeletedMetadata):
            current_state.pop(entry.path_lower,None)
    return current_state

# Check if file path exists or not
def path_exists(path):
    try:
        dbx.files_get_metadata(path)
        return True
    except ApiError as e:
        if e.error.get_path().is_not_found():
            return False
        raise
    
# Read in file list in a folder 
path = input('Enter folder path: ')
print('Scanning for photo files...')
result = dbx.files_list_folder(path, limit=3, include_media_info=True)
    
files = process_folder_entries({}, result.entries)

while result.has_more:
    print('Collecting additional files...')
    result = dbx.files_list_folder_continue(result.cursor)
    files = process_folder_entries(files,result.entries)    

# Move jpg file to a designated folder according to metadata.location and metadata.time_taken
for entry in files.values():
    base, ext = os.path.splitext(entry.name)

    if ext=='.jpg':
        if not isinstance(entry.media_info.get_metadata(),type(None)):
            metadata = entry.media_info.get_metadata()
            path = pathlib.Path('/sorted')

            # Extract location and convert it to address using geopy.geocoders.Nominatim
            if not isinstance(metadata.location,type(None)):
                loc = metadata.location
                geolocator = Nominatim(user_agent="USER_AGENT") #need to specify user agent name
                address = geolocator.reverse(str(loc.latitude)+","+str(loc.longitude),timeout=10)
                address_list = str(address).split(', ')
                city = address_list[-4] #select surburb name
                city = city.replace(' ','_')
            else:
                city = 'Unknown'

            # Extract time taken (year, month, date)
            if not isinstance(metadata.time_taken,type(None)):
                timetaken = metadata.time_taken
                year = str(timetaken.year)
                month = str(timetaken.month)
                destination_path = str(path.joinpath(year+"_Photo", month,city))
                date = "_{0:%Y_%m_%d}".format(timetaken)
                filename = city+date+ext
            else:
                year = 'Unknown'
                filename = city+'_Unknown'+ext
                if not city=='Unknown':
                    destination_path = str(path.joinpath(year+"_Photo", city))
                else:
                    destination_path = '/unsorted'
                    
            # Create folder and copy file
            if not path_exists(destination_path):
                print('Creating folder: {}'.format(destination_path))
                dbx.files_create_folder(destination_path)
            print("Copying {} to {}".format(entry.path_display,destination_path))
            dbx.files_copy(entry.path_lower,destination_path+'/'+filename,autorename=True)

        else: # if metadata is none, copy to /unsorted
            destination_path = '/unsorted'
            if not path_exists(destination_path):
                print('Creating folder: {}'.format(destination_path))
                dbx.files_create_folder(destination_path)
            print("Copying {} to {}".format(entry.path_display,destination_path))
            dbx.files_copy(entry.path_lower,destination_path+'/'+filename,autorename=True)


print('Complete!')
