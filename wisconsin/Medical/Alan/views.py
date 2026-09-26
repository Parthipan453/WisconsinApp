from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST,require_http_methods
from django.http import JsonResponse
import json
import random
import string
import uuid
from django.db import transaction
from .models import Facility,MedicalCenter,HospitalGallery,FacilityMaintenance,HospitalStatistics
from Medical.models import MedicalStaffProfile,MedicalDepartment
from Admin.models import User
from Admin.bela_admin.models import Building,Floor,Room,FacilityRoomAllocation,RoomPurposeAllocation
from .forms import FacilityForm,MedicalCenterForm,FacilityMaintenanceForm
import json
from django.core.paginator import Paginator
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Sum,Q
from django.db.models import Exists, OuterRef



def hospital_dashboard(request):
    
    hospitals = MedicalCenter.objects.select_related("statistics").order_by("-created_at")
    
    total_hospitals = hospitals.count()

    total_beds = (
        HospitalStatistics.objects.aggregate(
            total=Sum("total_beds")
        )["total"] or 0
    )
    
    total_facilities = Facility.objects.filter(
        is_active=True
    ).count()
    
    under_maintenance = (
        FacilityMaintenance.objects.filter(
            status__in=["running", "pending"],
            is_active=True
        )
        .values("facility")
        .distinct()
        .count()
    )
    
    assigned_facility_ids = set()

    for hospital in MedicalCenter.objects.filter(is_active=True):
        assigned_facility_ids.update(hospital.selected_facilities or [])
        assigned_facility_ids.update(hospital.selected_other_facilities or [])
    
    running_maintenance = FacilityMaintenance.objects.filter(
        facility=OuterRef("pk"),
        is_active=True, status__in=["running", "pending"])
    
    facilities = (
        Facility.objects.filter(
            id__in=assigned_facility_ids,
            is_active=True
        )
        .annotate(
            has_maintenance=Exists(running_maintenance)
        )
        .order_by("facility_type", "name")
    )
    
    context = {
        "hospitals":hospitals,
        "total_hospitals": total_hospitals,
        "total_beds" : total_beds,
        "total_facilities": total_facilities,
        "under_maintenance": under_maintenance,
        "facilities": facilities,
    }
    return render(request, "alan/hospital_dashboard.html", context)


# FACILITY MANITENANCE MODAL IN MAIN DASHBOARD

def facility_maintenance_details(request, facility_id):
    
    facility = get_object_or_404(
        Facility,id=facility_id,
        is_active=True
    )
    
    hospitals = MedicalCenter.objects.filter(is_active=True)
    
    available_hospitals = []
    maintenance_hospitals = []
    
    for hospital in hospitals:
        
        assigned_facilities = (
            (hospital.selected_facilities or []) + (hospital.selected_other_facilities or [])
        )
        
        if facility.id not in assigned_facilities:
            continue
        
        maintenance = (
            FacilityMaintenance.objects.filter(
                hospital=hospital,
                facility=facility,
                status__in=["running","pending"],
                is_active=True
            ).order_by("-created_at").first()
        )
        
        if maintenance:

            maintenance_hospitals.append({

                "hospital": hospital.hospital_name,

                "title": maintenance.title,

                "description": maintenance.description,

                "status": maintenance.status,

                "priority": maintenance.priority,

                "engineer": maintenance.assigned_engineer,

                "contact": maintenance.contact_number,

                "start_date": maintenance.start_date.strftime("%d %b %Y"),

                "expected_completion": (
                    maintenance.expected_completion.strftime("%d %b %Y")
                    if maintenance.expected_completion
                    else "-"
                ),

                "remarks": maintenance.remarks,
            })
        
        else:
            
            available_hospitals.append({
                "hospital":hospital.hospital_name
            })
    
    response = {
        
        "success": True,
        "facility": {
            "id": facility.id,

            "name": facility.name,

            "icon": facility.icon,

            "type": facility.get_facility_type_display(),
        },
        
        "summary": {
            
            "total_hospitals": len(available_hospitals) + len(maintenance_hospitals),

            "available": len(available_hospitals),

            "maintenance": len(maintenance_hospitals),
        },
        
        "available_hospitals": available_hospitals,

        "maintenance_hospitals": maintenance_hospitals,
    }
    
    return JsonResponse(response)

# Hospital code generator

