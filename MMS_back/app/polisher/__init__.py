"""Reply-draft polisher: rewrites the responder's draft before mod queue.

Member D's contribution. The polisher is a draft post-processor — it does not
generate replies, only refines them. Toggle with ``MMS_POLISHER_IMPL``.
"""

from app.polisher.base import Polisher
from app.polisher.factory import get_polisher

__all__ = ["Polisher", "get_polisher"]