from django.core.management.base import BaseCommand
from core.services.scheduler import Scheduler
from core.services.simulation import SimulationEngine
import time

class Command(BaseCommand):
    help = 'Start the scheduler and simulation engine for the HVAC system'

    def handle(self, *args, **options):
        scheduler = Scheduler()
        scheduler.start()
        sim = SimulationEngine()
        sim.start()
        self.stdout.write(self.style.SUCCESS('Scheduler and Simulation started. Press Ctrl+C to stop.'))
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sim.stop()
            scheduler.stop()
            self.stdout.write(self.style.WARNING('Stopped.'))
