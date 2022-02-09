from starlette.requests import Request
from starlette.responses import Response
import aiohttp
import os
import json
import random


ROUTER_MAP = json.loads(os.environ.get('TRAFFIC_ROUTER_MAP') or '[]')
if not (isinstance(ROUTER_MAP, list) and len(ROUTER_MAP) > 0):
    raise ValueError('Environment Variable `TRAFFIC_ROUTER_MAP` is invalid.')

# TODO. backends healthy check once

# prepare router map
ROUTER_MAP = sorted(ROUTER_MAP, key=lambda x: x['weight'])
weight_sum = sum([r['weight'] for r in ROUTER_MAP])
subtotal = 0

for r in ROUTER_MAP:
    normalized_weight = r["weight"] / weight_sum
    r['normalized_weight_subtotal'] = normalized_weight + subtotal
    subtotal += normalized_weight


def select_host():
    random_number = random.random()
    for r in ROUTER_MAP:
        if random_number <= r['normalized_weight_subtotal']:
            return r['host']
    return ROUTER_MAP[-1]['host']


async def proxy_request(session: aiohttp.ClientSession, method,
                        headers, url, query_params, data):
    async with getattr(session, str.lower(method))(
                       url=url, headers=headers,
                       params=query_params, data=data) as response:
        return await response.read(), response


async def app(scope, receive, send):
    request = Request(scope, receive)
    async with aiohttp.ClientSession() as session:
        try:
            host = select_host()
            content, res = await proxy_request(
                session,
                headers=request.headers,
                method=request.method,
                url=host + request.url.path,
                query_params=request.query_params,
                data=await request.body()
            )
            response = Response(
                content=content,
                status_code=res.status,
                headers=res.headers,
                media_type=res.content_type
                )
        except Exception as e:
            response = Response(
                content=json.dumps({"error": str(e)}),
                status_code=500,
                media_type='application/json'
            )
        await response(scope, receive, send)
