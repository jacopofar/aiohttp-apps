import uuid
import configparser
from os import path, makedirs
# all configuration goes in this module, or is loaded from here
# TODO which library to implement 12-factor-style configuration? maybe https://github.com/rochacbruno/dynaconf
web_port = 8080

secret_token = str(uuid.uuid4())
print(f'\n\n+++ the secret token is {secret_token} +++\n\n')

data_folder = path.join(path.abspath(path.dirname(__file__)), 'persistent_data')
makedirs(data_folder, exist_ok=True)

print(f'the data folder path is {data_folder}')

config = configparser.ConfigParser()
config.read('config.ini')
jwt_secret = secret_token
jwt_algorithms = ['HS256']

if 'JWT' not in config:
    print('WARNING, no JWT secret or key in config.ini file, secret token will be used for JWT validation instead...')
else:
    jwt_secret = config['JWT']['jwt_secret']
    jwt_algorithms = config['JWT']['jwt_algorithms'].split(' ')


