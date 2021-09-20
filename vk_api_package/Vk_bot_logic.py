import vk_api
import datetime
from random import randrange
from sql_package.SQl_table_fill import SqlDataPersons
from settings.settings import sql_name


class VkLoveSearcher:
    def __init__(self, token, user_id_num):
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.id = user_id_num
        self.database = SqlDataPersons(sql_name)
        self.user_data = self._get_user_info()
        self.person_city_id_by_name = 0
        self.sex_partner = 'м' if self.user_data['sex'] == 1 else 'ж'
        self.partner_status = 0
        self.request_data = []

    def _get_user_info(self):

        extra_data = 'bot_date,sex,city,country,occupation,relation,'
        request_data = self.vk.method('users.get', {'user_id': self.id, 'fields': extra_data})[0]
        user_age = int(datetime.datetime.now().strftime('%Y')) - int(request_data['bot_date'].split('.')[-1])
        user_photos = self._get_best_photo(self.id)
        user_data = dict(
            id=self.id,
            lastname=request_data['last_name'],
            firstname=request_data['first_name'],
            personurl=f"https://vk.com/idse{self.id}",
            age=user_age if user_age < 125 else 18,
            sex=request_data['sex'],
            city=request_data['city']['title'],
            photos=user_photos,
            photosurl=self._get_photos_url(user_photos),
            relation=request_data['relation'],
            closed=request_data['is_closed'])
        self.database.user_data = user_data
        self.database.fill_user_data()
        return user_data

    def find_persons(self, sex: str = None, age: str = None, status: str = None, city: str = None,
                     limit: int = 200) -> list:
        partner_sex = {'ж': 1,
                       'м': 2,
                       'п': 2}
        partner_status = {'свободный': 1,
                          'свободная': 1,
                          'не женат': 1,
                          'не замужем': 1,
                          'холост': 1,
                          'встречается': 2,
                          'помолвлен': 3,
                          'помолвлена': 3,
                          'женат': 4,
                          'замужем': 4,
                          'всё сложно': 5,
                          'в активном поиске': 6,
                          'влюблен': 7,
                          'влюблена': 7,
                          'в гражданском браке': 8}

        self.request_data.clear()
        sex = self.sex_partner if sex is None else sex
        sex_index = partner_sex.get(sex[0].lower(), 0)
        age = int(self.user_data['age']) if age is None else int(age)
        status = 'в активном поиске' if status is None else status
        status_index = partner_status.get(status, 6)
        city = self.user_data['city'] if city is None else city

        data_for_sql_request = dict(
            city=city,
            sex=sex_index,
            relation=status_index,
            age_from=age - 1 if age > 19 else 18,
            age_to=age + 1
        )

        request_list = self.database.get_existed_by_request(data_for_sql_request)

        if request_list:
            print("данные взяты из БД")
            self.request_data = request_list
            return self.request_data

        extra_data = 'bot_date,city,country,sex,occupation,relation'
        self.person_city_id_by_name = self.vk.method('database.getCities', {'country_id': 1, 'q': city})['items'][0][
            'id']
        print('city_id=', self.person_city_id_by_name)
        data = {'count': limit,
                'fields': extra_data,
                'city': self.person_city_id_by_name,
                'sex': sex_index,
                'status': status_index,
                'age_from': age - 1 if age > 19 else 18,
                'age_to': age + 1,
                'has_photo': 1,
                'offset': randrange(0, 15, 1),
                'v': 5.131}

        self.request_data = self.vk.method('users.search', data)['items']
        return self._format_data_to_template()

    def _format_data_to_template(self):
        format_list = []
        for person in self.request_data:

            if person.get('city', {}).get('id', None) == self.person_city_id_by_name and person.get('bot_date',
                                                                                                    None) is not None:
                personal_data = dict(
                    lastname=person['last_name'],
                    firstname=person['first_name'],
                    id=person['id'],
                    personurl=f"https://vk.com/id{person['id']}",
                    age=int(datetime.datetime.now().strftime('%Y')) - int(person.get('bot_date').split('.')[-1]),
                    sex=person['sex'],
                    city=person['city']['title'],
                    relation=person.get('relation', 6),
                    closed=person['is_closed']
                )
                format_list.append(personal_data)
            self.request_data = format_list
        return self._get_three_photo()

    def _get_best_photo(self, id):
        user_photos = self.vk.method('photos.get',
                                     {'owner_id': id, 'album_id': 'profile', 'extended': 1})
        photo_dict = {}
        for photo in user_photos['items']:
            photo_grade = int(photo['likes']['count']) + int(photo['comments']['count'])
            photo_url = f"photo{id}_{photo['id']}"
            photo_dict.setdefault(photo_grade, photo_url)

        best_photos_dict = {}
        sorted_marks = sorted(photo_dict.keys())
        if len(sorted_marks) > 3:
            for i in range(1, 4):
                best_photos_dict.setdefault(sorted_marks[-i], photo_dict[sorted_marks[-i]])
        else:
            best_photos_dict = photo_dict
        return best_photos_dict

    def _get_photos_url(self, dict_of_photos):
        result_url = ""
        for likes, photo in dict_of_photos.items():
            result_url += f'{photo},'
        return result_url

    def _get_three_photo(self):
        request_data_copy = self.request_data.copy()
        for person in request_data_copy:
            if person['closed']:
                print(f"{person['id']} закрыт для просмотра")
                self.request_data.remove(person)
                continue
            person['photos'] = self._get_best_photo(int(person['id']))
            if person['photos'] == {}:
                self.request_data.remove(person)
            person['photos_url'] = self._get_photos_url(person['photos'])
        self.database.person_data = self.request_data
        self.database.fill_person_data()

        return self.request_data

    def give_me_three_person(self):
        return self.database.get_three_users()
