# ******* Navina Code Starts ******* #

from django.db import models
from Admin.models import User
from Staff.models import StaffProfile
import uuid

from Admin.bela_admin.models import Building


# Library

class Library(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    SERVICE_CHOICES = [
        ("24_HOUR_SERVICE", "24-hour service"),
        ("AV_EQUIPMENT", "AV equipment for check out"),
        ("BOOK_SCANNER", "Book scanner"),
        ("CAFE_VENDING", "Café/Vending area"),
        ("COLOR_COPIER", "Color copier"),
        ("COLOR_LASER_PRINTER", "Color laser printer"),
        ("COMPUTER_LAB", "Computer lab"),
        ("GENDER_INCLUSIVE_RESTROOM", "Gender-inclusive restroom"),
        ("LACTATION_ROOM", "Lactation room"),
        ("LAPTOPS_CHECKOUT", "Laptops for check out"),
        ("LOCKERS", "Lockers"),
        ("MICROFORM_PRINTER", "Microform printer"),
        ("OPEN_RETURN", "Open return"),
        ("PHOTOCOPIER", "Photocopier"),
        ("PICKUP_BOOKS_APPOINTMENT", "Pickup books by appointment"),
        ("POSTER_PRINTING", "Poster printing"),
        ("REFLECTION_SPACE", "Reflection space"),
        ("RESERVABLE_STUDY_ROOMS", "Reservable study rooms"),
        ("SILENT_STUDY_SPACES", "Silent study spaces"),
    ]

    library_code = models.CharField(
        max_length=50,
        unique=True
    )

    library_name = models.CharField(
        max_length=255
    )

    building = models.ForeignKey(
    Building,
    on_delete=models.CASCADE,
    related_name='libraries',
    null=True,
    blank=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    website = models.URLField(
        blank=True,
        null=True
    )
    opening_hours = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )
    description = models.TextField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to='library/locations/',
        blank=True,
        null=True
    )

    # ==========================================
    # LIBRARY SERVICES
    # ==========================================

    services = models.JSONField(
        default=list,
        blank=True,
        help_text="Select the services available at this library."
    )

    # ==========================================
    # LIBRARY HOURS
    # ==========================================

    library_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Store opening and closing hours for each day."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=True)


    class Meta:
        db_table = "libraries"

    def __str__(self):
        return self.library_name
# library category

from django.db import models
from django.utils.text import slugify

class ResourceCategory(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True,)
    
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=120)
    # icon = models.CharField(max_length=100, blank=True, default='ti ti-folder')
    is_full_crud = models.BooleanField(default=False)
    
    # New fields
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=(
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
        ),
        default='ACTIVE'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True,        
        blank=True )
    updated_at = models.DateTimeField(auto_now=True, null=True,         
        blank=True  )
    
    class Meta:
        db_table = "resource_categories"
        ordering = ['title']
        verbose_name = "Resource Category"
        verbose_name_plural = "Resource Categories"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_book_count(self):
        return self.resources.count()

# Library Resource

class LibraryResource(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    RESOURCE_TYPES = (
        ("BOOK", "Book"),
        ("ARTICLE", "Article"),
        ("JOURNAL", "Journal"),
        ("THESIS", "Thesis"),
        ("EBOOK", "eBook"),
        ("VIDEO", "Video"),
    )
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name="resources"
    )
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.CASCADE,
        related_name="resources",
        null=True,
        blank=True
    )
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPES
    )

    title = models.CharField(max_length=255)
    
    cover_image = models.ImageField(
        upload_to="library/covers/",
        blank=True,
        null=True
    )

    isbn_issn = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    author = models.CharField(max_length=255)

    publisher = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    publication_year = models.PositiveIntegerField(
        blank=True,
        null=True
    )
    edition = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    language = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    is_full_crud = models.BooleanField(default=True)


    total_copies = models.PositiveIntegerField(default=0)

    available_copies = models.PositiveIntegerField(default=0)

    shelf_location = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    class Meta:
        db_table = "library_resources"

    def __str__(self):
        return self.title
    

# Library Resource Copy 

class ResourceCopy(models.Model):

    STATUS_CHOICES = (
        ("AVAILABLE", "Available"),
        ("CHECKED_OUT", "Checked Out"),
        ("RESERVED", "Reserved"),
        ("LOST", "Lost"),
        ("DAMAGED", "Damaged"),
    )
    resource = models.ForeignKey(
        LibraryResource,
        on_delete=models.CASCADE,
        related_name="copies"
    )
    barcode = models.CharField(
        max_length=100,
        unique=True
    )

    acquisition_date = models.DateField()

    condition = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE"
    )

    is_full_crud = models.BooleanField(default=True)


    class Meta:
        db_table = "resource_copies"

    def __str__(self):
        return self.barcode
    

# Library User 