def generate_hospital_code():
    """
    Generate a unique hospital code.
    Example:
        HSP483921
        HSP902174
    """

    while True:
        hospital_code = "HSP" + "".join(
            random.choices(string.digits, k=6)
        )

        if not MedicalCenter.objects.filter(
            hospital_code=hospital_code
        ).exists():
            return hospital_code

def create_hospital(request):
    
    medical_facilities = list(
        Facility.objects.filter(
            facility_type="medical",
            is_active=True
        ).values(
            "id","name","icon"
        )
    )
    
    other_facilities = list(
        Facility.objects.filter(
            facility_type="other",
            is_active=True
        ).values(
            "id","name","icon"
        )
    )
    


    directors = User.objects.filter(
        is_staff=True,
        is_medical_staff=False,
        account_status="ACTIVE"
    )
    
    departments = MedicalDepartment.objects.all().order_by("department_name")
    
    hospital_uuid = request.GET.get("hospital")
    
    hospital = None
    
    if hospital_uuid:
        hospital = get_object_or_404(
            MedicalCenter,
            uuid=hospital_uuid
        )
    
    allocated_building_ids = MedicalCenter.objects.filter(
        hospital_building__isnull=False
    ).exclude(
        id=hospital.id if hospital else None
    ).values_list(
        "hospital_building_id",
        flat=True
    )

    buildings = Building.objects.filter(
        building_type="MEDICAL",
        status="ACTIVE"
    ).exclude(
        id__in=allocated_building_ids
    )
    
    for building in Building.objects.filter(building_type="MEDICAL"):
        print(
            building.building_name,
            "→ hospital_id:",
            building.hospital_id
        )
    context = {
        "medical_facilities_json": json.dumps(medical_facilities),
        "other_facilities_json": json.dumps(other_facilities),
        "hospital_uuid":hospital_uuid,
        "directors":directors,
        "departments": departments,
        "buildings":buildings
    }
    
    return render(
        request, "alan/create_hospital.html",context
    )


def add_hospital(request):
    
    post_data = request.POST.copy()
    
    hospital_uuid = post_data.get("hospital_uuid")
    
    # convert json fields
    
    try:
        
        if post_data.get("selected_facilities"):
            post_data["selected_facilities"] = json.loads(
                post_data.get("selected_facilities")
            )
        if post_data.get("selected_other_facilities"):
            post_data["selected_other_facilities"] = json.loads(
                post_data.get("selected_other_facilities")
            )
            
        if post_data.get("selected_departments"):
            post_data["selected_departments"] = json.loads(
                post_data.get("selected_departments")
            )
    
    except (json.JSONDecodeError, TypeError):
        
        return JsonResponse({
            "success": False,
            "message": "Invalid request data."
        }, status=400)
    
    # forms
    
    if hospital_uuid:

        hospital = get_object_or_404(
            MedicalCenter,
            uuid=hospital_uuid
        )

        
        old_selected_facilities = set(
            str(facility_id)
            for facility_id in (hospital.selected_facilities or [])
        )

        old_selected_other_facilities = set(
            str(facility_id)
            for facility_id in (hospital.selected_other_facilities or [])
        )

        medical_form = MedicalCenterForm(
            post_data,
            request.FILES,
            instance=hospital
        )

    else:

        medical_form = MedicalCenterForm(
            post_data,
            request.FILES
        )

    
    medical_valid = medical_form.is_valid()

    
    print("Medical Form Errors:", medical_form.errors)

    
    # validation erros
    
    if not (medical_valid):
        
        errors = {}
        
        errors.update(medical_form.errors)
        
        return JsonResponse({
            "success": False,
            "errors":errors
        }, status=400)
    
    # save hospital
    
    hospital = medical_form.save(commit=False)

    if not hospital_uuid:
        hospital.hospital_code = generate_hospital_code()

        # Initialize default working hours for new hospital
        hospital.working_hours = {
            "weekly_schedule": {
                "monday": {
                    "enabled": True,
                    "opening": "09:00",
                    "closing": "18:00"
                },
                "tuesday": {
                    "enabled": True,
                    "opening": "09:00",
                    "closing": "18:00"
                },
                "wednesday": {
                    "enabled": True,
                    "opening": "09:00",
                    "closing": "18:00"
                },
                "thursday": {
                    "enabled": True,
                    "opening": "09:00",
                    "closing": "18:00"
                },
                "friday": {
                    "enabled": True,
                    "opening": "09:00",
                    "closing": "18:00"
                },
                "saturday": {
                    "enabled": True,
                    "opening": "09:00",
                    "closing": "18:00"
                },
                "sunday": {
                    "enabled": True,
                    "opening": "09:00",
                    "closing": "18:00"
                }
            },
            "overrides": {}
        }

    hospital.save()
    
    # Save departments AFTER hospital.save()
    department_ids = post_data.get("selected_departments", [])

    hospital.departments.set(department_ids)
    
    # -----------------------------------------
    # REMOVE ALLOCATIONS FOR REMOVED FACILITIES
    # -----------------------------------------

    if hospital_uuid:

        new_selected_facilities = set(
            str(facility_id)
            for facility_id in (hospital.selected_facilities or [])
        )

        new_selected_other_facilities = set(
            str(facility_id)
            for facility_id in (hospital.selected_other_facilities or [])
        )

        old_all_facilities = (
            old_selected_facilities |
            old_selected_other_facilities
        )

        new_all_facilities = (
            new_selected_facilities |
            new_selected_other_facilities
        )

        removed_facilities = (
            old_all_facilities - new_all_facilities
        )

        if removed_facilities:

            FacilityRoomAllocation.objects.filter(
                medical_center=hospital,
                facility_id__in=removed_facilities
            ).delete()
    
    
    # save gallery images
    
    gallery_images = request.FILES.getlist("gallery")

    if gallery_images:

        if hospital_uuid:
            HospitalGallery.objects.filter(
                hospital=hospital
            ).delete()

        for image in gallery_images:

            HospitalGallery.objects.create(
                hospital=hospital,
                image=image
            )
    
    # success response
    
    return JsonResponse({
        "success": True,
        "message": (
            "Hospital updated successfully."
            if hospital_uuid
            else "Hospital created successfully."
        )
    }, status=200 if hospital_uuid else 201)
    
