from vk_api_package.VKbot import VkBotLovers
from settings.settings import token
if __name__ == '__main__':
    session = VkBotLovers(token_bot=token)
    session.start_bot()