class LibraryUser(models.Model):

    USER_TYPES = (
        ("STUDENT", "Student"),
        ("FACULTY", "Faculty"),
        ("STAFF", "Staff"),
        ("ALUMNI", "Alumni"),
        ("GUEST", "Guest"),
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="library_profile"
    )
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES
    )

    membership_date = models.DateField()

    membership_expiry = models.DateField(
        blank=True,
        null=True
    )

    borrowing_limit = models.PositiveIntegerField(
        default=5
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_full_crud = models.BooleanField(default=True)


    class Meta:
        db_table = "library_users"

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"


# Borrow Transactions 

class BorrowTransaction(models.Model):

    STATUS_CHOICES = (
        ("ISSUED", "Issued"),
        ("RETURNED", "Returned"),
        ("OVERDUE", "Overdue"),
        ("LOST", "Lost"),
    )
    copy = models.ForeignKey(
        ResourceCopy,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    library_user = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name="borrow_transactions"
    )
    # new field added
    borrow_request = models.OneToOneField(
        "BorrowRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_transaction",
    )

    issue_date = models.DateField()

    due_date = models.DateField()

    return_date = models.DateField(
        blank=True,
        null=True
    )
    # ============================================
    # RENEWAL DETAILS
    # ============================================

    renewal_count = models.PositiveIntegerField(
        default=0
    )

    last_renewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    renewal_requested = models.BooleanField(
        default=False
    )

    renewal_requested_at = models.DateTimeField(
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ISSUED"
    )

    is_full_crud = models.BooleanField(default=True)


    class Meta:
        db_table = "borrow_transactions"

    def __str__(self):
        return (
            f"{self.library_user.user.username} | "
            f"{self.copy.resource.title}"
    )

# Reservation 

# class Reservation(models.Model):

#     STATUS_CHOICES = (
#         ("PENDING", "Pending"),
#         ("FULFILLED", "Fulfilled"),
#         ("CANCELLED", "Cancelled"),
#         ("EXPIRED", "Expired"),
#     )
#     resource = models.ForeignKey(
#         LibraryResource,
#         on_delete=models.CASCADE
#     )
#     library_user = models.ForeignKey(
#         LibraryUser,
#         on_delete=models.CASCADE
#     )

#     is_full_crud = models.BooleanField(default=True)

#     reservation_date = models.DateField()

#     expiry_date = models.DateField()

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="PENDING"
#     )

#     class Meta:
#         db_table = "library_reservations"

# # Fine 

# class Fine(models.Model):

#     transaction = models.OneToOneField(
#         BorrowTransaction,
#         on_delete=models.CASCADE,
#         related_name="fine"
#     )
#     amount = models.DecimalField(
#         max_digits=10,
#         decimal_places=2
#     )

#     reason = models.TextField()

#     assessed_date = models.DateField()

#     paid_date = models.DateField(
#         blank=True,
#         null=True
#     )

#     is_full_crud = models.BooleanField(default=True)

#     payment_status = models.BooleanField(
#         default=False
#     )

#     class Meta:
#         db_table = "library_fines"

from django.db import models
from django.conf import settings


class Fine(models.Model):

    PAYMENT_STATUS = [
        ("UNPAID", "Unpaid"),
        ("PAID", "Paid"),
    ]

    PAYMENT_METHODS = [
        ("CASH", "Cash"),
        ("UPI", "UPI"),
        ("CARD", "Card"),
        ("BANK", "Bank Transfer"),
    ]

    transaction = models.OneToOneField(
        "BorrowTransaction",
        on_delete=models.CASCADE,
        related_name="fine"
    )

    fine_per_day = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5.00
    )

    overdue_days = models.PositiveIntegerField(default=0)

    fine_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00
    )

    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS,
        default="UNPAID"
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        blank=True,
        null=True
    )

    amount_received = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )

    # Payment transaction generated after payment
    payment_transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    # Optional external payment reference
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )

    paid_date = models.DateTimeField(
        blank=True,
        null=True
    )

    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collected_fines"
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fine"
        verbose_name_plural = "Fines"

    def __str__(self):
       return (
           f"{self.transaction.library_user.user.username} | "
           f"${self.fine_amount}"
    )
from django.db import models


class FineAppeal(models.Model):

    APPEAL_REASON_CHOICES = [

        ("FIRST_APPEAL", "First Time Appeal"),

        ("MEDICAL", "Medical Emergency"),

        ("OTHER", "Other Circumstances"),

        ("QUESTION", "Question About My Fine"),

    ]

    STATUS_CHOICES = [

        ("SUBMITTED", "Submitted"),

        ("UNDER_REVIEW", "Under Review"),

        ("APPROVED", "Approved"),

        ("REJECTED", "Rejected"),

    ]

    uwid = models.CharField(max_length=10)

    applicant_name = models.CharField(max_length=150)

    applicant_phone = models.CharField(max_length=20)

    applicant_email = models.EmailField()

    appeal_reason = models.CharField(
        max_length=30,
        choices=APPEAL_REASON_CHOICES,
    )

    explanation_statement = models.TextField()

    consent = models.BooleanField(default=False)

    appeal_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUBMITTED",
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    admin_notes = models.TextField(
        blank=True,
        null=True,
    )

    is_full_crud = models.BooleanField(default=True)

    class Meta:

        db_table = "library_fine_appeals"

        ordering = ["-submitted_at"]

    def __str__(self):

        return f"{self.uwid} - {self.applicant_name}"



# DigitalResource

class DigitalResource(models.Model):

    resource = models.OneToOneField(
        LibraryResource,
        on_delete=models.CASCADE,
        related_name="digital_resource"
    )

    access_url = models.URLField()

    license_type = models.CharField(
        max_length=100
    )

    vendor = models.CharField(
        max_length=255
    )

    access_start_date = models.DateField()

    access_end_date = models.DateField(
        blank=True,
        null=True
    )

    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "digital_resources"

    def __str__(self):
        return self.resource.title
    
# StudyRoom
# from Admin.bela_admin.models import Floor, Room
# class StudyRoom(models.Model):

#     STATUS_CHOICES = (
#         ("AVAILABLE", "Available"),
#         ("MAINTENANCE", "Maintenance"),
#         ("UNAVAILABLE", "Unavailable"),
#     )

#     library = models.ForeignKey(
#         Library,
#         on_delete=models.CASCADE,
#         related_name="study_rooms"
#     )

#     room = models.OneToOneField(
#         Room,
#         on_delete=models.CASCADE,
#         related_name="study_room"
#     )

#     equipment = models.TextField(
#         blank=True,
#         null=True
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="AVAILABLE"
#     )

#     is_full_crud = models.BooleanField(
#         default=False
#     )

#     class Meta:
#         db_table = "study_rooms"

#     def __str__(self):
#         return f"{self.room.room_number} - {self.room.room_name}"

# # StudyRoom Booking

# class StudyRoomBooking(models.Model):

#     STATUS_CHOICES = (
#         ("BOOKED", "Booked"),
#         ("COMPLETED", "Completed"),
#         ("CANCELLED", "Cancelled"),
#     )
#     room = models.ForeignKey(
#         StudyRoom,
#         on_delete=models.CASCADE
#     )
#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE
#     )

#     booking_date = models.DateField()

#     start_time = models.TimeField()

#     end_time = models.TimeField()

#     is_full_crud = models.BooleanField(default=False)


#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="BOOKED"
#     )

#     class Meta:
#         db_table = "study_room_bookings"




# Library Event

class LibraryEvent(models.Model):

    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name="events"
    )

    event_name = models.CharField(
        max_length=255
    )

    event_type = models.CharField(
        max_length=100
    )

    event_date = models.DateField()

    organizer = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True,
        null=True
    )
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "library_events"

    def __str__(self):
        return self.event_name

# New models-navina

# # ===============================
# # Find Cards
# # ===============================

# class FindCard(models.Model):
#     title = models.CharField(
#         max_length=100
#     )

#     description = models.TextField()

#     image = models.ImageField(
#         upload_to='library/find/cards/'
#     )

#     icon = models.CharField(
#         max_length=100,
#         help_text="Example: fa-regular fa-newspaper"
#     )

#     button_text = models.CharField(
#         max_length=100,
#         default="Explore"
#     )

