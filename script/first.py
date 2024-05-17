import requests
from bs4 import BeautifulSoup
import psycopg2
import os

base_url = 'https://career.habr.com'


def connect():
    conn = psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB'),
        user=os.environ.get('POSTGRES_USER'),
        password=os.environ.get('POSTGRES_PASSWORD'),
        host=os.environ.get('POSTGRES_HOST')
    )
    return conn


def parse(url_link):
    response = requests.get(url_link)
    soup = BeautifulSoup(response.content, 'html.parser')
    resume_cards = soup.find_all('article', {'class': 'resume-card'})
    result = []
    for card in resume_cards:
        profile_link = card.find('a', {'class': 'resume-card__title-link'})['href']
        offer_text = card.find('div', {'class': 'resume-card__offer'}).getText()
        if 'От ' in offer_text and '•' in offer_text:
            salary = offer_text.split('От ')[1].split('•')[0].strip().replace(' ', '')
        else:
            salary = None
        result.append([base_url+profile_link, salary])
    return result


if __name__ == "__main__":
    url = "https://career.habr.com/resumes"
    try:
        db_connect = connect()
        if db_connect.status == 1:
            print('DB connected')
            resumes = parse(url)
            print('Parsed successful')
            with db_connect.cursor() as curs:
                curs.execute("INSERT INTO resumes (link, salary) VALUES "+", ".join([f"('{resume[0]}', '{resume[1]}')" for resume in resumes])+"ON CONFLICT (link) DO UPDATE SET salary = EXCLUDED.salary;")
                print('Data write successful')
                curs.close()
            db_connect.commit()
            db_connect.close()
        else:
            print('DB not connected')
    except Exception as e:
        print(f'DB connection error: {e}')


