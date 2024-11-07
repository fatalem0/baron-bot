from baron.background_jobs.approve_event_if_has_min_attendees import approve_event_if_has_min_attendees
from configs.models import load_config_global


async def start_background_jobs(application):
    job_queue = application.job_queue
    config = load_config_global().jobs

    # Запускаем задачу каждые 5 минут
    job_queue.run_repeating(approve_event_if_has_min_attendees,
                            interval=config['approve_event_if_has_min_attendees']['interval'],
                            first=config['approve_event_if_has_min_attendees']['first'])
