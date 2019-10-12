import dropbox
from dropbox.exceptions import ApiError
import pathlib
import datetime
import os

# Enter Access Token 
dbx = dropbox.Dropbox('ACCESS_TOKEN')
dbx.users_get_current_account()

def process_folder_entries(current_state,entries):
    for entry in entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            current_state[entry.path_lower]=entry
        elif isinstance(entry, dropbox.files.DeletedMetadata):
            current_state.pop(entry.path_lower,None)
    return current_state

def path_exists(path):
    try:
        dbx.files_get_metadata(path)
        return True
    except ApiError as e:
        if e.error.get_path().is_not_found():
            return False
        raise

# Scan files
print('Scanning for expense files...')
result = dbx.files_list_folder(path='/sample_expenses', limit=3, include_media_info=True)
    
files = process_folder_entries({}, result.entries)

while result.has_more:
    print('Collecting additional files...')
    result = dbx.files_list_folder_continue(result.cursor)
    files = process_folder_entries(files,result.entries)
    
# Make folder according to client_modified.year, month, and file type
for entry in files.values():
    path = pathlib.Path('/sorted')
    base, ext = os.path.splitext(entry.name)
    destination_path = str(path.joinpath(str(entry.client_modified.year)+"_Expenses", str(entry.client_modified.month),ext[1:]))

    if not path_exists(destination_path):
        print('Creating folder: {}'.format(destination_path))
        dbx.files_create_folder(destination_path)
    # Make filename contain today's date and copy to destination path
    print("Copying {} to {}".format(entry.path_display,destination_path))
    today = datetime.date.today()
    date = "_{0:%Y_%m_%d}".format(today)
    filename = base+date+ext
    dbx.files_copy(entry.path_lower,destination_path+'/'+filename,autorename=True)
    
print('Complete!')
    
