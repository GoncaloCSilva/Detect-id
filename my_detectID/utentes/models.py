from django.db import models

# Create your models here.
class Utente(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    risk = models.CharField(max_length=255)
    birthday = models.DateField()

    def __str__(self):
        return f"{self.firstname} {self.lastname}"
    

class Measurement(models.Model):
    measurement_id = models.IntegerField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    measurement_concept_id = models.IntegerField()
    value_as_number = models.DecimalField(max_digits=65535, decimal_places=65535)
    measurement_datetime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'measurement'


class Note(models.Model):
    note_id = models.IntegerField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    note_text = models.TextField()
    note_type_concept_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'note'


class Observation(models.Model):
    observation_id = models.IntegerField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    observation_concept_id = models.IntegerField()
    value_as_number = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    observation_datetime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'observation'


class Person(models.Model):
    person_id = models.IntegerField(primary_key=True)
    gender_concept_id = models.IntegerField()
    year_of_birth = models.IntegerField()
    month_of_birth = models.IntegerField(blank=True, null=True)
    day_of_birth = models.IntegerField(blank=True, null=True)
    person_source_value = models.CharField(max_length=50, blank=True, null=True)

    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'person'


class UtentesUtente(models.Model):
    id = models.BigAutoField(primary_key=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    risk = models.CharField(max_length=255)
    birthday = models.DateField()

    class Meta:
        managed = False
        db_table = 'utentes_utente'

class CareSite(models.Model):
    care_site_id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'care_site'


class ConditionOccurrence(models.Model):
    condition_occurrence_id = models.IntegerField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    condition_start_date = models.DateField()
    condition_source_value = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'condition_occurrence'


class VisitOccurrence(models.Model):
    visit_occurrence_id = models.IntegerField(primary_key=True)
    person = models.ForeignKey(Person, models.DO_NOTHING)
    care_site = models.ForeignKey(CareSite, models.DO_NOTHING, blank=True, null=True)
    visit_start_datetime = models.DateTimeField()
    visit_end_datetime = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'visit_occurrence'