# HOSPITAL DETAIL VIEW FOR EDIT HOSPITAL FUNCTIONALITIES

def hospital_detail(request, uuid):

    hospital = get_object_or_404(
        MedicalCenter,
        uuid=uuid
    )

    statistics = HospitalStatistics.objects.filter(
        medical_center=hospital
    ).first()

    gallery = HospitalGallery.objects.filter(
        hospital=hospital
    )

    return JsonResponse({
        "success": True,
        "hospital": {

            "uuid": str(hospital.uuid),

            "hospital_name": hospital.hospital_name,
            "short_description": hospital.short_description,
            "about_hospital": hospital.about_hospital,

            "director_name": (
                hospital.director_name.full_name
                if hospital.director_name else ""
            ),

            "department_ids": list(
                hospital.departments.values_list("id", flat=True)
            ),

            "department_id": (
                hospital.department.id
                if hospital.department else ""
            ),

            "building": (
                hospital.hospital_building.building_name
                if hospital.hospital_building else ""
            ),

            "building_id": hospital.hospital_building_id or "",

            "hospital_status": hospital.hospital_status,
            "established_year": hospital.established_year,

            "hospital_location": hospital.hospital_location,
            "hospital_map": hospital.hospital_map,
            "hospital_phone": hospital.hospital_phone,
            "hospital_emgphone": hospital.hospital_emgphone,
            "hospital_email": hospital.hospital_email,

            "working_hours": hospital.working_hours,

            "selected_facilities": hospital.selected_facilities,
            "selected_other_facilities": hospital.selected_other_facilities,

            "hospital_banner": (
                hospital.hospital_banner.url
                if hospital.hospital_banner else ""
            ),

            "gallery": [
                img.image.url
                for img in gallery
            ],

            "statistics": {
                "total_beds":
                    statistics.total_beds if statistics else 0,

                "total_staff":
                    statistics.total_staff if statistics else 0,

                "total_rooms":
                    statistics.total_rooms if statistics else 0,

                "total_operation_theatres":
                    statistics.total_operation_theatres
                    if statistics else 0,

                "emergency_open":
                    statistics.emergency_open
                    if statistics else False,
            }
        }
    })

