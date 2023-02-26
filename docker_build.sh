TAG=$1
BINARY_URL=$2
CHAIN_ID=$3

docker build . -t namada-load-tester:$TAG --build-arg chain_id=$CHAIN_ID --build-arg binary_url=$BINARY_URL

# example: ./docker_build.sh 0.0.1 https://github.com/anoma/namada/releases/download/v0.14.1/namada-v0.14.1-Linux-x86_64.tar.gz public-testnet-4.0.16a35d789f4