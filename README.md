# Namada Load Testing

A configurable load testing tool for Namada networks.

## Setup

- Install `poetry`
- Checkout the project
- Build a config (follow the example in `configs/config.yaml.example`)
- Run `poetry install`
- Run `poetry run python3 main.py --help`

## Run

- `poetry run python3 main.py --seeds [list of seeds space separated] --base-directory [base namada directory] --base-binary [path to namada binary (relative to --base-directory)] --config-path [path to config] (--fail-fast) (--json)`

A process will be spawned for each seed in the list, sending transactions concurrently.

### example:

- `poetry run python3 main.py --seeds 8 9 10 --base-directory /Heliax/namada --base-binary ./target/debug/namada --config-path configs/config.yaml.example`

## Transaction types

- `Faucet`
- `Transfer`
- `Delegate`
- `Unbond`
- `Withdraw`
- `InitProposal`
- `VoteProposal`

## Logs

A folder per seed is created in the `logs` folder. Inside that folder, a dump of the all command result is saved.