"""API router 패키지."""

from . import health  # noqa: F401
from . import auth_token as auth  # noqa: F401
from . import auth_google  # noqa: F401
from . import coach  # noqa: F401
from . import admin  # noqa: F401 
from . import billing  # noqa: F401 
from . import referral  # noqa: F401 
from . import user  # noqa: F401
from . import chat  # noqa: F401
from . import performance  # noqa: F401 
from . import assets  # noqa: F401 
from . import auth_mock  # noqa: F401 – exported for test environment 