#     button_link = models.URLField(
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     active = models.BooleanField(
#         default=True
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "library_find_cards"
#         ordering = ['display_order']

#     def __str__(self):
#         return self.title


# # ===============================
# # Resources By Type
# # ===============================

# class ResourceTypeItem(models.Model):
#     title = models.CharField(
#         max_length=100
#     )

#     icon = models.CharField(
#         max_length=100,
#         default='fa-solid fa-book-open'
#     )

#     link = models.URLField(
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     active = models.BooleanField(
#         default=True
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "library_resource_type_items"
#         ordering = ['display_order']

#     def __str__(self):
#         return self.title


# # ===============================
# # Resources By Subject
# # ===============================

# class ResourceSubject(models.Model):
#     title = models.CharField(
#         max_length=100
#     )

#     description = models.TextField()

#     icon = models.CharField(
#         max_length=100,
#         default='fa-solid fa-magnifying-glass'
#     )

#     link = models.URLField(
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     active = models.BooleanField(
#         default=True
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "library_resource_subjects"
#         ordering = ['display_order']

#     def __str__(self):
#         return self.title

# LibraryAdditionalResource

# class LibraryAdditionalResource(models.Model):
#     PAGE_CHOICES = (
#         ('LOCATIONS', 'Locations'),
#         ('BORROW', 'Borrow & Request'),
#         ('GIVING', 'Giving'),
#     )
 
#     page_type = models.CharField(
#         max_length=20,
#         choices=PAGE_CHOICES,
#         default='LOCATIONS'
#     )
#     title = models.CharField(max_length=100)

#     icon = models.CharField(
#         max_length=100,
#         default='fa-regular fa-map'
#     )

#     link = models.CharField(
#         max_length=255,
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(default=0)

#     active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "library_additional_resources"
#         ordering = ['display_order']

#     def __str__(self):
#         return self.title

# LibraryHours
# class LibraryHours(models.Model):
#     library = models.ForeignKey(
#         Library,
#         on_delete=models.CASCADE,
#         related_name='hours'
#     )

#     day = models.CharField(max_length=50)

#     opening_time = models.TimeField(
#         blank=True,
#         null=True
#     )

#     closing_time = models.TimeField(
#         blank=True,
#         null=True
#     )

#     is_closed = models.BooleanField(
#         default=False
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "library_hours"
#         ordering = ['display_order']

#     def __str__(self):
#         return f"{self.library.library_name} - {self.day}"
    
# LibraryAccessInfo

# class LibraryAccessInfo(models.Model):
#     library = models.ForeignKey(
#         Library,
#         on_delete=models.CASCADE,
#         related_name='access_infos'
#     )

#     title = models.CharField(max_length=150)

#     link = models.CharField(
#         max_length=255,
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "library_access_info"
#         ordering = ['display_order']

#     def __str__(self):
#         return self.title
    
# LibraryService

# class LibraryService(models.Model):
#     library = models.ForeignKey(
#         Library,
#         on_delete=models.CASCADE,
#         related_name='services'
#     )

#     service_name = models.CharField(
#         max_length=150
#     )

#     active = models.BooleanField(
#         default=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "library_services"

#     def __str__(self):
#         return self.service_name
    
# # Borrowcard

# class BorrowCard(models.Model):
#     title = models.CharField(
#         max_length=200
#     )

#     description = models.TextField()

#     image = models.ImageField(
#         upload_to='library/borrow/cards/'
#     )

#     icon = models.CharField(
#         max_length=100,
#         help_text="Example: fa-solid fa-users"
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     active = models.BooleanField(
#         default=True
#     )

#     is_full_crud = models.BooleanField(
#         default=False
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     class Meta:
#         db_table = "library_borrow_cards"
#         ordering = ['display_order']

#     def __str__(self):
#         return self.title

# # BorrowcardLink  

# class BorrowCardLink(models.Model):
#     card = models.ForeignKey(
#         BorrowCard,
#         on_delete=models.CASCADE,
#         related_name='links'
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     icon = models.CharField(
#         max_length=100,
#         default='fa-regular fa-map'
#     )

#     link = models.CharField(
#         max_length=255,
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     active = models.BooleanField(
#         default=True
#     )

#     is_full_crud = models.BooleanField(
#         default=False
#     )

#     class Meta:
#         db_table = "library_borrow_card_links"
#         ordering = ['display_order']

#     def __str__(self):
#         return self.title
    
# class GivingPage(models.Model):
#     banner_image = models.ImageField(
#         upload_to='library/giving/'
#     )
 
#     banner_title = models.CharField(
#         max_length=200,
#         default='Support the Libraries'
#     )
 
#     banner_subtitle = models.CharField(
#         max_length=255,
#         blank=True,
#         null=True
#     )
 
#     main_heading = models.TextField()
 
#     description = models.TextField()
 
#     quote = models.CharField(
#         max_length=255
#     )
 
#     button_text = models.CharField(
#         max_length=100,
#         default='Give to the Libraries'
#     )
 
#     button_link = models.URLField(
#         blank=True,
#         null=True
#     )
 
#     active = models.BooleanField(
#         default=True
#     )
 
#     is_full_crud = models.BooleanField(
#         default=False
#     )
 
#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )
 
#     updated_at = models.DateTimeField(
#         auto_now=True
#     )
 
#     class Meta:
#         db_table = 'library_giving_page'
 
#     def __str__(self):
#         return self.banner_title


# ============================================
# Contact Us Page
# ============================================
from django.conf import settings
class ContactRequest(models.Model):

    AFFILIATION_CHOICES = (

        ("FACULTY", "Faculty, Staff or Student"),

        ("NON_AFFILIATED", "Not affiliated with University"),

        ("NOT_SURE", "Not Sure"),

    )

    STATUS_CHOICES = (

        ("NEW", "New"),

        ("READ", "Read"),

        ("REPLIED", "Replied"),

    )

    name = models.CharField(
        max_length=150
    )

    email = models.EmailField()

    affiliation = models.CharField(
        max_length=30,
        choices=AFFILIATION_CHOICES
    )

    message = models.TextField()

    accepted_policy = models.BooleanField(
        default=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="NEW"
    )

    admin_notes = models.TextField(
        blank=True,
        null=True
    )

    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="contact_replies"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_active = models.BooleanField(
        default=True
    )

    is_full_crud = models.BooleanField(
        default=False
    )

    class Meta:

        db_table = "library_contact_requests"

        ordering = ["-created_at"]

        verbose_name = "Contact Request"

        verbose_name_plural = "Contact Requests"

    def __str__(self):

        return f"{self.name} - {self.email}"


class RequestPurchase(models.Model):

    email = models.EmailField(
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_full_crud = models.BooleanField(
            default=False
    )

    class Meta:

        verbose_name = "Request Purchase"

        verbose_name_plural = "Request Purchases"

        ordering = ["-created_at"]

    def __str__(self):

        return self.email

from django.db import models


class ShelvingFacilityRequest(models.Model):

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    email = models.EmailField(blank=True)

    phone = models.CharField(max_length=20, blank=True)

    street_address = models.CharField(max_length=255, blank=True)

    city = models.CharField(max_length=100, blank=True)

    state = models.CharField(max_length=100, blank=True)

    zip_code = models.CharField(max_length=20, blank=True)

    country = models.CharField(max_length=100, blank=True)

    viewing_library = models.ForeignKey(
        "Library",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shelving_requests"
    )

    title = models.CharField(max_length=255)

    call_number = models.CharField(
        max_length=100,
        blank=True
    )

    shelving_number = models.CharField(
        max_length=100,
        blank=True
    )

    volume = models.CharField(
        max_length=100,
        blank=True
    )

    journal_date = models.CharField(
        max_length=100,
        blank=True
    )

    other_information = models.TextField(
        blank=True
    )

    consent = models.BooleanField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_full_crud = models.BooleanField(
            default=False
    )

    class Meta:

        ordering = ["-created_at"]

        verbose_name = "Shelving Facility Request"

        verbose_name_plural = "Shelving Facility Requests"

    def __str__(self):

        return f"{self.first_name} {self.last_name}"

# ******* Navina code ends ******* #


# *********************************************rupa code start***************************************


from django.db import models
from django.utils.text import slugify

# Research Support page

# class ResearchSupportCategory(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     slug = models.SlugField(
#         max_length=220,
#         unique=True,
#         blank=True
#     )

#     description = models.TextField(
#         blank=True,
#         null=True
#     )

#     intro = models.TextField(
#     blank=True,
#     null=True
#     )

#     image = models.ImageField(
#         upload_to="research_support/categories/",
#         blank=True,
#         null=True
#     )

#     url = models.CharField(
#         max_length=300,
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "research_support_categories"
#         ordering = ["display_order", "title"]

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title


# # Research Support Category Link


# class ResearchSupportCategoryLink(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     category = models.ForeignKey(
#         ResearchSupportCategory,
#         on_delete=models.CASCADE,
#         related_name="links"
#     )

#     link_text = models.CharField(
#         max_length=200
#     )
#     data_management_page = models.ForeignKey(
#         "DataManagementPlan",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     grants_scholarship_page = models.ForeignKey(
#         "GrantsScholarshipPage",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#     evidence_synthesis_page=models.ForeignKey(
#     "EvidenceSynthesisPage",
#     on_delete=models.SET_NULL,
#     null=True,
#     blank=True
#     )

#     link_url = models.CharField(
#         max_length=300,
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=False)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "research_support_category_links"
#         ordering = ["display_order"]

#     def __str__(self):
#         return f"{self.category.title} -> {self.link_text}"


# Research Support Featured Resource

# class ResearchSupportFeaturedResource(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     url = models.CharField(
#         max_length=300
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=False)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "research_support_featured_resources"
#         ordering = ["display_order", "title"]

#     def __str__(self):
#         return self.title
    

# class ResearchSupportSection(models.Model):

#     is_full_crud = models.BooleanField(default=True)

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     category = models.ForeignKey(
#         ResearchSupportCategory,
#         on_delete=models.CASCADE,
#         related_name="sections"
#     )

#     title = models.CharField(max_length=200)

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "research_support_sections"
#         ordering = ["display_order", "title"]

#     def __str__(self):
#         return f"{self.category.title} - {self.title}"
    
# class ResearchSupportSectionItem(models.Model):

#     is_full_crud = models.BooleanField(default=True)

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     section = models.ForeignKey(
#         ResearchSupportSection,
#         on_delete=models.CASCADE,
#         related_name="items"
#     )

#     title = models.CharField(max_length=250)

#     url = models.CharField(
#         max_length=300,
#         blank=True,
#         null=True
#     )

#     description = models.TextField(
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "research_support_section_items"
#         ordering = ["display_order", "title"]

#     def __str__(self):
#         return self.title
    

    

# instruction support


from django.db import models
from django.utils.text import slugify


# ==========================================================
# Instruction Support Category
# ==========================================================

# class InstructionSupportCategory(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     slug = models.SlugField(
#         max_length=220,
#         unique=True,
#         blank=True
#     )

#     description = models.TextField(
#         blank=True,
#         null=True
#     )

   
#     image = models.ImageField(
#         upload_to="instruction_support/categories/",
#         blank=True,
#         null=True
#     )

#     icon = models.CharField(
#         max_length=100,
#         default="fa-solid fa-users"
#     )

    
#     button_text = models.CharField(
#         max_length=100,
#         default="Learn More"
#     )

#     button_url = models.CharField(
#         max_length=300,
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     class Meta:
#         db_table = "instruction_support_categories"
#         ordering = ["display_order", "title"]

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title


# ==========================================================
# Links inside each Category
# ==========================================================

# class InstructionSupportCategoryLink(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     category = models.ForeignKey(
#         InstructionSupportCategory,
#         on_delete=models.CASCADE,
#         related_name="links"
#     )

#     link_text = models.CharField(
#         max_length=200
#     )

#     link_url = models.CharField(
#         max_length=300
#     )

#     # Optional icon for each link
#     icon = models.CharField(
#         max_length=100,
#         default="fa-regular fa-calendar-plus"
#     )

#     open_in_new_tab = models.BooleanField(
#         default=False
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "instruction_support_category_links"
#         ordering = ["display_order"]

#     def __str__(self):
#         return f"{self.category.title} → {self.link_text}"


# # ==========================================================
# # Sidebar Links
# # ==========================================================

# class InstructionSupportSidebarLink(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     url = models.CharField(
#         max_length=300
#     )

#     icon = models.CharField(
#         max_length=100,
#         default="fa-regular fa-calendar"
#     )

#     open_in_new_tab = models.BooleanField(
#         default=False
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "instruction_support_sidebar_links"
#         ordering = ["display_order", "title"]

#     def __str__(self):
#         return self.title


# ==========================================================
# Instruction Request Form
# ==========================================================


# "Request Library Instruction" form.
# from django.db import models

# from Staff.models import StaffProfile
# from Library.models import Library, StudyRoom
# from Admin.bela_admin.models import Department, Course


# class InstructionRequest(models.Model):

#     STATUS_CHOICES = (
#         ("SUBMITTED", "Submitted"),
#         ("UNDER_REVIEW", "Under Review"),
#         ("CONFIRMED", "Confirmed"),
#         ("COMPLETED", "Completed"),
#         ("CANCELLED", "Cancelled"),
#     )

#     DELIVERY_CHOICES = (
#         ("IN_PERSON", "In-person Library Instruction"),
#         ("ONLINE", "Online Library Instruction"),
#         ("RESEARCH_GUIDE", "Online Research Guide"),
#         ("CANVAS", "Canvas Library Services"),
#     )

#     # ==========================
#     # Instructor Information
#     # ==========================

#     instructor_name = models.CharField(
#         max_length=200
#     )

#     instructor_email = models.EmailField()

#     phone = models.CharField(
#         max_length=20,
#         blank=True,
#         null=True
#     )

#     # ==========================
#     # Course Information
#     # ==========================

#     department = models.ForeignKey(
#     Department,
#     on_delete=models.SET_NULL,
#     null=True,
#     blank=True,
#     related_name="instruction_requests"
#     )

#     course = models.ForeignKey(
#         Course,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="instruction_requests"
#     )

#     number_of_students = models.PositiveIntegerField()

#     # ==========================
#     # Instruction Details
#     # ==========================

#     delivery_mode = models.CharField(
#         max_length=30,
#         choices=DELIVERY_CHOICES,
#         blank=False
#     )

#     instruction_support = models.TextField(
#         help_text="Describe the instructional support you would like."
#     )

#     # ==========================
#     # Library Preference
#     # ==========================

#     preferred_library = models.ForeignKey(
#         Library,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="instruction_requests"
#     )

#     preferred_room = models.ForeignKey(
#         StudyRoom,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="instruction_requests"
#     )

#     preferred_date = models.DateField()

#     additional_notes = models.TextField(
#         blank=True,
#         null=True
#     )

#     # ==========================
#     # Privacy Consent
#     # ==========================

#     consent = models.BooleanField(
#         default=False
#     )

#     # ==========================
#     # Admin Section
#     # ==========================

#     assigned_librarian = models.ForeignKey(
#         StaffProfile,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="assigned_instruction_requests"
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="SUBMITTED"
#     )

#     admin_notes = models.TextField(
#         blank=True,
#         null=True
#     )

#     # ==========================
#     # Timestamps
#     # ==========================

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "instruction_requests"
#         ordering = ["-created_at"]
#         verbose_name = "Instruction Request"
#         verbose_name_plural = "Instruction Requests"

#     def __str__(self):
#         return f"{self.course} - {self.instructor_name}"
    
from django.db import models

from Staff.models import StaffProfile
from Library.models import Library
from Admin.bela_admin.models import Department, Course


class InstructionRequest(models.Model):

    STATUS_CHOICES = (
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("CONFIRMED", "Confirmed"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    )

    # ==========================
    # Instruction Mode Choices
    # ==========================

    IN_PERSON = "IN_PERSON"
    ONLINE = "ONLINE"
    RESEARCH_GUIDE = "RESEARCH_GUIDE"
    CANVAS = "CANVAS"

    INSTRUCTION_MODE_CHOICES = (
        (IN_PERSON, "In-person Library Instruction"),
        (ONLINE, "Online Library Instruction"),
        (RESEARCH_GUIDE, "Online Research Guide"),
        (CANVAS, "Canvas Library Services"),
    )

    # ==========================
    # Instructor Information
    # ==========================

    instructor_name = models.CharField(
        max_length=200
    )

    instructor_email = models.EmailField()

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    # ==========================
    # Course Information
    # ==========================

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instruction_requests"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instruction_requests"
    )

    number_of_students = models.PositiveIntegerField()

    # ==========================
    # Instruction Details
    # ==========================

    instruction_modes = models.JSONField(
        default=list,
        blank=True,
        help_text="Select one or more instruction modes."
    )

    instruction_support = models.TextField(
        help_text="Describe the instructional support you would like."
    )

    # ==========================
    # Library Preference
    # ==========================

    preferred_library = models.ForeignKey(
        Library,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instruction_requests"
    )

    # Keep only if your project requires room selection
    # preferred_room = models.ForeignKey(
    #     StudyRoom,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="instruction_requests"
    # )

    preferred_schedule = models.TextField(
        blank=True,
        null=True,
        help_text="Provide three preferred dates/times or an assignment due date."
    )

    additional_notes = models.TextField(
        blank=True,
        null=True
    )

    # ==========================
    # Privacy Consent
    # ==========================

    consent = models.BooleanField(
        default=False
    )

    # ==========================
    # Admin Section
    # ==========================

    assigned_librarian = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_instruction_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUBMITTED"
    )

    admin_notes = models.TextField(
        blank=True,
        null=True
    )

    # ==========================
    # Timestamps
    # ==========================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "instruction_requests"
        ordering = ["-created_at"]
        verbose_name = "Instruction Request"
        verbose_name_plural = "Instruction Requests"

    def __str__(self):
        course = self.course if self.course else "No Course"
        return f"{course} - {self.instructor_name}"

# office of the dean

from django.db import models


class OfficeOfDeanMember(models.Model):
    staff = models.ForeignKey(
        "LibraryStaff",
        on_delete=models.CASCADE,
        related_name="office_of_dean_members"
    )

    designation = models.CharField(max_length=200)

    display_order = models.PositiveIntegerField(default=0)

    show_about_link = models.BooleanField(default=False)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order"]

# people models

from Staff.models import StaffProfile
from Library.models import Library  # adjust import path to match your app label
from Admin.bela_admin.models import Department


# Department

# updated department member

class DepartmentMember(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    department = models.ForeignKey(
    "bela_admin.Department",
    on_delete=models.CASCADE,
    related_name="library_members"
    )

    staff = models.ForeignKey(
        "LibraryStaff",
        on_delete=models.CASCADE,
        related_name="department_memberships"
    )

    job_title = models.CharField(max_length=200)

    display_order = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    is_full_crud = models.BooleanField(default=False)

# Subject
# Covers the Subject Librarians page, e.g. "Physical Sciences &
# Engineering", "International and Area Studies". Some subjects have
# a shared team inbox in addition to individual librarians.

class Subject(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    name = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True
    )

    team_email = models.EmailField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "subjects"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Subject Librarian
# Through-table linking a StaffProfile to a Subject, since one
# librarian can cover multiple subjects and one subject can list
# multiple librarians. Points at your existing StaffProfile rather
# than a duplicate Person model.

class SubjectLibrarian(models.Model):

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="librarians"
    )
    # updated department
    department = models.ForeignKey(
    "bela_admin.Department",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="library_subject_librarians"
    )

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="subject_assignments"
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "subject_librarians"
        ordering = ["display_order"]
        unique_together = ("subject", "staff")

    def __str__(self):
        return f"{self.subject.name} -> {self.staff}"

# people page
from django.db import models
 
 
class PeoplePageCard(models.Model):
 
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )
 
    title = models.CharField(
        max_length=200
    )
 
    description = models.TextField()
 
    image = models.ImageField(
        upload_to="people/cards/"
    )
 
    icon = models.CharField(
        max_length=100,
        default="fa-folder-open",
        help_text="Example: fa-folder-open, fa-user-group, fa-building-columns"
    )
 
    url = models.CharField(
        max_length=300,
        help_text="Example: /people/directory/"
    )
 
    display_order = models.PositiveIntegerField(
        default=0
    )
 
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )
 
    created_at = models.DateTimeField(
        auto_now_add=True
    )
 
    updated_at = models.DateTimeField(
        auto_now=True
    )
 
    is_full_crud = models.BooleanField(default=False)
 
    class Meta:
        db_table = "people_page_cards"
        ordering = ["display_order"]
 
    def __str__(self):
        return self.title


    
# about page
# About Category
# Covers the About landing hub cards: Collections, Diversity,
# Employment, News, Leadership, Visitor Services. Same shape as
# ResearchSupportCategory since both pages are card-based hubs.

# class AboutCategory(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     slug = models.SlugField(
#         max_length=220,
#         unique=True,
#         blank=True
#     )

#     description = models.TextField(
#         blank=True,
#         null=True
#     )

#     image = models.ImageField(
#         upload_to="about/categories/",
#         blank=True,
#         null=True
#     )

#     url = models.CharField(
#         max_length=300,
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "about_categories"
#         ordering = ["display_order", "title"]

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title


# About Category Link

# class AboutCategoryLink(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     category = models.ForeignKey(
#         AboutCategory,
#         on_delete=models.CASCADE,
#         related_name="links"
#     )

#     link_text = models.CharField(
#         max_length=200
#     )

#     link_url = models.CharField(
#         max_length=300
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "about_category_links"
#         ordering = ["display_order"]

#     def __str__(self):
#         return f"{self.category.title} -> {self.link_text}"



# class AboutSidebarLink(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     url = models.CharField(
#         max_length=300
#     )

#     icon = models.CharField(
#         max_length=100,
#         default="fa-regular fa-calendar",
#         help_text="Example: fa-regular fa-calendar, fa-regular fa-map"
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "about_sidebar_links"
#         ordering = ["display_order", "title"]

#     def __str__(self):
#         return self.title


# Collection page

# class CollectionSection(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(max_length=200)

#     slug = models.SlugField(
#         unique=True,
#         blank=True,
#     )

#     description = models.TextField()

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE",
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def save(self,*args,**kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args,**kwargs)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         ordering=["display_order"]

#     def __str__(self):
#         return self.title
    
# class CollectionStatistic(models.Model):

#     section=models.ForeignKey(
#         CollectionSection,
#         on_delete=models.CASCADE,
#         related_name="statistics"
#     )

#     label=models.CharField(max_length=200)

#     value=models.CharField(max_length=100)

#     display_order=models.PositiveIntegerField(default=0)

#     is_full_crud = models.BooleanField(default=False)

#     def __str__(self):
#         return self.label
    
# class CollectionDefinition(models.Model):

#     term=models.CharField(max_length=200)

#     description=models.TextField()

#     display_order=models.PositiveIntegerField(default=0)

#     is_full_crud = models.BooleanField(default=False)

#     def __str__(self):
#         return self.term


# help page
from Library.models import Library


# class HelpSection(models.Model):
#     """
#     Large cards shown on the Help page.

#     Example:
#     - Help Getting Materials
#     - Support Contacts
#     - Workshops, Classes & Events
#     - For Instructors
#     """

#     title = models.CharField(max_length=200)

#     slug = models.SlugField(
#         unique=True,
#         blank=True
#     )

#     description = models.TextField()

#     image = models.ImageField(
#         upload_to="help/sections/"
#     )

#     icon = models.CharField(
#         max_length=100,
#         default="fa-book-open",
#         help_text="FontAwesome icon class without 'fa-solid'"
#     )

#     display_order = models.PositiveIntegerField(default=0)

#     is_horizontal = models.BooleanField(
#         default=False,
#         help_text="Use for the bottom horizontal card."
#     )

#     is_active = models.BooleanField(default=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     updated_at = models.DateTimeField(auto_now=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         ordering = ["display_order"]

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title


# class HelpTopic(models.Model):
#     """
#     Links inside each Help Section.
#     """

#     CATEGORY_CHOICES = (
#         ("GETTING_HELP", "Getting Help"),
#         ("ACCOUNT_ACCESS", "Account & Access"),
#         ("BORROWING", "Borrowing"),
#         ("LEARNING", "Learning"),
#         ("PEOPLE", "People"),
#     )

#     section = models.ForeignKey(
#         HelpSection,
#         on_delete=models.CASCADE,
#         related_name="topics"
#     )

#     PAGE_TYPE_CHOICES = (
#     ("CATALOG", "Catalog"),
#     ("CONTENT", "Content"),
#     ("FAQ", "FAQ"),
#     )

#     page_type = models.CharField(
#         max_length=20,
#         choices=PAGE_TYPE_CHOICES,
#         default="CONTENT"
#     )



#     title = models.CharField(max_length=200)

#     slug = models.SlugField(
#         unique=True,
#         blank=True
#     )

#     category = models.CharField(
#         max_length=30,
#         choices=CATEGORY_CHOICES
#     )

#     url = models.CharField(max_length=300)

#     display_order = models.PositiveIntegerField(default=0)

#     is_active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         ordering = ["display_order", "title"]

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title


class HelpContactMethod(models.Model):
    """
    Sidebar contact methods.
    """

    METHOD_CHOICES = (
        ("CHAT", "Chat"),
        ("CALL", "Call"),
        ("EMAIL", "Email"),
        ("VISIT", "Visit"),
        ("APPOINTMENT", "Appointment"),
    )

    method_type = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES
    )

    library = models.ForeignKey(
        Library,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="help_contacts"
    )

    label = models.CharField(max_length=200)

    value = models.CharField(
        max_length=300,
        help_text="URL, phone number, email etc."
    )

    hours_text = models.CharField(
        max_length=200,
        blank=True
    )

    is_online = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.label


class HelpSidebarLink(models.Model):
    """
    Bottom sidebar links.

    Example:
    Ask a Librarian Hours
    Contact Us
    """

    title = models.CharField(max_length=200)

    url = models.CharField(max_length=300)

    icon = models.CharField(
        max_length=100,
        default="fa-clock"
    )

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title

# updated help models

# class HelpPageSection(models.Model):
#     """
#     Sections inside a HelpSection page.

#     Example:
#     - How to Use the Catalog
#     - My Account
#     - Tutorials on Finding Books
#     """

#     help_topic = models.ForeignKey(
#         HelpTopic,
#         on_delete=models.CASCADE,
#         related_name="page_sections"
#     )

#     title = models.CharField(max_length=200)

#     description = models.TextField(blank=True)

#     display_order = models.PositiveIntegerField(default=0)

#     is_active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.title
    
# class HelpPageItem(models.Model):
#     """
#     Links inside HelpPageSection.
#     """

#     page_section = models.ForeignKey(
#         HelpPageSection,
#         on_delete=models.CASCADE,
#         related_name="items"
#     )

#     title = models.CharField(max_length=200)

#     url = models.CharField(max_length=300)

#     display_order = models.PositiveIntegerField(default=0)

#     is_active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.title

# class HelpTopicPage(models.Model):
#     help_topic = models.OneToOneField(
#         HelpTopic,
#         on_delete=models.CASCADE,
#         related_name="page"
#     )

#     banner_image = models.ImageField(
#     upload_to="help/banners/",
#     blank=True,
#     null=True,
#     help_text="Hero banner image"
#     )

#     page_title = models.CharField(max_length=200)

#     breadcrumb_title = models.CharField(max_length=100)

#     is_active = models.BooleanField(default=True)

#     display_order = models.PositiveIntegerField(default=0)

#     is_full_crud = models.BooleanField(default=False)

#     def __str__(self):
#         return self.page_title
    
# class HelpTopicContent(models.Model):
#     page = models.ForeignKey(
#         HelpTopicPage,
#         on_delete=models.CASCADE,
#         related_name="contents"
#     )
#     image = models.ImageField(
#     upload_to="help/topic_content/",
#     blank=True,
#     null=True
#     )

#     heading = models.CharField(max_length=200)

#     content = models.TextField()

#     display_order = models.PositiveIntegerField(default=0)

#     is_active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.heading
    
# class HelpTopicBullet(models.Model):
#     section = models.ForeignKey(
#         HelpTopicContent,
#         on_delete=models.CASCADE,
#         related_name="bullets"
#     )

#     bullet_text = models.CharField(max_length=500)

#     display_order = models.PositiveIntegerField(default=0)

#     is_active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.bullet_text
    


# class HelpFAQPage(models.Model):

#     help_topic = models.OneToOneField(
#         HelpTopic,
#         on_delete=models.CASCADE,
#         related_name="faq_page"
#     )
#     banner_image = models.ImageField(
#     upload_to="help/banners/",
#     blank=True,
#     null=True,
#     help_text="Hero banner image"
#     )

#     page_title = models.CharField(max_length=200)

#     intro = models.TextField(blank=True)

#     is_active = models.BooleanField(default=True)

#     display_order = models.PositiveIntegerField(default=0)

#     is_full_crud = models.BooleanField(default=True)

#     def __str__(self):
#         return self.page_title
    
# class HelpFAQ(models.Model):

#     page = models.ForeignKey(
#         HelpFAQPage,
#         on_delete=models.CASCADE,
#         related_name="faqs"
#     )

#     question = models.CharField(max_length=500)

#     answer = models.TextField()

#     display_order = models.PositiveIntegerField(default=0)

#     is_active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.question

# class HelpTopicRelatedLink(models.Model):
#     """
#     Related links shown below each help section.
#     """

#     content = models.ForeignKey(
#         HelpTopicContent,
#         on_delete=models.CASCADE,
#         related_name="related_links"
#     )

#     title = models.CharField(
#         max_length=200
#     )

#     url = models.CharField(
#         max_length=300
#     )

#     icon = models.CharField(
#         max_length=100,
#         default="fa-arrow-right"
#     )

#     display_order = models.PositiveIntegerField(
#         default=0
#     )

#     is_active = models.BooleanField(
#         default=True
#     )

#     is_full_crud = models.BooleanField(
#         default=False
#     )

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.title
    


# *****updated librarystaff model

from django.db import models
from Staff.models import StaffProfile


class LibraryStaff(models.Model):

    ROLE_CHOICES = (
        ("LIBRARIAN", "Librarian"),
        ("LIBRARY_ASSISTANT", "Library Assistant"),
        ("ARCHIVIST", "Archivist"),
        ("DIGITAL_COLLECTIONS_MANAGER", "Digital Collections Manager"),
    )

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="library_assignments"
    )

    assigned_library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name="staff_members"
    )

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES
    )

    assigned_date = models.DateField()

    active = models.BooleanField(default=True)

    # New fields for your People Directory
    profile_photo = models.ImageField(
        upload_to="library/staff/",
        blank=True,
        null=True
    )

    office_location = models.CharField(
        max_length=200,
        blank=True
    )

    biography = models.TextField(
        blank=True
    )

    pronouns = models.CharField(max_length=50, blank=True)

    office_address = models.TextField(blank=True)

    campus_map_link = models.URLField(blank=True)

    office_hours = models.TextField(blank=True)


    subject_specialties = models.ManyToManyField(
        "SubjectSpecialty",
        blank=True
    )

    # citation_managers = models.ManyToManyField(
    # "CitationManager",
    # blank=True,
    # related_name="library_staff"
    # )

    is_public = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=0)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "library_staff"


