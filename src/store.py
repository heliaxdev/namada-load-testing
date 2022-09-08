from peewee import SqliteDatabase, Model, CharField, IntegerField, fn

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
        return cls.select().where(cls.amount > 0).order_by(fn.Random()).get()

    @classmethod
    def update_account_balance(cls, alias: str, token: str, delta_amount: int):
        user = cls.get(cls.alias == alias)
        old_amount = user.amount
        return cls.update({cls.amount: old_amount + delta_amount}).where((cls.alias == user.alias) & (cls.token == token)).execute()


class Validator(BaseModel):
    account = CharField()

    @classmethod
    def create_validator(cls, account: str):
        return cls.create(account=account)


def connect():
    db.connect()
    db.create_tables([Account, Validator])
