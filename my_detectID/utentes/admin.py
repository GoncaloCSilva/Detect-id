from django.contrib import admin
from .models import Utente

# Register your models here.
# Register your models here.
class MemberAdmin(admin.ModelAdmin):
  list_display = ("firstname", "lastname", "birthday",)
  
admin.site.register(Utente, MemberAdmin)