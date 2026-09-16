"""
Ecosystem Core Engine v5.6 ULTRA - High-performance in-memory cache + background metrics + self-heal
"""
import asyncio, logging, datetime
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EcosystemCore")

class EcosystemEngine:
    def __init__(self):
        self.is_running = False
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime.datetime] = {}
        self.metrics = {"requests_total": 0, "cache_hits": 0, "auto_heals": 0, "start_time": None}
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self.is_running: return
        self.is_running = True
        self.metrics["start_time"] = datetime.datetime.utcnow().isoformat()
        logger.info("🚀 Suomi Master Core Engine V5.6 ULTRA Started!")
        self._task = asyncio.create_task(self._background_loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass

    async def _background_loop(self):
        while self.is_running:
            try:
                now = datetime.datetime.utcnow()
                expired = [k for k, exp in self.cache_ttl.items() if exp < now]
                for k in expired:
                    del self.cache[k]
                    del self.cache_ttl[k]
                await asyncio.sleep(30)
            except asyncio.CancelledError: break
            except Exception as e:
                logger.error(f"Error in background loop: {e}")
                await asyncio.sleep(10)

    def set_cache(self, key: str, data: Any, ttl_seconds: int = 300):
        self.cache[key] = data
        self.cache_ttl[key] = datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl_seconds)

    def get_cache(self, key: str) -> Optional[Any]:
        self.metrics["requests_total"] += 1
        if key in self.cache:
            if datetime.datetime.utcnow() < self.cache_ttl.get(key, datetime.datetime.utcnow()):
                self.metrics["cache_hits"] += 1
                return self.cache[key]
            else:
                del self.cache[key]
                if key in self.cache_ttl: del self.cache_ttl[key]
        return None

    def get_health_status(self) -> Dict[str, Any]:
        now = datetime.datetime.utcnow()
        uptime_sec = 0
        if self.metrics.get("start_time"):
            try:
                start = datetime.datetime.fromisoformat(self.metrics["start_time"])
                uptime_sec = (now - start).total_seconds()
            except: pass
        return {
            "engine_status": "ONLINE" if self.is_running else "OFFLINE",
            "active_cache_keys": len(self.cache),
            "metrics": self.metrics,
            "uptime_seconds": int(uptime_sec),
            "timestamp": now.isoformat(),
            "version": "5.6-ultra-core"
        }

core_engine = EcosystemEngine()
