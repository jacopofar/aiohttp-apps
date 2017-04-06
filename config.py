import uuid
# all configuration goes in this module, or is loaded from here
web_port = 8080

secret_token = str(uuid.uuid4())
print(f'\n\n+++ the secret token is {secret_token} +++\n\n')