import simple_async_requests


def construct_configs():
    configs = []
    for _ in range(300):
        configs.append({
            'method': 'get',
            'url': 'https://flash-the-slow-api.herokuapp.com/delay/2000',
            'headers': {},
        })
    return configs


def test():
    configs = construct_configs()
    simple_async_requests.make_parallel_async_requests(configs)


if __name__ == "__main__":
    test()
