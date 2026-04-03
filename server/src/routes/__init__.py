from .tags import router as tags_router
from .assets import router as assets_router
from .sources import router as sources_router
from .rules import router as rules_router
from .auto_fill import router as auto_fill_router
from .tag_names import router as tag_names_router

__all__ = ["tags_router", "assets_router", "sources_router", "rules_router", "auto_fill_router", "tag_names_router"]