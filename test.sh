seq 100 | xargs -I{} -P50 curl -i -X POST \
http://localhost:8000/workflows/run