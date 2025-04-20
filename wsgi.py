import sys
import os
sys.path.insert(0, "/var/www/Coursero")
from app import create_app
application = create_app()