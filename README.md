# Namada Load Testing

A configurable load testing tool for Namada networks.

## Setup

- Install `poetry`
- Checkout the project
- Build a config (follow the example in `configs/config.yaml.example`)
- Run `poetry install`

## Run

- `./run.sh $namada_folder $binary_folder $config_path [--fail-fast]`

## Transaction types

- `Faucet`
- `Transfer`
- `Delegate`
- `Unbond`
- `Withdraw`
- `InitProposal`
- `VoteProposal`