# Borrow Request 
from django.db import models
from Admin.models import User
from Staff.models import StaffProfile


class BorrowRequest(models.Model):

    uuid = models.UUIDField(
       default=uuid.uuid4,
       unique=True,
       editable=False
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
        ("ISSUED", "Issued"),        # <-- NEW
        ("RETURNED", "Returned"),
    )

    resource = models.ForeignKey(
        LibraryResource,
        on_delete=models.CASCADE,
        related_name="borrow_requests"
    )

    library_user = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name="borrow_requests"
    )

    request_date = models.DateField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    approved_by = models.ForeignKey(
       LibraryStaff,
       on_delete=models.SET_NULL,
       null=True,
       blank=True,
       related_name="approved_borrow_requests"
    )

    approved_date = models.DateTimeField(
        null=True,
        blank=True
    )

    rejection_reason = models.TextField(
        blank=True,
        null=True
    )

    is_full_crud = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "borrow_requests"
        ordering = ["-request_date"]

    def __str__(self):
        return f"{self.library_user} - {self.resource.title}"


class SubjectSpecialty(models.Model):

    name = models.CharField(max_length=100)

    is_full_crud = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# datapage
from django.db import models
from django.utils.text import slugify


# class DataManagementPlan(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(max_length=200)

#     slug = models.SlugField(
#         unique=True,
#         blank=True
#     )

