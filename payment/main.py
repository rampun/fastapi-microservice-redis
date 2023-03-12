from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection,  HashModel
from starlette.requests import Request
import requests
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*'],
)

# This should be a different database; infact it could be any other database server mysql, mariadb etc
redis = get_redis_connection(
    host="redis-16559.c212.ap-south-1-1.ec2.cloud.redislabs.com",
    port=16559,
    password="aEGnyOucMtOu82vLVZLitoSaaVFNUQM0",
    decode_responses=True
)


class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str  # pending, completed, refunded

    class Meta:
        database = redis


@app.get('/orders/{pk}')
def get(pk: str):
    return Order.get(pk)


@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):  # id, quantity
    body = await request.json()

    # make a get request to inventory microservice
    req = requests.get(
        'http://localhost:8000/products/%s' % body['id'], timeout=3000)
    product = req.json()

    # make a order create now
    order = Order(
        product_id=body['id'],
        price=product['price'],
        fee=0.2*product['price'],
        total=1.2*product['price'],
        quantity=product['quantity'],
        status='pending'
    )

    order.save()

    background_tasks.add_task(order_completed, order)

    return order


def order_completed(order: Order):
    time.sleep(10)
    order.status = 'completed'
    order.save()
