from django.db import models
from Admin.models import User
import uuid

############# SportsHub Models Start ############

class Sport(models.Model):

    user_types = ["admin"]

    SPORT_TYPE = (
        ("INDOOR", "Indoor"),
        ("OUTDOOR", "Outdoor"),
        ("BOTH", "Both"),
    )

    GENDER_CHOICES = (
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("TRANSGENDER", "Transgender"),
        ("NON_BINARY", "Non-binary"),
        ("OTHER", "Other"),
        ("PREFER_NOT_TO_SAY", "Prefer not to say"),
    )

    sport_name = models.CharField(
        max_length=100,
        unique=True
    )

    sport_uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    
    sport_type = models.CharField(
        max_length=20,
        choices=SPORT_TYPE
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES
    )
    
    is_team_sport = models.BooleanField(default=False)

    min_players = models.PositiveIntegerField(null=True, blank=True)

    max_players = models.PositiveIntegerField(null=True, blank=True)

    is_olympic_sport = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)

    is_full_crud = models.BooleanField(default=True)

    icon = models.ImageField(
        upload_to="sports/icons/",
        null=True,
        blank=True
    )

    thumbnail = models.ImageField(
        upload_to="sports/thumbnail",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sport_name
    
class SportClub(models.Model):

    club_name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    sport = models.ForeignKey(
        Sport,
        on_delete=models.CASCADE,
        related_name="club"
    )

    ############ swetha's code start ############

    image = models.ImageField(
        upload_to="sports/clubs/",
        blank=True,
        null=True
    )

    ############ swetha's code end ##############

    is_active = models.BooleanField(default=True)

    logo = models.ImageField(
        upload_to="sports/club/",
        null=True,
        blank=True
    )

    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.club_name
    
    ############ swetha's code start ############
     
    @property
    def total_teams(self):
        return self.teams.count()

    @property
    def total_coaches(self):
        return Coach.objects.filter(head_coached_teams__club=self).distinct().count()
    
    ############ swetha's code end ##############

    
    
class Coach(models.Model):

    ROLE_CHOICES = (
        ('HEAD', 'Head Coach'),
        ('ASSISTANT', 'Assistant Coach'),
        ('STRENGTH', 'Strength Coach'),
        ('TRAINER', 'Athletic Trainer'),
        ('OTHER', 'Other'),
    )
    
    coach_id = models.AutoField(primary_key=True)

    staff_id = models.CharField(max_length=50, unique=True)

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    hire_date = models.DateField()

    certifications = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    is_full_crud = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.staff_id} - {self.role}"
    
class SportsFacility(models.Model):
    FACILITY_TYPES = (
        ('STADIUM', 'Stadium'),
        ('ARENA', 'Arena'),
        ('FIELD', 'Field'),
        ('POOL', 'Pool'),
        ('GYMNASIUM', 'Gymnasium'),
        ('TRAINING_CENTER', 'Training Center'),
        ('OTHER', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('INACTIVE', 'Inactive'),
    )
    
    facility_id = models.AutoField(primary_key=True)

    facility_name = models.CharField(max_length=100, unique=True)

    #####  swetha code start #####

    sport=models.ForeignKey(Sport,on_delete=models.CASCADE,related_name="facilities",null=True,blank=True)
    
    
    ##### swetha code end ######


    facility_type = models.CharField(max_length=50, choices=FACILITY_TYPES)

    capacity = models.PositiveIntegerField()

    location = models.CharField(max_length=200)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    
    ###### swetha code strat ########

    image = models.ImageField(upload_to="sports/images/", null=False, blank=True)

    ######## swetha code end #######

    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.facility_name
    
class SportTeamModel(models.Model):

    user_types = ["admin"]

    GENDER_CHOICES = (
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("TRANSGENDER", "Transgender"),
        ("NON_BINARY", "Non-binary"),
        ("OTHER", "Other"),
        ("PREFER_NOT_TO_SAY", "Prefer not to say"),
    )

    team_id = models.AutoField(primary_key=True)

    team_uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    
    team_code = models.CharField(
        max_length=20,
        unique=True
    )

    icon = models.ImageField(
        upload_to="teams/icon",
        null=True,
        blank=True,
    )

    team_name = models.CharField(
        max_length=100,
        unique=True
    )

    sport_type = models.ForeignKey(
        Sport,
        on_delete=models.CASCADE,
        related_name="teams"
    )

    gender_category = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES
    )

    division = models.CharField(max_length=100)

    season = models.CharField(max_length=100)

    head_coach = models.ForeignKey(
        Coach,
        on_delete=models.SET_NULL,
        null=True,
        related_name="head_coached_teams"
    )

    home_facility = models.ForeignKey(
        SportsFacility,
        on_delete=models.SET_NULL,
        null=True,
        related_name="home_teams"
    )

    founded_year = models.IntegerField()

    status = models.BooleanField(default=True)

    club = models.ForeignKey(
        SportClub,
        on_delete=models.CASCADE,
        related_name="teams",
        null=True,
        blank=True
    )

    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team_name} ({self.sport_type})"
    
class Athletic(models.Model):
    
    user_types = ["admin"]

    CLASS_YEAR_CHOICES = (
        ("FRESHMAN", "Freshman"),
        ("SOPHOMORE", "Sophomore"),
        ("JUNIOR", "Junior"),
        ("SENIOR", "Senior"),
        ("GRADUATE", "Graduate"),
        ("FACULTY", "Faculty"),
        ("STAFF", "Staff"),
    )
    
    ELIGIBILITY_CHOICES = (
        ("ELIGIBLE", "Eligible"),
        ("INELIGIBLE", "Ineligible"),
        ("PROBATION", "Probation"),
        ("REDSHIRT", "Redshirt"),
        ("MEDICAL", "Medical Redshirt"),
    )

    athlete_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="athlete_profile",  null=True, blank=True,
    )

    team = models.ForeignKey(
        SportTeamModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="athletes"
    )

    individual_sports = models.ManyToManyField(
        Sport,
        blank=True,
        related_name="individual_atheletes"
    )

    jersey_number = models.PositiveBigIntegerField(null=True, blank=True)

    position = models.CharField(max_length=50, null=True, blank=True)

    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class_year = models.CharField(max_length=20, choices=CLASS_YEAR_CHOICES, default="FRESHMAN")

    eligibility_status = models.CharField(max_length=20, choices=ELIGIBILITY_CHOICES, default="ELIGIBLE")

    scholarship_status = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    is_full_crud = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.team.team_name if self.team else 'Individual Sport'}"
    
    def get_individual_sports_list(self):
            return ", ".join([sport.sport_name for sport in self.individual_sports.all()])
    
############# SportsHub Models End ############ 