#     introduction = models.TextField()

#     banner_image = models.ImageField(
#         upload_to="data_management/",
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title


# class DataManagementSidebar(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     page = models.ForeignKey(
#         DataManagementPlan,
#         related_name="menus",
#         on_delete=models.CASCADE
#     )

#     title = models.CharField(max_length=200)

#     anchor = models.CharField(
#         max_length=100,
#         help_text="Example: introduction"
#     )

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.title


# class DataManagementPlanSection(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     menu = models.ForeignKey(
#         DataManagementSidebar,
#         related_name="sections",
#         on_delete=models.CASCADE
#     )

#     heading = models.CharField(max_length=250)

#     content = models.TextField()

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.heading


# class DataManagementSectionLink(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     section = models.ForeignKey(
#         DataManagementPlanSection,
#         related_name="links",
#         on_delete=models.CASCADE
#     )

#     title = models.CharField(max_length=200)

#     url = models.URLField()

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.title
    
# grants page

# from django.db import models
# from django.utils.text import slugify


# class GrantsScholarshipPage(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(max_length=200)

#     slug = models.SlugField(
#         unique=True,
#         blank=True
#     )

#     introduction = models.TextField(blank=True)

#     banner_image = models.ImageField(
#         upload_to="grants_scholarships/",
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.title
    
