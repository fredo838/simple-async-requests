import tqdm
import asyncio
import httpx


async def producer(queue, tqdm_context, payloads):
    for payload in payloads:
        try:
            await queue.put(payload)
            tqdm_context.total += 1
            tqdm_context.refresh()
        except Exception as ex:
            print(ex)


async def consumer(queue, tqdm_context, succesfull, failed, client):
    while True:
        try:
            config = await queue.get()
            res = None
            try:
                res = await client.request(**config)
                res.raise_for_status()
            except Exception as ex:
                if isinstance(res, type(None)):
                    print("Req Failed", ex)
                else:
                    print("Req Failed", ex, res.text)
                raise ex
            if not isinstance(res, type(None)):
                if res.status_code != 200:
                    failed.append(res)
                else:
                    succesfull.append(res)
            else:
                failed.append(res)
        except Exception as ex:
            print("Other unhandled Exception", ex)
            failed.append(None)
            raise ex

        queue_size = queue.qsize()
        finished_total = len(succesfull) + len(failed)
        tqdm_context.set_postfix({
            '✓': len(succesfull),
            '✖': len(failed),
            'sent': finished_total,
            'queued': queue_size
        })
        tqdm_context.update(1)
        queue.task_done()


async def execute(client: httpx.AsyncClient, urls, concurrency):
    queue = asyncio.Queue()
    tqdm_context = tqdm.tqdm(total=0, ascii=True, ncols=120)
    succesfull = []
    failed = []
    producers = [asyncio.create_task(producer(queue, tqdm_context, urls)) for _ in range(1)]
    consumers = [asyncio.create_task(consumer(
        queue, tqdm_context, succesfull, failed, client=client
    )) for _ in range(concurrency)]
    await asyncio.gather(*producers)
    await queue.join()
    tqdm_context.close()
    for c in consumers:
        c.cancel()
    return succesfull, failed


async def async_make_parallel_async_requests(configs, concurrency):
    async with httpx.AsyncClient(timeout=None, http2=False) as client:
        return await execute(client, configs, concurrency=concurrency)


def make_parallel_async_requests(configs, concurrency=20):
    res = asyncio.run(async_make_parallel_async_requests(configs, concurrency=concurrency))
    return res
