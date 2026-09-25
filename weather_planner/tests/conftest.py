import sys
import os

# Add weather_planner to the path so backend.services.scoring_service etc. are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
