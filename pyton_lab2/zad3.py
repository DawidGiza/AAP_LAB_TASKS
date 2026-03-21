def is_prime(n):
    if n <= 1: return False
    if n == 2: return True
    if n % 2 == 0: return False
    i = 3
    while i * i <= n:
        if n % i == 0: return False
        i += 2
    return True

def find_primes(start, end):
    return [num for num in range(start, end) if is_prime(num)]

def calculate_power_sum(n):
    return sum(n**i for i in range(1, 101))


import multiprocessing
import time

MIN = 1
MAX = 10000

if __name__ == "__main__":
    numbers = range(MIN, MAX)

    start = time.time()

    with multiprocessing.Pool() as pool:
        results = pool.map(calculate_power_sum, numbers)

    end = time.time()

    print(f"Czas wykonania: {end - start:.2f} s")
    print(f"Liczba wyników: {len(results)}")