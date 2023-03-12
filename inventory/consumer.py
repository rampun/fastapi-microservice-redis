# receives the event from redis stream

from main import redis, Product
import time

key = 'order_completed'
group = 'inventory-group'

try:
    redis.xgroup_create(key, group)
except:
    print('Group already exists!')


while True:
    try:
        results = redis.xreadgroup(group, key, {key: '>'}, None)

        if results != []:
            print(results)
            for result in results:
                order = result[1][0][1]
                product = Product.get(order['product_id'])

                if product:
                    product.quantity = int(
                        product.quantity) - int(order['quantity'])
                    product.save()
                else:
                    redis.xadd('order_refunded', order, '*')

    except Exception as e:
        print(str(e))
    time.sleep(1)
