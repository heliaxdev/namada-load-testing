from peewee import SqliteDatabase, Model, CharField, IntegerField, fn, ForeignKeyField

db: SqliteDatabase = SqliteDatabase('db.db')

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
        return cls.select().where(cls.amount > amount).order_by(fn.Random()).get()

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


class Delegation(BaseModel):
    account_id = ForeignKeyField(Account, to_field='id')
    validator_id = ForeignKeyField(Validator, to_field='id')
    amount = IntegerField()
    epoch = IntegerField()

    @classmethod
    def create_delegation(cls, account_id: int, validator_id: int, amount: int, epoch: int):
        return cls.create(account_id=account_id, validator_id=validator_id, amount=amount, epoch=epoch)


def connect():
    db.connect()
    db.create_tables([Account, Validator, Delegation])
