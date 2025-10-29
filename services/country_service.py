import os
import io
import random
from datetime import datetime
import requests
from models.country_models import Country
from repositories.country_repo import CountryRepo
from models.country_models import db

from repositories.country_repo import CountryRepo
from country_schema.country_schema import CountrySchema

COUNTRIES_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"

CACHE_DIR = "cache"
SUMMARY_IMAGE_PATH = os.path.join(CACHE_DIR, "summary.png")

class CountryService:

    @staticmethod
    def create_country(data):
        try:
            validated_data = CountrySchema().load(data)
        except Exception as e:
            return {'error': str(e)}, 400

        try:
            country = CountryRepo.add_country(
                name = validated_data['name'],
                currency_code = validated_data['currency_code'].upper(),
                exchange_rate = validated_data['exchange_rate'],
                capital = validated_data.get('capital'),
                region = validated_data.get('region'),
                population = validated_data.get('population'),
                estimated_gdp = validated_data.get('estimated_gdp'),
                flag_url = validated_data.get('flag_url')
            )
            return {
                "message":"Country created successfully",
                "country": CountrySchema.dump(country)
            }, 201
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def get_all_countries():
        try:
            countries = CountryRepo.get_all_countries()
            return [
                {"id": c.id, "name": c.name, "currency_code": c.currency_code, "exchange_rate": c.exchange_rate}
                for c in countries
            ], 200
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def get_country_by_id_service(country_id):
        try:
            country_entry = CountryRepo.get_country_by_id(country_id)
            if not country_entry:
                return {"error": "Country not found"}, 404
            return {
                "id": country_entry.id,
                "name": country_entry.name,
                "currency_code": country_entry.currency_code,
                "exchange_rate": country_entry.exchange_rate,
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def update_country_service(country_id, data):
        try:
            validated_data = CountrySchema().load(data, partial=True)
        except Exception as e:
            return {'error': str(e)}, 400

        try:
            country = CountryRepo.update_country(
                country_id = country_id,
                **validated_data
            )
            if not country:
                return {"error": "Country not found"}, 404
            return {
                "message":"Country updated successfully",
                "country": CountrySchema.dump(country)
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500
        

    @staticmethod
    def delete_country_service(country_id):
        try:
            country_entry = CountryRepo.get_country_by_id(country_id)
            if not country_entry:
                return {"error": "Country not found"}, 404
            CountryRepo.delete_country(country_id)
            return {"message": "Deleted country successfully"}, 200
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def refresh_countries():
        try:
            countries_resp = requests.get(COUNTRIES_API, timeout=15)
            countries_resp.raise_for_status()
            countries_data = countries_resp.json()
        except Exception as e:
            return {"error":"External data source unavailable", "details":f" Could not fetch data from restcountries API: {str(e)}"}, 503

        try:
            exchange_resp = requests.get(EXCHANGE_API, timeout=15)
            exchange_resp.raise_for_status()
            exchange_json = exchange_resp.json()
            rates = exchange_json.get('rates') or {}
        except Exception as e:
            return {"error": "External data source unavailable", "details":F"Could not fetch data from API:{str(e)}"}, 503

        rates_map = {str(k).upper(): v for k, v in (rates.items() if isinstance(rates, dict) else[])}

        last_refreshed = datetime.datetime.now()