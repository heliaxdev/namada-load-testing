BASE_DIRECTORY=${1}
BASE_BINARY=${2:-namada}
CONFIG_NAME=${3:-config.yaml}
FAIL_FAST=${4:--no-fail-fast}

DB_NAME="$(echo $RANDOM | md5sum | head -c 20; echo;).db"
export DB_FULLNAME

echo "Using database ${DB_NAME}..."

if [[ "$FAIL_FAST" == "--fail-fast" ]]
then
  echo "Running fail fast mode..."
  poetry run python3 main.py --base-directory $BASE_DIRECTORY --base-binary $BASE_BINARY --config-path configs/"$CONFIG_NAME" --fail-fast
else
  echo "Running without fail fast mode..."
  poetry run python3 main.py --base-directory $BASE_DIRECTORY --base-binary $BASE_BINARY --config-path configs/"$CONFIG_NAME"
fi