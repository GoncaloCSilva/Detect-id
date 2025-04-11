from django.contrib import admin
from .models import Person

# Register your models here.
# Register your models here.
class MemberAdmin(admin.ModelAdmin):
  list_display = ("first_name", "last_name", "day_of_birth","month_of_birth","year_of_birth")
  
admin.site.register(Person, MemberAdmin)