from pprint import pprint

from itertools import groupby
import json
import re
import requests
from fake_headers import Headers
from bs4 import BeautifulSoup

HOST = 'https://spb.hh.ru/search/vacancy?text=python&area=1&area=2'


# "сливаем" данные в JSON
def get_headers():
    return Headers(browser='chrome', os='win').generate()


def json_dump(data):
    with open('data.txt', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    with open('data.txt', 'r', encoding='utf-8') as f:
        x = json.load(f)
        pprint(x)


# "вытаскиваем" з/п с помощью регулярок
def translate_salary(data):
    salary_pattern = re.compile(r"([а-яё]+)\s*[\<\>\-\s\!]*(\d+)\s(\d+)[\<\>\-\s\!]*([а-яё]+)*[\<\>\-\s\!]"
                                r"*(\d+)*\s(\d+)*[\<\>\-\s\!]*([а-яё*A-Z*]"
                                r"+\.*)[\<\>\=\"\-\s\![a-z]+]*([а-яё\s]+)")
    salary_tag = data('div')
    for salary in salary_tag:
        sal = salary('span')
        if len(sal) != 0:
            group_list = []
            sal = str(sal)
            salary_search = re.search(salary_pattern, sal)
            if salary_search is not None:
                i = 1
                while i <= 8:
                    if salary_search.group(i) is not None:
                        group_list.append(salary_search.group(i))
                    i += 1
            if len(group_list) == 0:
                salary_correct = 'з/п не указана'
            else:
                salary_correct = ' '.join(group_list)
            return salary_correct


# формируем данные для записи в JSON
def get_results(data, href):
    title_tag = data.find(class_='vacancy-title')

    company_tag = data.find(class_='vacancy-company-name')
    name = company_tag.find('a').find('span')
    if name is None:
        name = company_tag.find('a').find('span').find('span')
    name = name.text

    location_tag = data.find(class_='vacancy-company-redesigned')
    location = location_tag.find('p')
    if location is None:
        location = 'Не определено'
    else:
        location = location.text

    salary = translate_salary(title_tag)

    return name, location, salary, href


# код для парсинга
def parsing():
    # парсим пул вакансий
    html = requests.get(HOST, headers=get_headers()).text
    bs = BeautifulSoup(html, parser='lxml', features='lxml')
    vacancies = bs.find(class_='main-content')
    data_pool = vacancies.find_all('h3')
    href_list = []

    # извлекаем ссылки для открытия страниц
    for i in data_pool:
        a = i('span')
        if a is not None:
            for b in a:
                c = b('a')
                for d in c:
                    ref = d['href']
                    href_list.append(ref)

    text_list = []
    par1 = re.compile(r"Django")
    par2 = re.compile(r"Flask")
    data_for_dump = {'vacancies': []}
    final_data = []
    for href in href_list:
        html1 = requests.get(href, headers=get_headers()).text
        bs1 = BeautifulSoup(html1, parser='lxml', features='lxml')
        text_tag = bs1.find(class_='g-user-content').text
        text_list.append(text_tag)
        for text in text_list:
            search1 = re.search(par1, text)
            search2 = re.search(par2, text)
            if search1 is not None or search2 is not None:
                data = get_results(bs1, href)
                data = tuple(data)
                final_data.append(data)
    # чистим повторяющиеся данные
    big_final_data = [el for el, _ in groupby(final_data)]
    for final_data in big_final_data:
        data_for_dump['vacancies'].append({
            'company_name': final_data[0],
            'location': final_data[1],
            'salary': final_data[2],
            'href': final_data[3]
            })
    return data_for_dump
