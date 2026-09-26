

import os
import shutil
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


APP_LABELS = [
    "Admin",
    "PermissionAccess",
    "Colleges",
    "bela_admin",
    "Applicants",
    "Events",
    "Faculty",
    "Library",
    "Medical",
    "Research",
    "Scholarships",
    "Staff",
    "Students",
]

SKIP_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "node_modules",
    "__pycache__", "site-packages",
}


class Command(BaseCommand):
    help = (
        "Deletes all migrations folders' contents and the database file, "
        "then runs makemigrations + migrate with live output. "
        "FOR TESTING/DEV USE ONLY."
    )

    def log(self, msg):
        self.stdout.write(f"[reset_db] {msg}")
        self.stdout.flush()

 
    def find_migration_dirs(self, root: Path):
        found = []
        for dirpath, dirnames, _filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            if os.path.basename(dirpath) == "migrations":
                found.append(Path(dirpath))
        return found

    def clean_migrations_folder(self, migrations_dir: Path):
       
        app_label = migrations_dir.parent.name
        self.log(f"  -> Deleting migrations for app: {app_label}  ({migrations_dir})")

        removed = []
        for item in migrations_dir.iterdir():
            if item.name == "__init__.py":
                continue
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed.append(item.name)
            except Exception as e:
                self.log(f"     ! Failed to remove {item}: {e}")

        init_file = migrations_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            removed.append("(created __init__.py)")

        if removed:
            self.log(f"     Removed: {', '.join(removed)}")
        else:
            self.log(f"     Nothing to remove (already clean)")

    
    def delete_database_files(self):
        
        any_deleted = False
        for alias, db_config in settings.DATABASES.items():
            if db_config.get("ENGINE") != "django.db.backends.sqlite3":
                self.log(f"  -> Skipping non-sqlite database '{alias}' ({db_config.get('ENGINE')})")
                continue

            db_name = db_config.get("NAME")
            if not db_name:
                continue

            db_path = Path(db_name)

            if db_path.exists():
                try:
                    db_path.unlink()
                    self.log(f"  -> Deleted database file for '{alias}': {db_path}")
                    any_deleted = True
                except Exception as e:
                    self.log(f"     ! Failed to delete {db_path}: {e}")
            else:
                self.log(f"  -> No database file found for '{alias}' at: {db_path} (skipping)")

            
            for suffix in ("-journal", "-wal", "-shm"):
                sidecar = Path(str(db_path) + suffix)
                if sidecar.exists():
                    try:
                        sidecar.unlink()
                        self.log(f"     Also removed sidecar file: {sidecar}")
                    except Exception as e:
                        self.log(f"     ! Failed to delete sidecar {sidecar}: {e}")

        if not any_deleted:
            self.log("  -> No sqlite database files were deleted.")

  
    def run_command_live(self, cmd, cwd):
        self.log(f"Running: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line-buffered
        )

       
        for line in iter(process.stdout.readline, ""):
            if line == "" and process.poll() is not None:
                break
            if line:
                self.stdout.write(line.rstrip("\n"))
                self.stdout.flush()

        process.stdout.close()
        return_code = process.wait()

        if return_code != 0:
            self.log(f"Command FAILED (exit code {return_code}): {' '.join(cmd)}")
            return False
        self.log(f"Command SUCCEEDED: {' '.join(cmd)}")
        return True

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR)
        self.log(f"Project root: {root}")

        self.log("=" * 70)
        self.log("STEP 1: Deleting migration files (per app)")
        self.log("=" * 70)
        migration_dirs = self.find_migration_dirs(root)
        if not migration_dirs:
            self.log("No migrations folders found.")
        else:
            self.log(f"Found {len(migration_dirs)} migrations folder(s). Cleaning each one:")
            for d in migration_dirs:
                self.clean_migrations_folder(d)

        self.log("=" * 70)
        self.log("STEP 2: Deleting database file(s)")
        self.log("=" * 70)
        self.delete_database_files()

        python_exe = sys.executable
        manage_py = str(root / "manage.py")

        self.log("=" * 70)
        self.log("STEP 3: Running makemigrations")
        self.log("=" * 70)
        makemigrations_cmd = [python_exe, manage_py, "makemigrations"] + APP_LABELS
        mk_ok = self.run_command_live(makemigrations_cmd, cwd=root)

        if not mk_ok:
            self.log("Aborting before migrate since makemigrations failed.")
            sys.exit(1)

        self.log("=" * 70)
        self.log("STEP 4: Running migrate")
        self.log("=" * 70)
        migrate_ok = self.run_command_live([python_exe, manage_py, "migrate"], cwd=root)

        self.log("=" * 70)
        if migrate_ok:
            self.log("ALL DONE: migrations reset, db recreated, and migrate applied successfully.")
        else:
            self.log("migrate FAILED. Check the output above for details.")
            sys.exit(1)