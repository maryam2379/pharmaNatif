from urllib.parse import urlparse, parse_qs

from httplib2 import Response

url = "/health?id=5&nom=Ali"
parsed_url = urlparse(url)
print(parsed_url)
query_params = parse_qs(parsed_url.query)
print(query_params)
print("path:", parsed_url.path)
print("query:", parsed_url.query)

