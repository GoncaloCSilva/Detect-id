from django.contrib import admin
from .models import Person

# Register your models here.
# Register your models here.
class MemberAdmin(admin.ModelAdmin):
  list_display = ("birthday","gender_concept_id")
  
admin.site.register(Person, MemberAdmin)