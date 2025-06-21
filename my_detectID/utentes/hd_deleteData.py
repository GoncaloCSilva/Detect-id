from django.db import connection

from models import CareSite, ConditionOccurrence, Measurement, MeasurementExt, Note, Observation, Person, PersonExt, VisitOccurrence

def deleteData():
    # Carregar o DataFrame com os person_id

    # Apagar medições
    Measurement.objects.all().delete()
    MeasurementExt.objects.all().delete()

    print("Medições removidas!")

    # Apagar condições
    ConditionOccurrence.objects.all().delete()
    print("Diagnósticos removidos!")

    # Apagar notas
    Note.objects.all().delete()
    print("Notas removidas!")

    # Apagar observações
    Observation.objects.all().delete()
    print("Observações removidas!")

    # Apagar visitas
    VisitOccurrence.objects.all().delete()
    print("Visitas removidas!")

    # Apagar os care sites (opcional e perigoso se partilhados com outras pessoas)
    CareSite.objects.all().delete()
    print("Care Sites removidos!")

    # Por fim, apagar os utentes
    Person.objects.all().delete()
    PersonExt.objects.all().delete()
    print("Pessoas removidas!")

    def reset_sequence(table_name, pk_column):
        seq_name = f"{table_name}_{pk_column}_seq"
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1;")

    # Exemplo para person:
    reset_sequence('person', 'person_id')