@require_POST
def save_working_hours(request, hospital_uuid):

    try:
        hospital = get_object_or_404(
            MedicalCenter,
            uuid=hospital_uuid
        )

        data = json.loads(request.body)

        weekly_schedule = data.get("weekly_schedule", {})
        overrides = data.get("overrides", {})

        if not isinstance(weekly_schedule, dict):
            return JsonResponse({
                "success": False,
                "message": "Invalid weekly schedule."
            }, status=400)

        if not isinstance(overrides, dict):
            return JsonResponse({
                "success": False,
                "message": "Invalid date overrides."
            }, status=400)

        hospital.working_hours = {
            "weekly_schedule": weekly_schedule,
            "overrides": overrides
        }

        hospital.save(
            update_fields=[
                "working_hours",
                "updated_at"
            ]
        )

        return JsonResponse({
            "success": True,
            "message": "Working hours saved successfully."
        })

    except json.JSONDecodeError:

        return JsonResponse({
            "success": False,
            "message": "Invalid JSON request."
        }, status=400)

    except Exception as e:

        print("Working hours save error:", e)

        return JsonResponse({
            "success": False,
            "message": "Unable to save working hours."
        }, status=500)

def own_hospital(request, hospital_uuid):

    hospital = get_object_or_404(
        MedicalCenter.objects.select_related("statistics"),
        uuid=hospital_uuid
    )
    
    if hospital.hospital_building:
        
        floors = hospital.hospital_building.floors.all().order_by("floor_number")
    
    else:
        floors = []
    
    allocated_room_ids = set(
        FacilityRoomAllocation.objects.filter(
            medical_center=hospital,
        ).values_list("room_id", flat=True)
    )
    
    purpose_room_ids = set(
        RoomPurposeAllocation.objects.filter(
            medical_center=hospital,
            is_full_crud=True
        ).values_list("room_id", flat=True)
    )
    
    unavailable_room_ids = (
        allocated_room_ids |
        purpose_room_ids
    )
    
    for floor in floors:
        floor.available_rooms = [
            room
            for room in floor.rooms.all()
            if room.id not in unavailable_room_ids
        ]
    
    gallery_images = HospitalGallery.objects.filter(
        hospital=hospital,
        is_full_crud=True
    ).order_by(
        "display_order",
        "-created_at"
    )
    
    medical_facilities = Facility.objects.filter(
        
        id__in = hospital.selected_facilities,
        facility_type = "medical",
        is_active = True
    )
    
    facility_allocations = {
        allocation.facility_id: allocation
        for allocation in FacilityRoomAllocation.objects.filter(
            medical_center=hospital
        ).select_related(
            "room__floor__building",
            "facility"
        )
    }
    
    other_facilities = Facility.objects.filter(
            
            id__in = hospital.selected_other_facilities,
            facility_type = "other",
            is_active = True
        )
    
    recent_activities = (
        FacilityMaintenance.objects
        .filter(
            hospital=hospital,
            is_active=True
        )
        .select_related("facility")
        .order_by("-updated_at")
    )

    paginator = Paginator(recent_activities, 4)

    page = request.GET.get("activity_page", 1)

    recent_activities = paginator.get_page(page)
    
    
    active_maintenance_ids = set(
        FacilityMaintenance.objects.filter(
            hospital=hospital,
            is_active=True
        )
        .exclude(status="completed")
        .values_list("facility_id", flat=True)
    )
    
    print("Active Maintenance IDs :", active_maintenance_ids)

    for facility in medical_facilities:
        facility.is_under_maintenance = (
            facility.id in active_maintenance_ids
        )
        
        facility.allocation = facility_allocations.get(
            facility.id
        )
    
    for facility in other_facilities:
        facility.is_under_maintenance = (
            facility.id in active_maintenance_ids
        )
        
    
    maintenance_data = []

    for maintenance in hospital.maintenances.filter(is_active=True).select_related("facility"):

        maintenance_data.append({
            "id": maintenance.id,
            "name": maintenance.facility.name,
            "icon": maintenance.facility.icon,
            "status": maintenance.status,
            "description": maintenance.description,
            "priority": maintenance.priority,
            "start": maintenance.start_date.strftime("%d %b %Y"),
            "eta": maintenance.expected_completion.strftime("%d %b %Y") if maintenance.expected_completion else "-",
            "eng": maintenance.assigned_engineer,
            "remarks": maintenance.remarks or "",
        })
    
    print(hospital.selected_other_facilities)
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        html = render_to_string(

            "alan/partials/maintenance_timeline.html",

            {
                "recent_activities": recent_activities
            },

            request=request

        )

        return JsonResponse({

            "success": True,

            "timeline_html": html,

        })

    return render(
        request,
        "alan/own_hospital.html",
        {
            "hospital": hospital,
            "medical_facilities": medical_facilities,
            "other_facilities": other_facilities,
            "maintenance_data": maintenance_data,
            "gallery_images":gallery_images,
            "recent_activities": recent_activities,
            "floors": floors,
            
        }
    )
    
