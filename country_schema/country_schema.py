from datetime import datetime

from marshmallow import Schema, fields, validates, ValidationError

class CountrySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    currency_code = fields.Str(required=True)
    exchange_rate = fields.Float(required=True)
    capital = fields.Str(required=False)
    region = fields.Str(required=False)
    population = fields.Int(required=False)
    estimated_gdp = fields.Float(required=False)
    flag_url = fields.Str(required=False)

    @validates("currency_code")
    def validate_currency_code(self, currency_code):
        if len(currency_code) != 3:
            raise ValidationError("currency_code must be 3 characters long")

    @validates("exchange_rate")
    def validate_exchange_rate(self, value):
        if value <= 0:
            raise ValidationError("exchange_rate must be greater than 0")