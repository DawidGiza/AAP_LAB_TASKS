import queue
import threading

q = queue.Queue()
MAX = 20


def render():
    for i in range(MAX):
        print(f"[PRODUCENT] Dodano: {i}")
        q.put(i)
    q.put(None)


def consumer_even():
    while True:
        item = q.get()

        if item is None:
            break

        if item % 2 == 0:
            print(f"[PARZYSTE] {item}")

        q.task_done()


def consumer_odd():
    while True:
        item = q.get()

        if item is None:
            break

        if item % 2 == 1:
            print(f"[NIEPARZYSTE] {item}")

        q.task_done()

t_producer = threading.Thread(target=producer)
t_even = threading.Thread(target=consumer_even)
t_odd = threading.Thread(target=consumer_odd)

t_producer.start()
t_even.start()
t_odd.start()

t_producer.join()
t_even.join()
t_odd.join()

print("Koniec programu.")