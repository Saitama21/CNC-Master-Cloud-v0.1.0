from typing import Any

import aiohttp


class CNCAPIError(RuntimeError):
    pass


class CNCAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        timeout = aiohttp.ClientTimeout(total=20)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        if self.session is None:
            raise CNCAPIError("API client is not started")
        url = f"{self.base_url}{path}"
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise CNCAPIError(f"API {response.status}: {text}")
                return await response.json()
        except aiohttp.ClientError as exc:
            raise CNCAPIError(f"API unavailable: {exc}") from exc

    async def upsert_user(self, user: Any) -> dict[str, Any]:
        return await self.request(
            "POST",
            "/api/v1/users/upsert",
            json={
                "telegram_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "language_code": user.language_code,
            },
        )

    async def manufacturers(self) -> list[dict[str, Any]]:
        return await self.request("GET", "/api/v1/manufacturers")

    async def controllers(self, manufacturer_id: int | None = None) -> list[dict[str, Any]]:
        params = {"manufacturer_id": manufacturer_id} if manufacturer_id else None
        return await self.request("GET", "/api/v1/controllers", params=params)

    async def codes(self, query: str, controller_id: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "limit": 12}
        if controller_id:
            params["controller_id"] = controller_id
        return await self.request("GET", "/api/v1/codes/search", params=params)

    async def materials(self) -> list[dict[str, Any]]:
        return await self.request("GET", "/api/v1/materials")

    async def machines(self, telegram_id: int) -> list[dict[str, Any]]:
        return await self.request("GET", f"/api/v1/users/{telegram_id}/machines")

    async def machine(self, telegram_id: int, machine_id: int) -> dict[str, Any]:
        return await self.request("GET", f"/api/v1/users/{telegram_id}/machines/{machine_id}")

    async def create_machine(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.request("POST", "/api/v1/machines", json=payload)

    async def operations(self, telegram_id: int, machine_id: int) -> list[dict[str, Any]]:
        return await self.request(
            "GET",
            f"/api/v1/users/{telegram_id}/machines/{machine_id}/operations",
        )

    async def create_operation(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.request("POST", "/api/v1/operations", json=payload)
    async def tool_categories(self) -> dict[str, Any]:
        return await self.request("GET", "/api/v1/tools/categories")

    async def tools(
        self, *, category: str | None = None, operation: str | None = None,
        iso_group: str | None = None, query: str | None = None,
        page: int = 0, limit: int = 8,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"page": page, "limit": limit}
        if category:
            params["category"] = category
        if operation:
            params["operation"] = operation
        if iso_group:
            params["iso_group"] = iso_group
        if query:
            params["q"] = query
        return await self.request("GET", "/api/v1/tools", params=params)

    async def tool(self, tool_key: str) -> dict[str, Any]:
        return await self.request("GET", f"/api/v1/tools/{tool_key}")

    async def save_tool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.request("POST", "/api/v1/saved-tools", json=payload)

    async def saved_tools(self, telegram_id: int, machine_id: int) -> list[dict[str, Any]]:
        return await self.request(
            "GET", f"/api/v1/users/{telegram_id}/machines/{machine_id}/saved-tools"
        )

    async def create_process_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.request("POST", "/api/v1/process-plans", json=payload)

    async def process_plans(self, telegram_id: int, machine_id: int) -> list[dict[str, Any]]:
        return await self.request(
            "GET", f"/api/v1/users/{telegram_id}/machines/{machine_id}/process-plans"
        )

    async def consume(self, telegram_id: int, feature_key: str, *, consume: bool = True) -> dict[str, Any]:
        return await self.request(
            "POST", "/api/v1/usage/consume",
            json={"telegram_id": telegram_id, "feature_key": feature_key, "consume": consume},
        )

