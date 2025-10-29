from datetime import datetime

from sqlalchemy import func

from models.country_models import db, Country, RefreshInfo


class CountryRepo:

    @staticmethod
    def add_country(name, currency_code, exchange_rate, capital, region, population, estimated_gdp, flag_url):
        new_country = Country(
            name=name,
            currency_code=currency_code,
            exchange_rate=exchange_rate,
            last_refreshed_at=datetime.utcnow()
        )
        db.session.add(new_country)
        db.session.commit()
        return new_country

    @staticmethod
    def get_all_countries():
        return Country.query.all()

    @staticmethod
    def get_country_by_id(country_id):
        return Country.query.get(country_id)

    @staticmethod
    def update_country(country_id, name=None, currency_code=None, exchange_rate=None):
        country = Country.query.get(country_id)
        if not country:
            return None
        if name:
            country.name = name
        if currency_code:
            country.currency_code = currency_code
        if exchange_rate:
            country.exchange_rate = exchange_rate
            country.last_refreshed_at = datetime.utcnow()
        db.session.commit()
        return country

    @staticmethod
    def delete_country(country_id):
        country = Country.query.get(country_id)
        if not country:
            return None
        db.session.delete(country)
        db.session.commit()
        return True

    @staticmethod
    def upsert_country_by_name(country_data, last_refreshed_at):
        name = country_data.get("name")
        if not name:
            return None
        existing_country = Country.query.filter(func.lower(Country.name) == func.lower()).first()
        if existing_country:
            existing_country.capital = country_data.get("capital")
            existing_country.region = country_data.get("region")
            existing_country.population = country_data.get("population")
            existing_country.currency_code = country_data.get("currency_code")
            existing_country.exchange_rate = country_data.get("exchange_rate")
            existing_country.estimated_gdp = country_data.get("estimated_gdp")
            existing_country.flag_url = country_data.get("flag_url")
            existing_country.last_refreshed_at = last_refreshed_at
            db.session.add(existing_country)
            return existing_country
        else:
            new_country = Country(
                name=name,
                capital=country_data.get("capital"),
                region=country_data.get("region"),
                population=country_data.get("population"),
                currency_code=country_data.get("currency_code"),
                exchange_rate=country_data.get("exchange_rate"),
                estimated_gdp=country_data.get("estimated_gdp"),
                flag_url=country_data.get("flag_url"),
                last_refreshed_at= datetime.utcnow()
            )
            db.session.add(new_country)
            return new_country

    @staticmethod
    def update_refresh_info(total_countries, last_refresh_at):
        info = RefreshInfo.query.first()
        if not info:
            info = RefreshInfo(total_countries=total_countries, last_refreshed_at=last_refresh_at)
            db.session.add(info)
        else:
            info.total_countries = total_countries
            info.last_refreshed_at = last_refresh_at
            db.session.add(info)
        return info

    @staticmethod
    def get_refreshed_info():
        return RefreshInfo.query.first()