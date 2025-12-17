from typing import TypeVar, Callable, List, Awaitable
import asyncio

TIn = TypeVar("TIn")   # input type
TOut = TypeVar("TOut")  # output type

class Throttling:
    def __init__(self, max_tasks: int):
        self.max_tasks = max_tasks
        self._semaphore = asyncio.Semaphore(max_tasks)

    async def submit(
        self,
        items: List[TIn],
        func: Callable[[TIn], Awaitable[TOut]]
    ) -> List[TOut]:
        async def worker(item: TIn) -> TOut:
            async with self._semaphore:
                return await func(item)

        tasks = [worker(item) for item in items]
        results = await asyncio.gather(*tasks)
        return list(results)