# class GrantsScholarshipSidebar(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     page = models.ForeignKey(
#         GrantsScholarshipPage,
#         related_name="menus",
#         on_delete=models.CASCADE
#     )

#     title = models.CharField(max_length=200)

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.title
    
# class GrantsScholarshipGuide(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     menu = models.ForeignKey(
#         GrantsScholarshipSidebar,
#         related_name="guides",
#         on_delete=models.CASCADE
#     )

#     title = models.CharField(max_length=250)

#     url = models.CharField(
#         max_length=300
#     )

#     updated_date = models.DateField()

#     views = models.PositiveIntegerField(default=0)

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.title

# evidance
# class EvidenceSynthesisPage(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE", "Active"),
#         ("INACTIVE", "Inactive"),
#     )

#     title = models.CharField(max_length=200)

#     slug = models.SlugField(
#         unique=True,
#         blank=True
#     )

#     introduction = models.TextField()

#     banner_image = models.ImageField(
#         upload_to="evidence_synthesis/",
#         blank=True,
#         null=True
#     )

#     display_order = models.PositiveIntegerField(default=0)

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud = models.BooleanField(default=True)

#     def save(self,*args,**kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super().save(*args,**kwargs)

#     def __str__(self):
#         return self.title

# class EvidenceSynthesisSection(models.Model):

