TAG=$1
BINARY_URL=$2
CHAIN_ID=$3

docker build . -t namada-load-tester:$TAG --build-arg chain_id=$CHAIN_ID --build-arg binary_url=$BINARY_URL