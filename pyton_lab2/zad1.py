import requests
import time
import concurrent.futures

CAT_API_URL = "https://catfact.ninja/fact"

def get_cat_fact():
    return requests.get(CAT_API_URL).json().get('fact')


#sekwencyjnie
start = time.time()

facts_seq = []
for _ in range(20):
    fact = get_cat_fact()
    facts_seq.append(fact)

end = time.time()
seq_time = end - start

print("Sekwencyjnie:")
print(f"Czas: {seq_time:.2f} s\n")

#rownolegle
start = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(lambda _: get_cat_fact(), range(20))
    facts_threaded = list(results)

end = time.time()
thread_time = end - start

print(f"Czas: {thread_time:.2f} s\n")
