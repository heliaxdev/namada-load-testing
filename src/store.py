import os

from peewee import SqliteDatabase, Model, CharField, IntegerField, fn, ForeignKeyField

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
    def get_random_account_with_positive_balance(cls):
        return cls.get_random_account_with_balance_grater_than(0)

    @classmethod
    def get_random_account_with_balance_grater_than(cls, amount: int):
        return cls.select().where(cls.amount > amount).order_by(fn.Random()).get_or_none()

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
        return cls.select().where(
                (cls.epoch < current_epoch) &
                (cls.amount < 10000)
        ).order_by(fn.Random()).get_or_none()


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
    grace_epoch = IntegerField()


def connect():
    db.connect()
    db.create_tables([Account, Validator, Delegation, Withdrawal, Proposal])