@require_POST
def allocate_facility_room(request, hospital_uuid):

    data = json.loads(request.body)

    facility_id = data.get("facility_id")
    room_id = data.get("room_id")

    hospital = get_object_or_404(
        MedicalCenter,
        uuid=hospital_uuid
    )

    facility = get_object_or_404(
        Facility,
        id=facility_id
    )

    room = get_object_or_404(
        Room,
        id=room_id
    )
    
    purpose_allocation_exists = RoomPurposeAllocation.objects.filter(
        medical_center=hospital,
        room=room,
        is_full_crud=True
    ).exists()

    if purpose_allocation_exists:
        return JsonResponse({
            "success": False,
            "message": "This room is already assigned a room purpose and cannot be allocated to a facility."
        }, status=400)

    allocation_id = data.get("allocation_id")
    
    if allocation_id:
        
        allocation = get_object_or_404(
            FacilityRoomAllocation,
            id=allocation_id,
            medical_center=hospital
        )
        
        allocation.room = room
        allocation.save()
        
        return JsonResponse({
            "success": True,
            "message": "Facility allocation updated successfully.",
            "allocation_id": allocation.id
        })
    
    allocation = FacilityRoomAllocation.objects.create(
        medical_center=hospital,
        facility=facility,
        room=room
    )

    return JsonResponse({
        "success": True,
        "message": "Facility allocated successfully.",
        "allocation_id": allocation.id
    })


# FACILITY RELATED FUNCTIONS

@require_POST
def add_facility(request):
    
    form = FacilityForm(request.POST)
    

    if form.is_valid():
        facility = form.save()

        return JsonResponse({
            "success": True,
            "message": "Facility added successfully.",
            "facility": {
                "id": facility.id,
                "name": facility.name,
                "icon": facility.icon,
                "facility_type": facility.facility_type,
            }
        })

    return JsonResponse({
        "success": False,
        "errors": form.errors,
    }, status=400)
    
# EDIT FACILITY
@require_POST
def edit_facility(request,facility_id):
    
    try:
        facility = Facility.objects.get(id=facility_id)
    except Facility.DoesNotExist:
        
        return JsonResponse({
            
            "success": False,
            "message": "Facility not found."
        }, status=404)
        
    form = FacilityForm(
        request.POST,
        instance=facility
    )
    
    if form.is_valid():
        
        facility = form.save()
        
        return JsonResponse({
            
            "success": True,
            "message":"Facility updated successfully.",
            "facility": {
                
                "id":facility.id,
                "name":facility.name,
                "icon":facility.icon,
                "facility_type":facility.facility_type,
            }
        })
    return JsonResponse({
        
        "success": False,
        "errors": form.errors,
        
    }, status=400)

    # FACILITY MAINTENANCE FUNCTION
@require_POST
def add_facility_maintenance(request, hospital_uuid):
    


    hospital = get_object_or_404(
        MedicalCenter,
        uuid=hospital_uuid
    )
    


    facility_id = request.POST.get("facility_id")
    facility_type = request.POST.get("facility_type")
    maintenance_id = request.POST.get("maintenance_id")
    


    facility = get_object_or_404(
        Facility,
        id=facility_id,
        facility_type=facility_type,
        is_active=True,
    )
    


    if maintenance_id:
        
        maintenance = get_object_or_404(
            FacilityMaintenance,
            id=maintenance_id,
            hospital=hospital
        )
        
        form = FacilityMaintenanceForm(
            request.POST,instance=maintenance
        )
    
    else:
        form = FacilityMaintenanceForm(request.POST)

    if form.is_valid():

        maintenance = form.save(commit=False)

        maintenance.hospital = hospital
        maintenance.facility = facility

        if not maintenance_id:
            maintenance.created_by = request.user.username

        maintenance.save()

        return JsonResponse({
            "success": True,
            "message": (
                "Maintenance updated successfully."
                if maintenance_id
                else "Maintenance created successfully."
            ),
            "maintenance": {
            "id": maintenance.id,
            "facility_id": maintenance.facility.id,
            "facility_type": maintenance.facility.facility_type,
            "name": maintenance.facility.name,
            "icon": maintenance.facility.icon,
            "description": maintenance.description,
            "status": maintenance.status,
            "priority": maintenance.priority,
            "start": maintenance.start_date.strftime("%d %b %Y"),
            "eta": maintenance.expected_completion.strftime("%d %b %Y"),
            "eng": maintenance.assigned_engineer,
            "remarks": maintenance.remarks or "",
        }
        })

    return JsonResponse({
        "success": False,
        "errors": form.errors
    }, status=400)


