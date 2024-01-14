import json
from asyncio import Lock
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from time import time


class Updateable(object):
    def update(self, new):
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass(slots=True)
class Client(Updateable):
    name: str
    ip: str
    active: bool = True
    time: float = field(default_factory=time)

    def __repr__(self) -> str:
        return f"Client<{self.name}>"


class ClientManager:
    def __init__(self):
        self._lock = Lock()
        self._db: dict[str, Client] = {}

    async def add(self, name: str, ip: str):
        async with self._lock:
            self._db[name] = Client(name=name, ip=ip)

    async def update(self, name: str, data: dict):
        async with self._lock:
            self._db[name].update(data)

    async def clients(self) -> list[Client]:
        async with self._lock:
            return deepcopy(list(self._db.values()))

    async def dumps(self) -> str:
        return json.dumps([asdict(client) for client in await self.clients()])

    async def merge(self, raw_db: list[dict]):
        async with self._lock:
            db = [Client(**client) for client in raw_db]
            for client in db:
                if self._db[client.name].time > client.time:
                    continue
                self._db[client.name].update(asdict(client))
