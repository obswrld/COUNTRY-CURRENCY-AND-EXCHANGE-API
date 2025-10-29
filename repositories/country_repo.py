from datetime import datetime
from sqlalchemy import func, desc
from models.country_models import db, Country, RefreshInfo

class CountryRepo:

    @staticmethod
    def add_country(name, currency_code, exchange_rate, capital=None, region=None,
                    population=None, estimated_gdp=None, flag_url=None):
        new_country = Country(
            name=name,
            capital=capital,
            region=region,
            population=population,
            currency_code=currency_code,
            exchange_rate=exchange_rate,
            estimated_gdp=estimated_gdp,
            flag_url=flag_url,
            last_refreshed_at=datetime.utcnow()
        )
        db.session.add(new_country)
        db.session.commit()
        return new_country

    @staticmethod
    def get_all_countries(filters=None, sort=None):
        query = Country.query
        if filters:
            if filters.get("region"):
                query = query.filter(Country.region == filters["region"])
            if filters.get("currency"):
                query = query.filter(Country.currency_code == filters["currency"])
        if sort:
            if sort == "gdp_desc":
                query = query.order_by(desc(Country.estimated_gdp))
            elif sort == "gdp_asc":
                query = query.order_by(Country.estimated_gdp)
        return query.all()

    @staticmethod
    def get_country_by_id(country_id):
        return Country.query.get(country_id)

    @staticmethod
    def update_country(country_id, **kwargs):
        country = Country.query.get(country_id)
        if not country:
            return None
        for key, value in kwargs.items():
            if hasattr(country, key):
                setattr(country, key, value)
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
        existing_country = Country.query.filter(func.lower(Country.name) == func.lower(name)).first()
        if existing_country:
            for key in ["capital", "region", "population", "currency_code", "exchange_rate", "estimated_gdp", "flag_url"]:
                setattr(existing_country, key, country_data.get(key))
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
                last_refreshed_at=last_refreshed_at
            )
            db.session.add(new_country)
            return new_country

    @staticmethod
    def update_refresh_info(total_countries, last_refreshed_at):
        info = RefreshInfo.query.first()
        if not info:
            info = RefreshInfo(total_countries=total_countries, last_refreshed_at=last_refreshed_at)
        else:
            info.total_countries = total_countries
            info.last_refreshed_at = last_refreshed_at
        db.session.add(info)
        db.session.commit()
        return info

    @staticmethod
    def get_refreshed_info():
        return RefreshInfo.query.first()
