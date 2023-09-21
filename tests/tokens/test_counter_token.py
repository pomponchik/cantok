from threading import Thread

import pytest

from cantok.tokens.counter_token import CounterToken


@pytest.mark.parametrize(
    'iterations',
    [
        0,
        1,
        5,
        15,
    ],
)
def test_counter(iterations):
    token = CounterToken(iterations)
    counter = 0

    while not token.cancelled:
        counter += 1

    assert counter == iterations


def test_counter_less_than_zero():
    with pytest.raises(ValueError):
        CounterToken(-1)


@pytest.mark.parametrize(
    'iterations',
    [
        10_000,
        50_000,
        1_000,
    ],
)
@pytest.mark.parametrize(
    'number_of_threads',
    [
        1,
        2,
        5,
    ],
)
def test_race_condition_for_counter(iterations, number_of_threads):
    results = []
    token = CounterToken(iterations)

    def decrementer(number):
        counter = 0
        while not token.cancelled:
            counter += 1
        results.append(counter)

    threads = [Thread(target=decrementer, args=(iterations / number_of_threads, )) for _ in range(number_of_threads)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    result = sum(results)
    print(result)
    assert result == iterations
