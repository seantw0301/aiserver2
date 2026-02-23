from .translation import router as translation_router
from .language import router as language_router
from .parse import router as parse_router
from .staffs import router as staffs_router
from .stores import router as stores_router
from .tasks import router as tasks_router
from .schedule import router as schedule_router
from .rooms import router as rooms_router

__all__ = [
    "translation_router",
    "language_router",
    "parse_router",
    "staffs_router",
    "stores_router",
    "tasks_router",
    "schedule_router",
    "rooms_router"
]
