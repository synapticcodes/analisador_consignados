"""
Celery App Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Configuração do Celery para processamento assíncrono de jobs.
"""

from celery import Celery

from app.core.config import settings

# Criar instância do Celery
celery_app = Celery(
    "calculadora_consignados",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

# Configuração do Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos max por task
    task_soft_time_limit=25 * 60,  # 25 minutos soft limit
    worker_prefetch_multiplier=1,  # Processar uma task por vez
    worker_max_tasks_per_child=50,  # Reciclar worker após 50 tasks
    result_expires=3600,  # Resultados expiram em 1 hora
)

# Autodiscovery de tasks (opcional)
# celery_app.autodiscover_tasks()


if __name__ == "__main__":
    celery_app.start()
