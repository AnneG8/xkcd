from pathlib import Path
from urllib.parse import urlsplit, unquote
from dotenv import load_dotenv
import requests
import argparse
import os
import random
import pprint
IMG_FOLDER = 'images'
load_dotenv()
VK_APP_TOKEN = os.environ['VK_APP_ACCESS_TOKEN']
VK_VERS = os.environ['VK_API_VERS']


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-id', '--comic_id',
                        type=int,
                        default=0, const=0,
                        nargs='?')
    return parser


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


def get_header():
    return {'Authorization': f'Bearer {VK_APP_TOKEN}'}


def get_groups(vk_user_id):
    url = 'https://api.vk.com/method/groups.get'
    payload = {
        'extended': 1,
        'user_id': vk_user_id,
        'v': VK_VERS,
    }
    response = requests.get(url, params=payload, headers=get_header())
    response.raise_for_status()
    return response.json()


def get_server_url(vk_group_id):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    payload = {
        'group_id': vk_group_id,
        'v': VK_VERS,
    }
    response = requests.get(url, params=payload, headers=get_header())
    response.raise_for_status()
    return response.json()['response']['upload_url']


def send_file_to_serv(serv_url, file_path):
    with open(file_path, 'rb') as file:
        payload = {
            'photo': file
        }
        response = requests.post(serv_url, files=payload)
        response.raise_for_status()
        return response.json()


def save_file_to_album(vk_group_id, sending_params):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    payload = {
        'hash': sending_params['hash'],
        'photo': sending_params['photo'],
        'server': sending_params['server'],
        'group_id': vk_group_id,
        'v': VK_VERS,
    }
    response = requests.post(url, params=payload, headers=get_header())
    response.raise_for_status()
    return response.json()


def post_on_wall(img_media_id, img_owner_id, comment, vk_group_id):
    url = 'https://api.vk.com/method/wall.post'
    payload = {
        'attachments': f'photo{img_owner_id}_{img_media_id}',
        'message':comment,
        'from_group': 1,
        'owner_id': f'-{vk_group_id}',
        'group_id': vk_group_id,
        'v': VK_VERS,
    }
    response = requests.post(url, params=payload, headers=get_header())
    response.raise_for_status()
    return response.json()


def post_comic(vk_group_id, file_path, comment):
    serv_url = get_server_url(vk_group_id)
    sending_params = send_file_to_serv(serv_url, file_path)
    seving_params = save_file_to_album(vk_group_id, sending_params)
    post_on_wall(seving_params['response'][0]['id'],
                 seving_params['response'][0]['owner_id'],
                 comment,
                 vk_group_id)


def main():
    vk_user_id = os.environ['VK_USER_ID']
    vk_group_id = os.environ['VK_GROUP_ID']
    Path(IMG_FOLDER).mkdir(parents=True, exist_ok=True)

    parser = create_parser()
    args = parser.parse_args()

    if args.comic_id:
        comic_id = args.comic_id
    else:
        last_comic_id = get_xkcd_comic()['num']
        comic_id = random.randint(1, last_comic_id)
    file_path, comment = download_xkcd_comic(comic_id)
    #pprint.pprint(get_groups(vk_user_id))
    post_comic(vk_group_id, file_path, comment)


if __name__ == '__main__':
    main()