from django.contrib import admin
from .models import Sport, SportClub, SportTeamModel, Coach, SportsFacility, Athletic

admin.site.register(Sport)
admin.site.register(SportClub)
admin.site.register(SportTeamModel)
admin.site.register(Coach)
admin.site.register(SportsFacility)
admin.site.register(Athletic)