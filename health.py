from __future__ import annotations

import logging

from aiohttp import web

log = logging.getLogger("sublate.health")


async def start_health_server(bot, port: int) -> web.AppRunner | None:
    app = web.Application()

    async def health(request: web.Request) -> web.Response:
        ready = bool(getattr(bot, "is_ready", lambda: False)())
        latency_ms = round((bot.latency or 0) * 1000) if ready else None
        body = {
            "status": "ok" if ready else "starting",
            "bot": str(bot.user) if ready and bot.user else None,
            "latency_ms": latency_ms,
            "guilds": len(bot.guilds) if ready else 0,
        }
        return web.json_response(body)

    async def root(request: web.Request) -> web.Response:
        return web.Response(text="Sublate Key — alive")

    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get("/healthz", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    try:
        await site.start()
        log.info("Health server listening on 0.0.0.0:%s", port)
        return runner
    except OSError as exc:
        log.warning("Health server failed to bind on port %s: %s", port, exc)
        await runner.cleanup()
        return None