def maintenance_detail(request, maintenance_id):

    maintenance = get_object_or_404(
        FacilityMaintenance.objects.select_related("facility"),
        id=maintenance_id,
        is_active=True,
    )

    return JsonResponse({
        "success": True,
        "maintenance": {
            "id": maintenance.id,
            "facility": maintenance.facility.name,
            "facility_id": maintenance.facility.id,
            "facility_type": maintenance.facility.facility_type,
            "title": maintenance.title,
            "description": maintenance.description,
            "status": maintenance.status,
            "priority": maintenance.priority,
            "start_date": maintenance.start_date.strftime("%d %b %Y"),
            "expected_completion": (
                maintenance.expected_completion.strftime("%d %b %Y")
                if maintenance.expected_completion
                else "-"
            ),
            "completed_date": (
                maintenance.completed_date.strftime("%d %b %Y")
                if maintenance.completed_date
                else "-"
            ),
            "engineer": maintenance.assigned_engineer,
            "contact": maintenance.contact_number,
            "remarks": maintenance.remarks or "-",
            "created_by": maintenance.created_by,
        }
    })
    
    
    
def complete_maintenance(request, maintenance_id):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        }, status=400)

    maintenance = get_object_or_404(
        FacilityMaintenance,
        id=maintenance_id,
        is_active=True,
    )

    maintenance.status = "completed"
    maintenance.completed_date = timezone.localdate()
    maintenance.is_full_crud = True
    maintenance.save()
    
    hospital = maintenance.hospital


    return JsonResponse({
        "success": True,
        "facility_id": maintenance.facility.id,
        "facility_type": maintenance.facility.facility_type,
        "maintenance_id": maintenance.id,
        "message": "Maintenance completed successfully.",
        
    })
    

@require_POST
@transaction.atomic
def add_hospital_gallery(request, hospital_uuid):

    hospital = get_object_or_404(
        MedicalCenter,
        uuid=hospital_uuid
    )

    caption = request.POST.get("caption", "").strip()

    image = request.FILES.get("images")

    if not image:
        return JsonResponse({
            "success": False,
            "message": "Please upload at least one image."
        }, status=400)
        
    display_order = HospitalGallery.objects.filter(
        hospital=hospital
    ).count()

    HospitalGallery.objects.create(

        hospital=hospital,

        image=image,

        caption=caption,

        alt_text=caption,

        display_order=display_order,

    )



    gallery_images = HospitalGallery.objects.filter(
        hospital=hospital,
        is_full_crud=True
    ).order_by(
        "display_order",
        "-created_at"
    )

    html = render_to_string(
        "alan/partials/hospital_gallery.html",
        {
            "gallery_images": gallery_images
        },
        request=request
    )

    return JsonResponse({
        "success": True,
        "message": "Gallery uploaded successfully.",
        "html": html,
    })
    

@require_POST
def delete_hospital_gallery(request, gallery_id):

    gallery = get_object_or_404(
        HospitalGallery,
        id=gallery_id,
        is_full_crud=True
    )

    hospital = gallery.hospital

    gallery.is_full_crud = False
    gallery.save()

    gallery_images = HospitalGallery.objects.filter(
        hospital=hospital,
        is_full_crud=True
    ).order_by(
        "display_order",
        "-created_at"
    )

    html = render_to_string(
        "alan/partials/hospital_gallery.html",
        {
            "gallery_images": gallery_images
        },
        request=request
    )

    return JsonResponse({

        "success": True,

        "message": "Gallery image deleted successfully.",

        "html": html,

    })