#     STATUS_CHOICES = (
#         ("ACTIVE","Active"),
#         ("INACTIVE","Inactive"),
#     )

#     page = models.ForeignKey(
#         EvidenceSynthesisPage,
#         related_name="sections",
#         on_delete=models.CASCADE
#     )

#     title = models.CharField(max_length=250)

#     image = models.ImageField(
#         upload_to="evidence_synthesis/sections/"
#     )

#     content = models.TextField()

#     display_order=models.PositiveIntegerField(default=0)

#     status=models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud=models.BooleanField(default=True)

#     class Meta:
#         ordering=["display_order"]

#     def __str__(self):
#         return self.title

# class EvidenceSynthesisSectionLink(models.Model):

#     STATUS_CHOICES=(
#         ("ACTIVE","Active"),
#         ("INACTIVE","Inactive"),
#     )

#     section=models.ForeignKey(
#         EvidenceSynthesisSection,
#         related_name="links",
#         on_delete=models.CASCADE
#     )

#     title=models.CharField(max_length=200)

#     url=models.URLField()

#     display_order=models.PositiveIntegerField(default=0)

#     status=models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="ACTIVE"
#     )

#     is_full_crud=models.BooleanField(default=True)

#     class Meta:
#         ordering=["display_order"]

#     def __str__(self):
#         return self.title
    
