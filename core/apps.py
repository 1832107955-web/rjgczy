from django.apps import AppConfig
import os

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Only run in the main process, not the reloader
        if os.environ.get('RUN_MAIN') == 'true':
            self.start_services()

    def start_services(self):
        from core.services.scheduler import Scheduler
        from core.services.simulation import SimulationEngine
        from core.models import Room
        from django.db.utils import OperationalError, ProgrammingError

        # Initialize Rooms
        try:
            # Check if table exists by querying
            if not Room.objects.exists():
                room_ids = ['301', '302', '303', '304', '305',
                            '401', '402', '403', '404', '405']
                for rid in room_ids:
                    Room.objects.create(room_id=rid)
                print("[Init] Created default rooms.")
        except (OperationalError, ProgrammingError):
            # DB not ready (e.g. during migration)
            print("[Init] Database not ready, skipping room initialization.")
            return

        # Start Scheduler
        scheduler = Scheduler()
        scheduler.start()
        
        # Start Simulation
        sim = SimulationEngine()
        sim.start()
