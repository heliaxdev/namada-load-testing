BASE_DIRECTORY=${1}
BASE_BINARY=${2:-namada}
CONFIG_NAME=${3:-config.yaml}
FAIL_FAST=${4:--no-fail-fast}

DB_NAME=$(echo $RANDOM | md5sum | head -c 20; echo;)
export DB_NAME

if [[ "$FAIL_FAST" == "--fail-fast" ]]
then
  poetry run python3 main.py --base-directory $BASE_DIRECTORY --base-binary $BASE_BINARY --config-path configs/"$CONFIG_NAME" --fail-fast
else
  poetry run python3 main.py --base-directory $BASE_DIRECTORY --base-binary $BASE_BINARY --config-path configs/"$CONFIG_NAME"
fi