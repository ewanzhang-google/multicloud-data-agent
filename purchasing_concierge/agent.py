from .purchasing_agent import PurchasingAgent
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

root_agent = PurchasingAgent(
    remote_agent_addresses=[
        os.getenv("REMOTE_AGENT_URL", "http://localhost:9999"),
    ]
).create_agent()
