from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from datetime import datetime
import time
import re
from Vk_bot_logic import VkLoveSearcher
from settings.settings import token, bot_id


class VkBotLovers:
    def __init__(self, token_bot):
        self.vk = vk_api.VkApi(token=token_bot)
        self.server_pool = VkLongPoll(self.vk)
        self.user_id = 0

    def _write_msg(self, user_id_num, message):
        self.vk.method('messages.send', {'user_id': user_id_num, 'message': message, 'random_id': randrange(10 ** 7), })

    def _attach_photo(self, user_id_num, message, attachment):
        self.vk.method('messages.send', {'user_id': user_id_num, 'message': message, 'attachment': attachment,
                                         'random_id': randrange(10 ** 7), })

    def _greetings_mes(self):
        today_date = datetime.today().strftime('%d%m%Y')
        text = 'Привет, хочешь найти себе пару? ' \
               'как в Tinder но в Вконтакте? ' \
               'Набери в ответе на данной сообщение:OK чтобы начать' \
               'Далее прошу следовать указанным инструкциям, спасибо'
        prev_greeting = self.vk.method('messages.search', {'q': text, 'date': today_date, 'v': 5.131})
        if prev_greeting['count'] != 0:
            delta_time = time.mktime(datetime.now().timetuple()) - prev_greeting['items'][0]['date']
            text = 'Вижу ты уже пользовался ботом. Для продолжения жми ОК' if delta_time < 600 else text
        return text

    def _print_persons(self, user):
        check_list = user.give_me_three_person()
        if not check_list:
            self._write_msg(self.user_id, f"выборка завершена. Чтобы оформить новый запрос, введите Новый")
            return None
        for elem in check_list:
            self._attach_photo(self.user_id,
                               f"{elem['name']}: {elem['vk_url']}\nТоп 3 самых "
                               f"популярных фото",
                               elem['photos'])

    def _send_matches(self, user1):

        print(f'найдено {len(user1.request_data)} совпадений')
        self._print_persons(user=user1)
        self._write_msg(self.user_id,
                        'Если вы желаете посмотреть другие варианты введите :  Далее или Выход ')

    def start_bot(self):
        step_action = 0
        for event in self.server_pool.listen():

            if event.type != VkEventType.MESSAGE_NEW:
                continue
            if not event.to_me:
                continue
            if not event.from_user:
                continue
            self.user_id = event.user_id
            user_msg = event.message.lower()

            if step_action == 0:
                self._write_msg(self.user_id, self._greetings_mes())
                step_action += 1

            if step_action == 1:

                if user_msg == "ок":
                    self._write_msg(self.user_id,
                                    f'Начинаю обработку, Передай мне токен, для доступа к приложению\n'
                                    'для получения токена перейди по ссылке ниже и вставь ответом результат полностью\n'
                                    f'https://oauth.vk.com/authorize?client_id={bot_id}&display=page&scope=stats'
                                    '.offline&response_type=token&v=5.130')
                    step_action += 1

            if step_action == 2:
                user_msg = re.findall(r"access_token=(.{85})", user_msg)
                if not user_msg:
                    continue
                if len(user_msg[0]) != 85:
                    continue
                token_user = user_msg[0]
                self._write_msg(self.user_id,
                                'Токен принят\n'
                                'Введите в одной строке пол / возраст / семейное положение / город предполагаемого '
                                'партнера\n '
                                'Если вы ищете человека своего возраста и из вашего города, то вводите "мест"')
                user1 = VkLoveSearcher(token_user, user_id_num=self.user_id)
                step_action += 1

                user_msg = ""

            if step_action == 3:

                if user_msg.lower() == 'мест':
                    self._write_msg(self.user_id, 'Ищем пару по данным по умолчанию, твой город, твой возраст')
                    user1.find_persons()
                    self._send_matches(user1)
                    step_action += 1

                elif len(user_msg.split('/')) == 4:
                    input_data = user_msg.split('/')
                    self._write_msg(self.user_id, 'Обрабатываю запрос:')
                    user1.find_persons(sex=input_data[0],
                                       age=input_data[1],
                                       status=input_data[2],
                                       city=input_data[3].capitalize())
                    self._send_matches(user1)
                    step_action += 1

            if step_action == 4:
                if user_msg == 'далее':
                    self._write_msg(self.user_id, f'Высылаю предварительные результаты.Следующая попытка:')
                    self._print_persons(user1)
                if user_msg == 'выход':
                    self._write_msg(self.user_id, 'Успехов в делах любовных. Я спать')
                    step_action = 0
                if user_msg == 'новый':
                    step_action = 3
                    self._write_msg(self.user_id,
                                    'Введите в одной строке пол / возраст / семейное положение / город '
                                    'предполагаемого партнера\n '
                                    'Если вы ищете человека своего возраста и из вашего города, то вводите "мест"')
                    continue


if __name__ == '__main__':
    session = VkBotLovers(token_bot=token)
    session.start_bot()
