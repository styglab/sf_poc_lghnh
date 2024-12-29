## summary
스노우플레이크 LG생활건강 POC
Cortext Analyst를 활용한 자연어 쿼리

## build
docker build --tag sf_poc_lghnh:1.0.0 .

## run
### run (run background mode)
docker run -d -p 8000:8000 --name sf_poc_lghnh sf_poc_lghnh:1.0.0
### run (run background and dev mode)
docker run -d -p 8000:8000 --name sf_poc_lghnh -v .:/app sf_poc_lghnh:1.0.0

