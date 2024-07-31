import gdown
from pathlib import Path

def download_from_google_drive(file_id, destination_folder, destination_filename):
    """
    Download a file from Google Drive and save it locally, creating the destination folder if it doesn't exist.

    :param file_id: str, The file ID from the Google Drive shareable link.
    :param destination_folder: str, The folder where the file should be saved.
    :param destination_filename: str, The name of the file to save as.
    """
    # Construct the Google Drive download URL
    url = f'https://drive.google.com/uc?id={file_id}'
    
    # Create the destination path
    destination_path = Path(destination_folder) / destination_filename
    
    # Ensure the destination folder exists
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Download the file
    gdown.download(url, str(destination_path), quiet=False)

    print(f'File downloaded and saved as {destination_path}')

if __name__ == "__main__":
    # Google Drive file ID from the shareable link
    file_id = '1U6_CIIzURYMffv5yrdcrzwLTRVjdWaYi'

    # Folder to save the file
    destination_folder = r'./models'

    # Filename to save as
    destination_filename = 'unet_downloaded.h5'

    # Download the file
    download_from_google_drive(file_id, destination_folder, destination_filename)
