from pathlib import Path
from urllib.parse import urlsplit, unquote
from dotenv import load_dotenv
import requests
import os
import random
IMG_FOLDER = 'images'


def get_comic_id_arg():
    last_comic_id = get_xkcd_comic()['num']
    return random.randint(1, last_comic_id)


def fetch_image(image_name, url, payload=None, folder=IMG_FOLDER):
    response = requests.get(url, params=payload)
    response.raise_for_status()
    image_path = Path(folder, image_name)
    with open(image_path, 'wb') as file:
        file.write(response.content)
    return image_path


def get_xkcd_comic(comic_id=0):
    if comic_id:
        url = f'https://xkcd.com/{comic_id}/info.0.json'
    else:
        url = 'https://xkcd.com/info.0.json'

    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def download_xkcd_comic(comic_id):
    comic = get_xkcd_comic(comic_id)
    image_url = comic['img']
    comment = comic['alt']
    filename = urlsplit(unquote(image_url)).path.split('/')[2]
    return fetch_image(filename, image_url), comment


def get_server_url(vk_group_id, vk_vers, vk_app_token):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    payload = {
        'group_id': vk_group_id,
        'v': vk_vers,
    }
    header = {'Authorization': f'Bearer {vk_app_token}'}
    response = requests.get(url, params=payload, headers=header)
    response.raise_for_status()
    return response.json()['response']['upload_url']


def upload_file_to_serv(serv_url, file_path):
    with open(file_path, 'rb') as file:
        payload = {'photo': file}
    response = requests.post(serv_url, files=payload)
    response.raise_for_status()
    return response.json()


def save_file_to_album(vk_group_id, sending_hash, sending_photo,
                       sending_server, vk_vers, vk_app_token):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    payload = {
        'hash': sending_hash,
        'photo': sending_photo,
        'server': sending_server,
        'group_id': vk_group_id,
        'v': vk_vers,
    }
    header = {'Authorization': f'Bearer {vk_app_token}'}
    response = requests.post(url, params=payload, headers=header)
    response.raise_for_status()
    return response.json()


def post_on_wall(img_media_id, img_owner_id, comment, 
                 vk_group_id, vk_vers, vk_app_token):
    url = 'https://api.vk.com/method/wall.post'
    payload = {
        'attachments': f'photo{img_owner_id}_{img_media_id}',
        'message': comment,
        'from_group': 1,
        'owner_id': f'-{vk_group_id}',
        'group_id': vk_group_id,
        'v': vk_vers,
    }
    header = {'Authorization': f'Bearer {vk_app_token}'}
    response = requests.post(url, params=payload, headers=header)
    response.raise_for_status()
    return response.json()


def post_comic(vk_group_id, file_path, comment, vk_vers, vk_app_token):
    serv_url = get_server_url(vk_group_id, vk_vers, vk_app_token)
    sending_params = upload_file_to_serv(serv_url, file_path)
    seving_params = save_file_to_album(vk_group_id, 
                                       sending_params['hash'],
                                       sending_params['photo'],
                                       sending_params['server'],
                                       vk_vers,
                                       vk_app_token)
    post_on_wall(seving_params['response'][0]['id'],
                 seving_params['response'][0]['owner_id'],
                 comment,
                 vk_group_id,
                 vk_vers,
                 vk_app_token)


def main():
    load_dotenv()
    vk_app_token = os.environ['VK_APP_ACCESS_TOKEN']
    vk_vers = os.environ['VK_API_VERS']
    vk_group_id = os.environ['VK_GROUP_ID']

    Path(IMG_FOLDER).mkdir(parents=True, exist_ok=True)

    comic_id = get_comic_id_arg()

    file_path, comment = download_xkcd_comic(comic_id)
    try:
        post_comic(vk_group_id, file_path, comment, vk_vers, vk_app_token)
    finally:
        os.remove(file_path)


if __name__ == '__main__':
    main()