# help circulation support contact
from django.db import models

class CirculationInquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    question = models.TextField()
    consent_given = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.submitted_at.strftime('%Y-%m-%d')}"


# technical assistance page
from django.db import models

class TechnicalAssistanceInquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    consent_given = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)

    is_full_crud = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    


# find a consultant
# class CitationManager(models.Model):
#     name = models.CharField(max_length=100, unique=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         db_table = "citation_manager"
#         ordering = ["name"]

#     def __str__(self):
#         return self.name
    

# UWDCC: Submit a Project Proposal form

from django.db import models

class ProposalSubmission(models.Model):
    project_idea = models.TextField()

    name = models.CharField(max_length=200)

    phone = models.CharField(max_length=20)

    email = models.EmailField()

    title = models.CharField(max_length=200, blank=True)

    department = models.CharField(max_length=200, blank=True)

    institution = models.CharField(max_length=200, blank=True)

    institution_director = models.CharField(max_length=200, blank=True)

    agree = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Digital Collections Proposal"
        verbose_name_plural = "Digital Collections Proposals"

    def __str__(self):
        return f"{self.name} - {self.project_idea[:30]}"
    


#  contact the UWDCC form

from django.db import models


class DigitalCollectionsContact(models.Model):

    name = models.CharField(
        max_length=150
    )

    email = models.EmailField()

    subject = models.CharField(
        max_length=250,
        blank=True
    )

    question = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_full_crud = models.BooleanField(default=False)

    class Meta:

        ordering = ["-created_at"]

        verbose_name = "Digital Collections Contact"

        verbose_name_plural = "Digital Collections Contacts"

    def __str__(self):
        return f"{self.name} - {self.email}"

    name = models.CharField(max_length=150)

    email = models.EmailField()

    subject = models.CharField(max_length=200, blank=True)

    question = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Digital Collections Contact"
        verbose_name_plural = "Digital Collections Contacts"

    def __str__(self):
        return self.name
    


# instruction rooms

# class LibraryInstructionSpace(models.Model):
#     room_name = models.CharField(max_length=200)
#     floorplan_url = models.URLField(blank=True)
#     display_order = models.PositiveIntegerField(default=0)
#     is_active = models.BooleanField(default=True)

#     is_full_crud = models.BooleanField(default=False)

#     class Meta:
#         ordering = ["display_order"]

#     def __str__(self):
#         return self.room_name


# ============================================================
# AI LIBRARY CHAT
# ============================================================

import uuid

from django.conf import settings
from django.db import models


class AIConversation(models.Model):
    """
    Stores one student's library AI conversation.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="library_ai_conversations",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.title or 'Library AI Chat'}"
        )


class AIMessage(models.Model):
    """
    Stores each user/assistant message in a conversation.
    """

    ROLE_CHOICES = (
        ("USER", "User"),
        ("ASSISTANT", "Assistant"),
    )

    SOURCE_TYPE_CHOICES = (
        ("CATALOG", "Catalog"),
        ("WORKFLOW", "Workflow"),
        ("PERSONAL_DATA", "Personal Data"),
        ("GROQ", "Groq"),
    )

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    content = models.TextField()

    intent = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    source_type = models.CharField(
        max_length=30,
        choices=SOURCE_TYPE_CHOICES,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_full_crud = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.conversation.title or 'Library AI Chat'} - "
            f"{self.role}"
        )