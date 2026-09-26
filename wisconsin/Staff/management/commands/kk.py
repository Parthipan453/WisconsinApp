from django.core.management.base import BaseCommand

class Command(BaseCommand):                  
    help = "Explains what this command does"

    def handle(self, *args, **options):      
        print("Hello!")