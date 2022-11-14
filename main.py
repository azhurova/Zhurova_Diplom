import os
import json
import requests
from urllib.parse import urlparse
from pprint import pprint

DEFAULT_PHOTO_COUNT = 5

VK_APP_ID = '51467773'
VK_APP_TOKEN = 'vk1.a.C53YcRT3uISzXZFLwpDrh7yucni3Tq5oZcyl-3AeieQkSjcQGsP6577rrscJ_0jMBEJbBc2q27xeyKgdVSvxSh8T_Vu7TVQNAme9zssPtEWz_rsx8XD5n7AeXHzw-w-KsAbb6nWVYsmz_KlvHw6EyNWQX55V5gBsjWdWUPoQhujrvOkzyoSXyQue2rj0c-DyhCrI2X9UsPPK7OsQ8Bo1OQ'


class Vk:

    def __init__(self, user_id, access_token, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def photo_list(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': '1', 'photo_sizes': '1'}
        response = requests.get(url, params={**self.params, **params})
        return response.json()


class YaDisk:

    def __init__(self, access_token):
        self.token = access_token
        self.headers = {'Authorization': 'OAuth ' + self.token}

    def is_directory_exists(self, path):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': path}
        response = requests.get(url, headers=self.headers, params={**params})
        return response.status_code == 200

    def create_directory(self, path):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': path}
        response = requests.put(url, headers=self.headers, params={**params})
        return response.status_code == 201

    def upload_file(self, path, file_url):
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': path, 'url': file_url}
        response = requests.post(url, headers=self.headers, params={**params})
        if response.status_code == 202:
            return response.json()['href']
        else:
            return ''


vk_id = input('Введите id пользователя vk:')
disk_token = input('Введите токен с Полигона Яндекс.Диска:')

vk = Vk(vk_id, VK_APP_TOKEN)
photo_info_json = vk.photo_list()
print('Получен список доступных файлов из профиля VK:', vk_id, ',', photo_info_json['response']['count'], 'шт')

# 1. Переменная photo_url_list = список ссылок на файлы: размер, лайки, URL фото
# (цикл по photo_info_json с переносом значений в результирующий список id, size.width, size.height, likes.count, sizes.url)
photo_url_list = []
for item in photo_info_json['response']['items']:
    file_with_max_size = max(item['sizes'], key=lambda file_size: file_size['height'] * file_size['width'])
    photo_url_list.append(
        {'id': item['id'], 'size': str(file_with_max_size['width']) + 'x' + str(file_with_max_size['height']),
         'likes': item['likes']['count'], 'url': file_with_max_size['url']})
print('Сформирован список файлов максимального размера:', len(photo_url_list), 'шт')

# 2. Делаем цикл по sort_photo_list и сохраняем на яндекс диск
# 2.1 В каждой итерации делать логирование с занесением результата в json_file

photo_count = min(len(photo_url_list), DEFAULT_PHOTO_COUNT)
print('На Яндекс.Диск будет загружены файлы:', photo_count, 'шт')

files_directory_name = 'VK' + vk_id
ya_disk = YaDisk(disk_token)

if not ya_disk.is_directory_exists(files_directory_name):
    ya_disk.create_directory(files_directory_name)
    print('Создана папка для фотографий:', files_directory_name)
else:
    print('Уже существует папка для фотографий:', files_directory_name)

print('Загрузка файлов на Яндекс.Диск:')
photo_log_list = []
for i in range(photo_count):
    url_path = urlparse(photo_url_list[i]['url']).path

    file_name = os.path.splitext(url_path)[0].split('/')[-1]
    file_extension = os.path.splitext(url_path)[1]

    ya_disk_file_name = str(photo_url_list[i]['id']) + '_likes_' + str(
        photo_url_list[i]['likes']) + '_' + file_name + file_extension
    print(i + 1, ya_disk_file_name)

    ya_disk.upload_file(files_directory_name + '/' + ya_disk_file_name, photo_url_list[i]['url'])
    photo_log_list.append({'file_name': ya_disk_file_name, 'size': photo_url_list[i]['size']})
print('Конец. Загружены файлы:', photo_count, 'шт')

with open('result' + files_directory_name + '.json', 'w') as f:
    json.dump(photo_log_list, f)
pprint(photo_log_list)