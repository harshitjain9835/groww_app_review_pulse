import os
import logging
from typing import Dict, Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class PulseMCPClient:
    """
    Manages connections to the remote FastAPI MCP-style server.
    """
    def __init__(self):
        self.base_url = os.getenv("FASTAPI_SERVER_URL", "https://web-production-4b16a.up.railway.app").rstrip('/')
        self.api_key = os.getenv("MCP_API_KEY", "")
        if not self.api_key:
            logger.warning("MCP_API_KEY is not set. API calls will fail if the server requires it.")
        self.client = httpx.AsyncClient(headers={"X-API-Key": self.api_key}, timeout=30.0)
        
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invokes an endpoint on the FastAPI server."""
        logger.info(f"Calling endpoint '/{tool_name}' on '{self.base_url}'...")
        
        try:
            response = await self.client.post(f"{self.base_url}/{tool_name}", json=arguments)
            response.raise_for_status()
            try:
                return response.json()
            except Exception:
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {e}")
            raise

    async def close(self):
        """Cleans up the HTTP client session."""
        await self.client.aclose()
        logger.info("Closed HTTP client session.")