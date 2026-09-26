from django.contrib import admin
from .models import *


admin.site.register(FacilityRoomAllocation)
admin.site.register(RoomPurposeAllocation)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        'department_code',
        'department_name',
        'school',
        'email',
        'status',
    )

    search_fields = (
        'department_code',
        'department_name',
    )

    list_filter = (
        'school',
        'status',
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'course_code',
        'course_name',
        'department',
        'credits',
        'status',
    )

    search_fields = (
        'course_code',
        'course_name',
    )

    list_filter = (
        'department',
        'status',
    )



from django.contrib import admin
from .models import *


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):

    list_display = (
        "building_code",
        "building_name",
        "status",
        "is_full_crud",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "building_code",
        "building_name",
        "address",
    )

    list_filter = (
        "status",
        "is_full_crud",
        "created_at",
    )

    ordering = (
        "building_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (

        ("Building Information", {

            "fields": (
                "building_name",
                "building_code",
                "address",
                "building_image",
            )

        }),

        ("Status", {

            "fields": (
                "status",
                "is_full_crud",
            )

        }),

        ("Audit Information", {

            "fields": (
                "created_at",
                "updated_at",
            )

        }),

    )


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = (
        'building',
        'floor_name',
        'floor_number',
        'is_full_crud',
    )

    search_fields = (
        'floor_name',
        'building__building_name',
        'building__building_code',
    )

    list_filter = (
        'building',
        'is_full_crud',
    )

    ordering = (
        'building',
        'floor_number',
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number',
        'room_name',
        'floor',
        'room_type',
        'capacity',
        'status',
        'has_projector',
        'has_computers',
        'has_ac',
    )

    search_fields = (
        'room_number',
        'room_name',
        'floor__floor_name',
        'floor__building__building_name',
    )

    list_filter = (
        'room_type',
        'status',
        'has_projector',
        'has_computers',
        'has_ac',
        'floor__building',
    )

    ordering = (
        'floor__building',
        'floor__floor_number',
        'room_number',
    )