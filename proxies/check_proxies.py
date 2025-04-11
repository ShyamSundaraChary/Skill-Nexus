import requests

TEST_URL = "https://httpbin.org/ip"

with open("proxies.txt", "r") as f:
    proxy_list = f.read().splitlines()

working_proxies = []

for proxy in proxy_list:
    try:
        res = requests.get(TEST_URL, proxies={"http": proxy, "https": proxy}, timeout=5)
        if res.status_code == 200:
            print(f"✅ Working Proxy: {proxy}")
            working_proxies.append(proxy)
    except:
        pass  # Ignore bad proxies

# Save working proxies
with open("working_proxies_filtered.txt", "w") as f:
    f.write("\n".join(working_proxies))
