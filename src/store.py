import os
from typing import List

from peewee import SqliteDatabase, Model, CharField, IntegerField, fn, ForeignKeyField

from src.constants import TOKENS

db_name = os.getenv('DB_NAME', 'db.db')
db: SqliteDatabase = SqliteDatabase(db_name)


class BaseModel(Model):
    class Meta:
        database = db


class Account(BaseModel):
    alias = CharField()
    address = CharField()
    token = CharField()
    amount = IntegerField()

    @classmethod
    def create_account(cls, alias: str, address: str, token: str, amount: int):
        return cls.create(alias=alias, address=address, token=token, amount=amount)

    @classmethod
    def get_random_account(cls):
        return cls.select().order_by(fn.Random()).get()

    @classmethod
    def get_random_account_with_positive_balance(cls, tokens: List[str] = TOKENS):
        return cls.get_random_account_with_balance_grater_than(0, tokens)

    @classmethod
    def get_random_account_with_balance_grater_than(cls, amount: int, tokens: List[str] = TOKENS):
        return cls.select().where(cls.amount > amount, cls.token << tokens).order_by(fn.Random()).get_or_none()

    @classmethod
    def get_by_address(cls, address: str):
        return cls.select().where(cls.address == address).get_or_none()

    @classmethod
    def update_account_balance(cls, alias: str, token: str, delta_amount: int):
        user = cls.get(cls.alias == alias)
        old_amount = user.amount
        return cls.update({cls.amount: old_amount + delta_amount}).where((cls.alias == user.alias) & (cls.token == token)).execute()


class Validator(BaseModel):
    address = CharField()

    @classmethod
    def create_validator(cls, address: str):
        return cls.create(address=address)

    @classmethod
    def get_random_validator(cls):
        return cls.select().order_by(fn.Random()).get()

    @classmethod
    def get_by_address(cls, address: str):
        return cls.select().where(cls.address == address).get_or_none()


class Delegation(BaseModel):
    account_id = ForeignKeyField(Account, to_field='id')
    validator_id = ForeignKeyField(Validator, to_field='id')
    amount = IntegerField()
    epoch = IntegerField()

    @classmethod
    def create_delegation(cls, account_id: int, validator_id: int, amount: int, epoch: int):
        return cls.create(account_id=account_id, validator_id=validator_id, amount=amount, epoch=epoch)

    @classmethod
    def get_random_valid_delegation(cls, current_epoch: int):
        return cls.select().where(cls.epoch < current_epoch, cls.amount < 50000).order_by(fn.Random()).get_or_none()


class Withdrawal(BaseModel):
    account_id = ForeignKeyField(Account, to_field='id')
    validator_id = ForeignKeyField(Validator, to_field='id')
    amount = IntegerField()
    epoch = IntegerField()

    @classmethod
    def create_withdrawal(cls, account_id: int, validator_id: int, amount: int, epoch: int):
        return cls.get_or_create(account_id=account_id, validator_id=validator_id, amount=amount, epoch=epoch)

    @classmethod
    def get_random_withdrawable_withdraw(cls, current_epoch: int):
        return cls.select().where(cls.epoch <= current_epoch).order_by(fn.Random()).get_or_none()

    @classmethod
    def get_compatible_withdrawals(cls, delegator_id: int, validator_id: int, epoch: int):
        return cls.select().where(
            cls.epoch <= epoch,
            cls.account_id == delegator_id,
            cls.validator_id == validator_id
        ).order_by(cls.epoch).execute()

    @classmethod
    def delete_all(cls):
        return cls.delete().execute()


class Proposal(BaseModel):
    proposal_id = IntegerField(primary_key=True)
    author = ForeignKeyField(Account, to_field='id')
    voting_start_epoch = IntegerField()
    voting_end_epoch = IntegerField()

    @classmethod
    def create_proposal(cls, proposal_id: int, author_id: int, voting_start_epoch: int, voting_end_epoch: int):
        return cls.create(proposal_id=proposal_id, author_id=author_id, voting_start_epoch=voting_start_epoch, voting_end_epoch=voting_end_epoch)

    @classmethod
    def total_proposals(cls):
        return cls.select().count()

    @classmethod
    def get_last_proposal_id(cls):
        return cls.select(fn.MAX(cls.proposal_id)).scalar()

    @classmethod
    def get_random_votable_proposal(cls, epoch: int):
        return cls.select().where(
            cls.voting_start_epoch <= epoch,
            cls.voting_end_epoch >= epoch, # this is done to avoid an epoch change during vote transactions
        ).order_by(fn.Random()).get_or_none()


def connect():
    db.connect()
    db.create_tables([Account, Validator, Delegation, Withdrawal, Proposal])
