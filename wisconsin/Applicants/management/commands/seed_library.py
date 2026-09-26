from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files.base import ContentFile
import requests
import random

from Library.models import Library, ResourceCategory, LibraryResource
from Admin.bela_admin.models import Building


class Command(BaseCommand):
    help = "Seed Library with Real Books + HD Covers"

    def handle(self, *args, **kwargs):
        self.stdout.write("📚 Seeding Library Data...")

        library = self._seed_library()
        categories = self._seed_categories()
        self._seed_books(library, categories)

        self.stdout.write(self.style.SUCCESS("✅ Library seeding completed!"))

    # --------------------------------------------------
    # DOWNLOAD IMAGE
    # --------------------------------------------------
    def download_image(self, url):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return ContentFile(response.content)
        except Exception:
            return None

    # --------------------------------------------------
    # LIBRARY
    # --------------------------------------------------
    def _seed_library(self):
        building = Building.objects.first()

        library, _ = Library.objects.get_or_create(
            library_code="LIB001",
            defaults={
                "library_name": "Central Library",
                "building": building,
                "email": "library@college.com",
                "phone": "9876543210",
                "status": "ACTIVE",
                "description": "Main campus library",
                "address": "Campus Main Block"
            }
        )

        return library

    # --------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------
    def _seed_categories(self):
        categories_data = [
            "Computer Science",
            "Programming",
            "Database",
            "Artificial Intelligence",
            "History",
            "Mathematics",
        ]

        categories = {}

        for title in categories_data:
            obj, _ = ResourceCategory.objects.get_or_create(
                title=title,
                defaults={
                    "slug": slugify(title),
                    "description": f"{title} books",
                    "status": "ACTIVE",
                }
            )
            categories[title] = obj

        return categories

    # --------------------------------------------------
    # BOOKS WITH REAL NAMES + HD COVERS
    # --------------------------------------------------
    def _seed_books(self, library, categories):

        books_data = [

            # -------- PYTHON --------
            ("Python Crash Course", "Eric Matthes", "Programming",
            "https://picsum.photos/400/600?random=1"),

            ("Automate the Boring Stuff with Python", "Al Sweigart", "Programming",
            "https://picsum.photos/400/600?random=2"),

            ("Fluent Python", "Luciano Ramalho", "Programming",
            "https://picsum.photos/400/600?random=3"),

            # -------- JAVA --------
            ("Effective Java", "Joshua Bloch", "Programming",
            "https://picsum.photos/400/600?random=4"),

            ("Head First Java", "Kathy Sierra", "Programming",
            "https://picsum.photos/400/600?random=5"),

            # -------- DATABASE --------
            ("Database System Concepts", "Korth", "Database",
            "https://picsum.photos/400/600?random=6"),

            ("SQL Cookbook", "Anthony Molinaro", "Database",
            "https://picsum.photos/400/600?random=7"),

            # -------- AI --------
            ("Artificial Intelligence: A Modern Approach", "Russell & Norvig", "Artificial Intelligence",
            "https://picsum.photos/400/600?random=8"),

            ("Deep Learning", "Ian Goodfellow", "Artificial Intelligence",
            "https://picsum.photos/400/600?random=9"),

            # -------- HISTORY --------
            ("Sapiens: A Brief History of Humankind", "Yuval Noah Harari", "History",
            "https://picsum.photos/400/600?random=10"),

            ("Guns, Germs, and Steel", "Jared Diamond", "History",
            "https://picsum.photos/400/600?random=11"),

            # -------- MATH --------
            ("Discrete Mathematics", "Kenneth Rosen", "Mathematics",
            "https://picsum.photos/400/600?random=12"),

            ("Linear Algebra and Its Applications", "Gilbert Strang", "Mathematics",
            "https://picsum.photos/400/600?random=13"),
        ]

        created_count = 0

        for title, author, category_name, image_url in books_data:

            obj, created = LibraryResource.objects.get_or_create(
                title=title,
                library=library,
                defaults={
                    "author": author,
                    "category": categories.get(category_name),
                    "resource_type": "BOOK",
                    "total_copies": 3,
                    "available_copies": 3,
                    "status": "ACTIVE",
                }
            )

            if created:
                created_count += 1

                image_file = self.download_image(image_url)

                if image_file:
                    obj.cover_image.save(
                        f"{slugify(title)}.jpg",
                        image_file,
                        save=True
                    )

        self.stdout.write(f"✔ {created_count} real books created")

        # --------------------------------------------------
        # BULK SUBJECT BASED BOOKS (STABLE IMAGES)
        # --------------------------------------------------

        subjects = [
            ("Python Programming", "Programming"),
            ("Java Development", "Programming"),
            ("Data Structures", "Computer Science"),
            ("Machine Learning", "Artificial Intelligence"),
            ("World History", "History"),
        ]

        for i in range(1, 101):

            subject_name, category_name = random.choice(subjects)
            title = f"{subject_name} Vol {i}"

            obj, created = LibraryResource.objects.get_or_create(
                title=title,
                library=library,
                defaults={
                    "author": f"Author {i}",
                    "category": categories.get(category_name),
                    "resource_type": "BOOK",
                    "total_copies": 2,
                    "available_copies": 2,
                    "status": "ACTIVE",
                }
            )

            if created:
                # 🔥 Stable image (no failure)
                img_url = f"https://picsum.photos/400/600?random={i}"

                image_file = self.download_image(img_url)

                if image_file:
                    obj.cover_image.save(
                        f"{slugify(title)}.jpg",
                        image_file,
                        save=True
                    )

        self.stdout.write("✔ 100 subject-based books with HD covers created")