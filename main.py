from pathlib import Path
from urllib.parse import urlsplit, unquote
from dotenv import load_dotenv
import requests
import argparse
import os
import random
IMG_FOLDER = 'images'


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-id', '--comic_id',
                        type=int,
                        default=0, const=0,
                        nargs='?')
    return parser


def get_comic_id_arg():
    parser = create_parser()
    args = parser.parse_args()

    last_comic_id = get_xkcd_comic()['num']
    if args.comic_id:
        if args.comic_id > last_comic_id:
            raise ValueError(
                f'Не существует комикса с номером {args.comic_id}.\n'
                f'Последний комикс имеет номер {last_comic_id}.'
            )
        return args.comic_id
    else:
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


def get_header(vk_app_token):
    return {'Authorization': f'Bearer {vk_app_token}'}


def get_server_url(vk_group_id, vk_vers, vk_app_token):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    payload = {
        'group_id': vk_group_id,
        'v': vk_vers,
    }
    response = requests.get(url, 
                            params=payload, 
                            headers=get_header(vk_app_token))
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


def save_file_to_album(vk_group_id, sending_params, vk_vers, vk_app_token):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    payload = {
        'hash': sending_params['hash'],
        'photo': sending_params['photo'],
        'server': sending_params['server'],
        'group_id': vk_group_id,
        'v': vk_vers,
    }
    response = requests.post(url, 
                             params=payload, 
                             headers=get_header(vk_app_token))
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
    response = requests.post(url, 
                             params=payload, 
                             headers=get_header(vk_app_token))
    response.raise_for_status()
    return response.json()


def post_comic(vk_group_id, file_path, comment, vk_vers, vk_app_token):
    serv_url = get_server_url(vk_group_id, vk_vers, vk_app_token)
    sending_params = send_file_to_serv(serv_url, file_path)
    seving_params = save_file_to_album(vk_group_id, 
                                       sending_params, 
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

    try:
        comic_id = get_comic_id_arg()
    except ValueError as err:
        print(err)
        return

    file_path, comment = download_xkcd_comic(comic_id)
    post_comic(vk_group_id, file_path, comment, vk_vers, vk_app_token)
    os.remove(file_path)


if __name__ == '__main__':
    main()
