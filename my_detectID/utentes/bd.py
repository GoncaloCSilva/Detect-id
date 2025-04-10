import psycopg2

def getUtentes():
    conn = psycopg2.connect(
        dbname="detectid",
        user="postgres",
        password="Goncalo123",
        host="localhost"
    )

    cur = conn.cursor()
    cur.execute("SELECT * " \
    "FROM cdmdatabaseschema.person_details " \
    "FULL JOIN cdmdatabaseschema.PERSON ON cdmdatabaseschema.PERSON.person_id = cdmdatabaseschema.PERSON_DETAILS.person_id;")
    result = cur.fetchall()
    

    cur.close()
    conn.close()

    return result