import os
import requests
import subprocess

def download_file(url):
    print(f"Downloading file from URL: {url}") 
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Failed to download file from {url} due to error: {e}")
        return None

def save_file(content, target_path):
    with open(target_path, 'wb') as f:
        f.write(content)

def get_current_version(file_content):
    lines = file_content.decode().splitlines()
    version_dict = {}
    for line in lines:
        key, value = line.split(':')
        version_dict[key] = value.strip()
    return version_dict

url_files = "https://repo.hexaflare.net/s/sPForCjyQYJJXAC/download/link_files.json"
response = requests.get(url_files)
response.raise_for_status()
files = response.json()

target_folder = os.path.expanduser('~/Documents/PepalAutoAttendance')

if not os.path.exists(target_folder):
    os.makedirs(target_folder)
    subprocess.run('attrib +h ' + target_folder, shell=True)

for filename, url in files.items():
    _, ext = os.path.splitext(url)
    target_path = os.path.join(target_folder, filename + ext)
    
    if filename != "version" and os.path.exists(target_path):
        continue

    content = download_file(url)
    
    if filename == "version":
        online_versions = get_current_version(content)

        if os.path.exists(target_path):
            with open(target_path, 'rb') as f:
                local_content = f.read()
            local_versions = get_current_version(local_content)

            if local_versions.get('version_programme') != online_versions.get('version_programme'):
                _, ext_main = os.path.splitext(files['main'])
                save_file(download_file(files['main']), os.path.join(target_folder, 'main' + ext_main))
            if local_versions.get('version_chrome_driver') != online_versions.get('version_chrome_driver'):
                _, ext_chrome = os.path.splitext(files['chromedriver'])
                save_file(download_file(files['chromedriver']), os.path.join(target_folder, 'chromedriver' + ext_chrome))
        
    save_file(content, target_path)

_, ext_main = os.path.splitext(files['main'])
subprocess.Popen(os.path.join(target_folder, 'main' + ext_main))