@require_POST
def save_room_purpose(request, hospital_uuid):

    hospital = get_object_or_404(
        MedicalCenter,
        uuid=hospital_uuid
    )

    room_ids = request.POST.getlist("room_ids[]")
    purpose = request.POST.get("purpose", "").strip()

    if not room_ids:
        return JsonResponse({
            "success": False,
            "message": "No rooms selected."
        }, status=400)

    if not purpose:
        return JsonResponse({
            "success": False,
            "message": "Please select a room purpose."
        }, status=400)

    # Validate purpose against model choices
    valid_purposes = dict(RoomPurposeAllocation.PURPOSE_CHOICES)

    if purpose not in valid_purposes:
        return JsonResponse({
            "success": False,
            "message": "Invalid room purpose."
        }, status=400)

    rooms = Room.objects.filter(
        id__in=room_ids
    )

    if rooms.count() != len(set(room_ids)):
        return JsonResponse({
            "success": False,
            "message": "One or more rooms are invalid."
        }, status=400)

    # Facility-assigned rooms must never receive a purpose
    facility_room_ids = set(
        FacilityRoomAllocation.objects.filter(
            medical_center=hospital,
            room_id__in=room_ids,
            is_full_crud=True
        ).values_list("room_id", flat=True)
    )

    if facility_room_ids:
        return JsonResponse({
            "success": False,
            "message": "One or more selected rooms are already assigned to a facility."
        }, status=400)

    updated_rooms = []

    for room_id in room_ids:

        allocation, created = (
            RoomPurposeAllocation.objects.update_or_create(
                medical_center=hospital,
                room_id=room_id,
                defaults={
                    "purpose": purpose,
                    "is_full_crud": True,
                }
            )
        )

        updated_rooms.append({
            "room_id": room_id,
            "purpose": allocation.purpose,
        })

    return JsonResponse({
        "success": True,
        "message": (
            "Room purpose saved successfully."
            if len(room_ids) == 1
            else f"{len(room_ids)} rooms updated successfully."
        ),
        "rooms": updated_rooms,
    })


def room_alloation(request, hospital_uuid):

    hospital = get_object_or_404(
        MedicalCenter,
        uuid=hospital_uuid
    )

    if hospital.hospital_building:

        floors = (
            hospital.hospital_building.floors
            .prefetch_related("rooms")
            .all()
            .order_by("floor_number")
        )

    else:
        floors = []

    # Facility allocation
    facility_allocations = {
        allocation.room_id: allocation
        for allocation in FacilityRoomAllocation.objects.filter(
            medical_center=hospital,
            is_full_crud=True
        ).select_related("facility")
    }

    # Purpose allocation
    purpose_allocations = {
        allocation.room_id: allocation
        for allocation in RoomPurposeAllocation.objects.filter(
            medical_center=hospital,
            is_full_crud=True
        )
    }
    
    print("PURPOSE ALLOCATIONS:", purpose_allocations)

    for floor in floors:

        for room in floor.rooms.all():

            # Facility flow
            facility_allocation = facility_allocations.get(room.id)

            room.facility_name = (
                facility_allocation.facility.name
                if facility_allocation
                else None
            )

            room.facility_allocated = bool(
                facility_allocation
            )

            # Purpose flow
            purpose_allocation = purpose_allocations.get(room.id)

            room.purpose = (
                purpose_allocation.purpose
                if purpose_allocation
                else None
            )
            
            print(
                "ROOM ID:", room.id,
                "| PURPOSE:", room.purpose
            )

    return render(
        request,
        "alan/room_allocation.html",
        {
            "hospital": hospital,
            "floors": floors,
        }
    )


@require_POST
def empty_room_purpose(request, hospital_uuid):

    hospital = get_object_or_404(
        MedicalCenter,
        uuid=hospital_uuid
    )

    room_id = request.POST.get("room_id")

    if not room_id:
        return JsonResponse({
            "success": False,
            "message": "Room is required."
        }, status=400)

    deleted_count, _ = RoomPurposeAllocation.objects.filter(
        medical_center=hospital,
        room_id=room_id
    ).delete()

    if not deleted_count:
        return JsonResponse({
            "success": False,
            "message": "No purpose assigned to this room."
        }, status=404)

    return JsonResponse({
        "success": True,
        "message": "Room purpose removed successfully.",
        "room_id": room_id,
    })
    



ALLOWED_SERVICE_TYPES = {
    "BLS",
    "ALS",
    "CCT",
    "Neonatal",
    "Bariatric",
    "Non-Emergency",
}

