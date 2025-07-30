import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines
from dotenv import load_dotenv
import os
from purchasing_concierge.agent import root_agent

load_dotenv()

PROJECT_ID = os.getenv("GCLOUD_PROJECT_ID")
LOCATION = os.getenv("GCLOUD_LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

adk_app = reasoning_engines.AdkApp(
    agent=root_agent,
)

remote_app = agent_engines.create(
    agent_engine=adk_app,
    requirements="./requirements.txt",
    extra_packages=[
        "./purchasing_concierge",
    ],
    env_vars={
        "GOOGLE_GENAI_USE_VERTEXAI": os.environ["GOOGLE_GENAI_USE_VERTEXAI"],
        "PIZZA_SELLER_AGENT_URL": os.environ["PIZZA_SELLER_AGENT_URL"],
        "BURGER_SELLER_AGENT_URL": os.environ["BURGER_SELLER_AGENT_URL"],
    }
)

print(f"Deployed remote app resource: {remote_app.resource_name}")
