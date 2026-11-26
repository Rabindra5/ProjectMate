from django.apps import AppConfig

class ActivityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity'

    def ready(self):
        """Register authentication history signals."""
        
        from . import signals