ALLOWED_STATUSES = {
    "available",
    "dispatched",
    "maintenance",
    "reserved",
    "outofservice",
}


@require_http_methods(["GET", "POST", "PATCH"])
def ambulance_services(request, hospital_uuid):

    hospital = get_object_or_404(
        MedicalCenter,
        uuid=hospital_uuid
    )

    # =========================================
    # GET
    # =========================================
    if request.method == "GET":

        return render(
            request,
            "alan/ambulance_services.html",
            {
                "hospital": hospital,
                "ambulances": hospital.ambulance_services or [],
            }
        )

    # =========================================
    # PATCH → ACTIVATE / DEACTIVATE
    # =========================================
    if request.method == "PATCH":

        try:
            data = json.loads(request.body.decode("utf-8"))

        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            return JsonResponse({
                "success": False,
                "message": "Invalid PATCH request data."
            }, status=400)

        ambulance_id = data.get("id")
        new_status = data.get("status")

        if not ambulance_id:
            return JsonResponse({
                "success": False,
                "message": "Ambulance ID is required."
            }, status=400)

        if not new_status:
            return JsonResponse({
                "success": False,
                "message": "Ambulance status is required."
            }, status=400)

        ambulances = hospital.ambulance_services or []

        for ambulance in ambulances:

            if str(ambulance.get("id")) == str(ambulance_id):

                ambulance["status"] = new_status

                hospital.ambulance_services = ambulances

                hospital.save(
                    update_fields=["ambulance_services"]
                )

                return JsonResponse({
                    "success": True,
                    "message": "Ambulance status updated successfully.",
                    "ambulance": ambulance,
                })

        return JsonResponse({
            "success": False,
            "message": "Ambulance not found."
        }, status=404)

    # =========================================
    # POST → ADD / EDIT
    # =========================================

    try:
        data = json.loads(request.body.decode("utf-8"))

    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return JsonResponse({
            "success": False,
            "message": "Invalid request data."
        }, status=400)

    ambulances = hospital.ambulance_services or []
    ambulance_id = data.get("id")

    # -----------------------------------------
    # EDIT
    # -----------------------------------------

    if ambulance_id:

        for index, ambulance in enumerate(ambulances):

            if str(ambulance.get("id")) == str(ambulance_id):

                updated_ambulance = {
                    "id": ambulance_id,
                    "unitNumber": data.get("unitNumber", "").strip(),
                    "plate": data.get("plate", "").strip(),
                    "vin": data.get("vin", "").strip().upper(),
                    "make": data.get("make", "").strip(),
                    "model": data.get("model", "").strip(),
                    "serviceType": data.get("serviceType", "").strip(),
                    "status": data.get("status", "available").strip(),
                    "nextMaint": data.get("nextMaint", "").strip(),
                    "dispatchPhone": data.get("dispatchPhone", "").strip(),
                    "altContact": data.get("altContact", "").strip(),
                    "notes": data.get("notes", "").strip(),
                }

                ambulances[index] = updated_ambulance

                hospital.ambulance_services = ambulances

                hospital.save(
                    update_fields=["ambulance_services"]
                )

                return JsonResponse({
                    "success": True,
                    "message": "Ambulance updated successfully.",
                    "ambulance": updated_ambulance,
                })

        return JsonResponse({
            "success": False,
            "message": "Ambulance not found."
        }, status=404)

    # -----------------------------------------
    # ADD
    # -----------------------------------------

    ambulance = {
        "id": str(uuid.uuid4()),
        "unitNumber": data.get("unitNumber", "").strip(),
        "plate": data.get("plate", "").strip(),
        "vin": data.get("vin", "").strip().upper(),
        "make": data.get("make", "").strip(),
        "model": data.get("model", "").strip(),
        "serviceType": data.get("serviceType", "").strip(),
        "status": data.get("status", "available").strip(),
        "nextMaint": data.get("nextMaint", "").strip(),
        "dispatchPhone": data.get("dispatchPhone", "").strip(),
        "altContact": data.get("altContact", "").strip(),
        "notes": data.get("notes", "").strip(),
    }

    ambulances.insert(0, ambulance)

    hospital.ambulance_services = ambulances

    hospital.save(
        update_fields=["ambulance_services"]
    )

    return JsonResponse({
        "success": True,
        "message": "Ambulance registered successfully.",
        "ambulance": ambulance,
    }, status=201)