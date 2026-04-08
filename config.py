import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
PBIX_TEMPLATE_PATH = os.getenv("PBIX_TEMPLATE_PATH", "pbix/template.pbix")
