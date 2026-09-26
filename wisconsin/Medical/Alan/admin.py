from django.contrib import admin
from .models import MedicalCenter, HospitalGallery, HospitalStatistics, Facility,FacilityMaintenance

admin.site.register(MedicalCenter)
admin.site.register(Facility)
admin.site.register(HospitalGallery)
admin.site.register(HospitalStatistics)
admin.site.register(FacilityMaintenance)