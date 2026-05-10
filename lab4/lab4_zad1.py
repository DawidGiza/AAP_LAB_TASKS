# -*- coding: utf-8 -*-

!apt-get -qq update
!apt-get -qq install postgresql postgresql-contrib

!service postgresql start

!sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

!pip install psycopg2-binary requests

import requests
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

cur.execute("""
DROP TABLE IF EXISTS users;
""")

cur.execute("""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    country TEXT,
    city TEXT,
    age INT,
    gender TEXT
);
""")

conn.commit()

url = "https://randomuser.me/api/?results=30"

response = requests.get(url)
data = response.json()["results"]

for user in data:
    first_name = user["name"]["first"]
    last_name = user["name"]["last"]
    email = user["email"]
    country = user["location"]["country"]
    city = user["location"]["city"]
    age = user["dob"]["age"]
    gender = user["gender"]

    cur.execute("""
        INSERT INTO users
        (first_name, last_name, email, country, city, age, gender)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (first_name, last_name, email, country, city, age, gender))

conn.commit()

print("Dodano 30 użytkowników.")

cur.execute("""
SELECT COUNT(*)
FROM users
WHERE gender = 'male';
""")

men_count = cur.fetchone()[0]

cur.execute("""
SELECT AVG(age)
FROM users;
""")

avg_age = cur.fetchone()[0]

cur.execute("""
SELECT COUNT(DISTINCT country)
FROM users;
""")

countries_count = cur.fetchone()[0]

print("Liczba mężczyzn:", men_count)
print("Średni wiek:", round(avg_age, 2))
print("Liczba krajów:", countries_count)