import time

import psycopg2
from flask import Flask, request, render_template_string

app = Flask(__name__)
def get_db_connection():
    return psycopg2.connect(
        host='postgres',
        database='mydatabase',
        user='myuser',
        password='mypassword'
    )

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS table_Counter (
        id SERIAL PRIMARY KEY,
        datetime TIMESTAMP NOT NULL,
        client_info VARCHAR NOT NULL
    );
    """)
    conn.commit()
    cur.close()
    conn.close()


def get_and_increment_hit_count(client_info):
    retries = 5
    while True:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM table_counter')
            count = cur.fetchone()[0]
            cur.execute('INSERT INTO table_Counter (datetime, client_info) VALUES (NOW(), %s)', (client_info,))
            conn.commit()
            cur.close()
            conn.close()
            return count
        except (Exception, psycopg2.DatabaseError) as error:
            if retries == 0:
                raise error
            retries -= 1
            time.sleep(0.5)


@app.route('/')
def hello():
    client_info = request.headers.get('User-Agent')
    count = get_and_increment_hit_count(client_info)
    return 'Hello World! I have been seen {} times.\n'.format(count)


@app.route('/table')
def table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM table_counter')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    table_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Table Counter</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Table Counter</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Datetime</th>
                <th>Client Info</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''

    return render_template_string(table_html, rows=rows)

create_table()