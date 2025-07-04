# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from datetime import date
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CareSite(models.Model):
    care_site_id = models.IntegerField(primary_key=True)
    care_site_name = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'care_site'


class ConditionOccurrence(models.Model):
    condition_occurrence_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    condition_start_date = models.DateField()
    condition_source_value = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = 'condition_occurrence'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class HdRegions(models.Model):
    region_id = models.IntegerField(primary_key=True)
    region_name = models.CharField(max_length=50)
    region_color = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = 'hd_regions'


class Measurement(models.Model):
    measurement_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    measurement_concept_id = models.IntegerField()
    value_as_number = models.FloatField()
    measurement_datetime = models.DateTimeField()
    range_low = models.FloatField()
    range_high = models.FloatField()

    class Meta:
        managed = True
        db_table = 'measurement'


class MeasurementExt(Measurement):
    probability_km = models.FloatField(blank=True, null=True)
    probability_rsf = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'measurement_ext'


class Note(models.Model):
    note_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    note_text = models.TextField()
    note_type_concept_id = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'note'


class Observation(models.Model):
    observation_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    observation_concept_id = models.IntegerField()
    value_as_number = models.FloatField(blank=True, null=True)
    observation_datetime = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'observation'


class Person(models.Model):
    person_id = models.AutoField(primary_key=True)
    gender_concept_id = models.IntegerField()
    person_source_value = models.CharField(max_length=50, blank=True, null=True)
    birthday = models.DateField()

    class Meta:
        managed = True
        db_table = 'person'

    def idade(self):
        if self.birthday:
            today = date.today()
            return today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day)
            )
        return None



class PersonExt(Person):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    probability_km = models.FloatField(blank=True, null=True)
    probability_rsf = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'person_ext'


class VisitOccurrence(models.Model):
    visit_occurrence_id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Person, models.DO_NOTHING)
    care_site = models.ForeignKey(CareSite, models.DO_NOTHING, blank=True, null=True)
    visit_start_datetime = models.DateTimeField()
    visit_end_datetime = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'visit_occurrence'
