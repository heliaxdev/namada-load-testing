from typing import List

from peewee import Model, CharField, IntegerField, fn, ForeignKeyField, SqliteDatabase

from src.constants import TOKENS

db: SqliteDatabase = SqliteDatabase('db.db')


class BaseModel(Model):
    class Meta:
        database = db


class Account(BaseModel):
    alias = CharField()
    address = CharField()
    token = CharField()
    amount = IntegerField()
    seed = IntegerField()

    @classmethod
    def create_account(cls, alias: str, address: str, token: str, amount: int, seed: int):
        return cls.create(alias=alias, address=address, token=token, amount=amount, seed=seed)

    @classmethod
    def get_random_account(cls, seed: int, tokens: List[str] = TOKENS):
        return cls.select().where(cls.seed == seed, cls.token << tokens).order_by(fn.Random()).get()

    @classmethod
    def get_random_account_with_positive_balance(cls, seed: int, tokens: List[str] = TOKENS):
        return cls.get_random_account_with_balance_greater_than(0, seed, tokens)

    @classmethod
    def get_random_account_with_balance_greater_than(cls, amount: int, seed: int, tokens: List[str] = TOKENS):
        return cls.select().where(cls.amount > amount, cls.token << tokens, cls.seed == seed).order_by(
            fn.Random()).get_or_none()

    @classmethod
    def get_by_address(cls, address: str, seed: int):
        return cls.select().where(cls.address == address, cls.seed == seed).get_or_none()

    @classmethod
    def update_account_balance(cls, alias: str, token: str, delta_amount: int, seed: int):
        user = cls.get(cls.alias == alias, cls.token == token, cls.seed == seed)
        old_amount = user.amount
        return cls.update({cls.amount: old_amount + delta_amount}).where(cls.alias == user.alias, cls.token == token,
                                                                         cls.seed == seed).execute()


class Validator(BaseModel):
    address = CharField()
    seed = IntegerField()

    @classmethod
    def create_validator(cls, address: str, seed: int):
        return cls.create(address=address, seed=seed)

    @classmethod
    def get_random_validator(cls, seed: int):
        return cls.select().where(cls.seed == seed).order_by(fn.Random()).get()

    @classmethod
    def get_by_address(cls, address: str, seed: int):
        return cls.select().where(cls.address == address, cls.seed == seed).get_or_none()


class Delegation(BaseModel):
    account_id = ForeignKeyField(Account, to_field='id')
    validator_id = ForeignKeyField(Validator, to_field='id')
    amount = IntegerField()
    epoch = IntegerField()
    seed = IntegerField()

    @classmethod
    def create_delegation(cls, account_id: int, validator_id: int, amount: int, epoch: int, seed: int):
        return cls.create(account_id=account_id, validator_id=validator_id, amount=amount, epoch=epoch, seed=seed)

    @classmethod
    def get_random_valid_delegation(cls, current_epoch: int, seed: int):
        return cls.select().where(cls.epoch < current_epoch, cls.amount < 50000, cls.seed == seed).order_by(
            fn.Random()).get_or_none()


class Withdrawal(BaseModel):
    account_id = ForeignKeyField(Account, to_field='id')
    validator_id = ForeignKeyField(Validator, to_field='id')
    amount = IntegerField()
    epoch = IntegerField()
    seed = IntegerField()

    @classmethod
    def create_withdrawal(cls, account_id: int, validator_id: int, amount: int, epoch: int, seed: int):
        return cls.get_or_create(account_id=account_id, validator_id=validator_id, amount=amount, epoch=epoch,
                                 seed=seed)

    @classmethod
    def get_random_withdrawable_withdraw(cls, current_epoch: int, seed: int):
        return cls.select().where(cls.epoch <= current_epoch, cls.seed == seed).order_by(fn.Random()).get_or_none()

    @classmethod
    def get_compatible_withdrawals(cls, delegator_id: int, validator_id: int, epoch: int, seed: int):
        return cls.select().where(
            cls.epoch <= epoch,
            cls.account_id == delegator_id,
            cls.validator_id == validator_id,
            cls.seed == seed
        ).order_by(cls.epoch).execute()

    @classmethod
    def delete_all(cls, seed: int):
        return cls.delete().where(cls.seed == seed).execute()


class Proposal(BaseModel):
    proposal_id = IntegerField()
    author = ForeignKeyField(Account, to_field='id')
    voting_start_epoch = IntegerField()
    voting_end_epoch = IntegerField()
    seed = IntegerField()

    @classmethod
    def create_proposal(cls, proposal_id: int, author_id: int, voting_start_epoch: int, voting_end_epoch: int,
                        seed: int):
        return cls.create(proposal_id=proposal_id, author_id=author_id, voting_start_epoch=voting_start_epoch,
                          voting_end_epoch=voting_end_epoch, seed=seed)

    @classmethod
    def total_proposals(cls, seed: int):
        return cls.select().where(cls.seed == seed).count()

    @classmethod
    def get_last_proposal_id(cls, seed: int):
        return cls.select(fn.MAX(cls.proposal_id)).where(cls.seed == seed).scalar()

    @classmethod
    def get_random_votable_proposal(cls, epoch: int, seed: int):
        return cls.select().where(
            cls.seed == seed,
            cls.voting_start_epoch <= epoch,
            cls.voting_end_epoch >= epoch - 1  # this is done to avoid an epoch change during vote transactions
        ).order_by(fn.Random()).get_or_none()


def connect():
    models = [Account, Validator, Delegation, Withdrawal, Proposal]
    db.connect()
    db.create_tables(models)
