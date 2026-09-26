from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from Events.models import Event, EventCategory, EventVenue
from Admin.models import User


class Command(BaseCommand):
    help = "Seed Events module with Categories, Venues and Events"

    def handle(self, *args, **kwargs):
        self.stdout.write("🎉 Seeding Events Data...")

        categories = self._seed_categories()
        venues = self._seed_venues()
        self._seed_events(categories, venues)

        self.stdout.write(self.style.SUCCESS("✅ Events seeding completed!"))

    # --------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------
    def _seed_categories(self):
        categories_data = [
            ("Academic Conferences", "Annual academic research symposiums, keynote presentations, and departmental seminars."),
            ("Workshops & Training", "Skill development workshops, professional training sessions, and technical bootcamps."),
            ("Student Organizations", "Events, meetings, and cultural gatherings hosted by registered student clubs and campus societies."),
            ("Sports & Athletics", "Inter-college athletic competitions, sports tournaments, fitness programs, and outdoor games."),
            ("Cultural & Arts", "Performing arts shows, musical concerts, art exhibitions, and multicultural festivals."),
            ("Career & Placement", "Job fairs, campus placement drives, resume workshops, and recruiter interactions."),
            ("Guest Lectures", "Talks and lectures delivered by visiting scholars, alumni, and industry professionals."),
        ]

        categories = {}
        created_count = 0

        for name, description in categories_data:
            obj, created = EventCategory.objects.get_or_create(
                category_name=name,
                defaults={"description": description},
            )
            categories[name] = obj
            if created:
                created_count += 1

        self.stdout.write(f"✔ {created_count} categories created")
        return categories

    # --------------------------------------------------
    # VENUES
    # --------------------------------------------------
    def _seed_venues(self):
        venues_data = [
            ("Main Auditorium", "Central Block", "A-101", 500, "Ground floor, near main entrance"),
            ("Seminar Hall 1", "Academic Block A", "B-204", 150, "Second floor, beside library"),
            ("Seminar Hall 2", "Academic Block B", "B-105", 120, "First floor, near cafeteria"),
            ("Open Air Theatre", "Sports Complex", "OAT", 1000, "Adjacent to the main stadium"),
            ("Conference Room", "Admin Block", "C-301", 40, "Third floor, admin wing"),
            ("Indoor Sports Arena", "Sports Complex", "SPA-1", 300, "Near the athletics track"),
            ("Computer Lab 3", "Engineering Block", "CL-303", 60, "Third floor, near the elevator"),
            ("Innovation Hub", "Research Block", "IH-01", 80, "Ground floor, glass wing"),
        ]

        venues = {}
        created_count = 0

        for name, building, room, capacity, location in venues_data:
            obj, created = EventVenue.objects.get_or_create(
                venue_name=name,
                defaults={
                    "building_name": building,
                    "room_number": room,
                    "seating_capacity": capacity,
                    "location_details": location,
                },
            )
            venues[name] = obj
            if created:
                created_count += 1

        self.stdout.write(f"✔ {created_count} venues created")
        return venues

    # --------------------------------------------------
    # EVENTS
    # --------------------------------------------------
    def _seed_events(self, categories, venues):

        organizer = User.objects.filter(is_admin=True).first() or User.objects.first()

        if not organizer:
            self.stdout.write(self.style.WARNING("⚠ No User found to assign as organizer. Skipping event creation."))
            return

        visibility_choices = ["Public", "Campus Only", "Invitation Only"]
        venue_names = list(venues.keys())

        now = timezone.now()
        created_count = 0

        # --------------------------------------------------
        # NAMED / REALISTIC EVENTS (19)
        # --------------------------------------------------
        events_data = [
            ("Annual Tech Symposium 2026", "Academic Conferences", -20, -20, "Completed"),
            ("AI & Machine Learning Bootcamp", "Workshops & Training", -10, -10, "Completed"),
            ("Inter-College Cultural Fest", "Cultural & Arts", -5, -4, "Completed"),
            ("Placement Drive - Infosys", "Career & Placement", -2, -2, "Completed"),
            ("Freshers' Welcome Party", "Student Organizations", -1, -1, "Completed"),

            ("Guest Lecture: Future of Robotics", "Guest Lectures", 0, 0, "Published"),
            ("Inter-Department Cricket Tournament", "Sports & Athletics", 2, 4, "Published"),
            ("Web Development Workshop", "Workshops & Training", 5, 5, "Published"),
            ("Annual Alumni Meet", "Student Organizations", 7, 7, "Published"),
            ("Research Paper Presentation Day", "Academic Conferences", 10, 10, "Published"),
            ("Music & Dance Night", "Cultural & Arts", 12, 12, "Published"),
            ("Campus Placement Drive - TCS", "Career & Placement", 15, 15, "Published"),

            ("Robotics Club Meetup", "Student Organizations", 20, 20, "Draft"),
            ("Data Science Career Talk", "Guest Lectures", 25, 25, "Draft"),
            ("Sports Meet 2026", "Sports & Athletics", 30, 32, "Draft"),
            ("Entrepreneurship Summit", "Academic Conferences", 35, 35, "Draft"),
            ("Photography Exhibition", "Cultural & Arts", 40, 41, "Draft"),

            ("Blockchain Fundamentals Workshop", "Workshops & Training", 18, 18, "Cancelled"),
            ("Inter-College Debate Championship", "Student Organizations", 22, 22, "Cancelled"),
        ]

        for title, category_name, start_offset, end_offset, status in events_data:

            start_dt = now + timedelta(days=start_offset, hours=random.choice([9, 10, 11, 14, 16]))
            end_dt = now + timedelta(days=end_offset, hours=random.choice([17, 18, 19]))

            obj, created = Event.objects.get_or_create(
                event_title=title,
                defaults={
                    "event_code": Event.generate_event_code(),
                    "event_category": categories.get(category_name),
                    "venue": venues.get(random.choice(venue_names)),
                    "organizer": organizer,
                    "start_datetime": start_dt,
                    "end_datetime": end_dt if status == "Completed" else (end_dt if random.choice([True, False]) else None),
                    "event_status": status,
                    "event_visibility": random.choice(visibility_choices),
                },
            )

            if created:
                created_count += 1

        self.stdout.write(f"✔ {created_count} named events created")

        # --------------------------------------------------
        # BULK GENERIC EVENTS (~31 more, to reach ~50 total)
        # --------------------------------------------------
        subjects = [
            ("Workshop", "Workshops & Training"),
            ("Seminar", "Academic Conferences"),
            ("Cultural Night", "Cultural & Arts"),
            ("Sports Meet", "Sports & Athletics"),
            ("Club Gathering", "Student Organizations"),
            ("Career Fair", "Career & Placement"),
            ("Guest Talk", "Guest Lectures"),
        ]

        status_pool = ["Draft", "Published", "Published", "Completed", "Cancelled"]

        bulk_created = 0

        for i in range(1, 32):

            subject_name, category_name = random.choice(subjects)
            title = f"{subject_name} Series - Session {i}"

            status = random.choice(status_pool)

            # Completed events must be in the past, upcoming ones in the future
            if status == "Completed":
                start_offset = -random.randint(1, 60)
            else:
                start_offset = random.randint(1, 90)

            end_offset = start_offset + random.choice([0, 1, 2])

            start_dt = now + timedelta(days=start_offset, hours=random.choice([9, 10, 11, 14, 16]))
            end_dt = now + timedelta(days=end_offset, hours=random.choice([17, 18, 19]))

            obj, created = Event.objects.get_or_create(
                event_title=title,
                defaults={
                    "event_code": Event.generate_event_code(),
                    "event_category": categories.get(category_name),
                    "venue": venues.get(random.choice(venue_names)),
                    "organizer": organizer,
                    "start_datetime": start_dt,
                    "end_datetime": end_dt if status == "Completed" else (end_dt if random.choice([True, False]) else None),
                    "event_status": status,
                    "event_visibility": random.choice(visibility_choices),
                },
            )

            if created:
                bulk_created += 1

        self.stdout.write(f"✔ {bulk_created} bulk events created")
        self.stdout.write(f"✔ {created_count + bulk_created} total events created")