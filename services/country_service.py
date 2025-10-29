import os
import io
import random
from datetime import datetime
from tkinter import Image

import requests
from PIL import Image, ImageDraw, ImageFont

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

        try:
            with db.session.begin():
                total = 0
                for c in countries_data:
                    name = c.get('name')
                    capital = c.get('capital')
                    region = c.get('region')
                    population = c.get('population')
                    flag_url = c.get('flag_url')
                    currencies = c.get('currencies') or []
                    if currencies and isinstance(currencies, list) and len(currencies) > 0:
                        first = currencies[0]
                        currency_code = first.get("code") if isinstance(first, dict) else None
                        if currency_code:
                            currency_code = currency_code.upper()
                    else:
                        currency_code = None

                    exchange_rate = None
                    estimated_gdp = None

                    if not currency_code:
                        exchange_rate = None
                        estimated_gdp = 0
                    else:
                        rate = rates_map.get(currency_code)
                        if rate is None:
                            exchange_rate = None
                            estimated_gdp = None
                        else:
                            exchange_rate = float(rate)
                            try:
                                pop_val = int(population) if population is not None else 0
                            except Exception:
                                pop_val = 0
                                multiplier = random.randint(1000, 2000)

                                if exchange_rate == 0:
                                    estimated_gdp = None
                                else:
                                    estimated_gdp = (pop_val * multiplier) / exchange_rate

                    country_payload = {
                        "name": name,
                        "capital": capital,
                        "region": region,
                        "population": population,
                        "currency_code": currency_code,
                        "exchange_rate": exchange_rate,
                        "estimated_gdp": estimated_gdp,
                        "flag_url": flag_url
                    }
                    CountryRepo.upsert_country_by_name(country_payload, last_refreshed)
                    total += 1

                CountryRepo.upsert_country_by_name(total, last_refreshed)
        except Exception as e:
            return {"error": "Internal server error", "details": str(e)}, 500

        try:
            CountryService.generate_summary_image(last_refreshed)
        except Exception as e:
            return {"message": "Countries refreshed successfully", "total": total, "warning":f"image generation failed: {str(e)}"}, 200
        return {"message": "Countries refreshed successfully", "total": total}, 200


    @staticmethod
    def generate_summary_image(last_refreshed):
        os.makedirs(CACHE_DIR, exist_ok=True)
        total = db.session.query(Country).count()
        top5 = Country.query.filter(
            Country.estimated_gdb is not None).order_by(Country.estimated_gdb.desc()).limit(5).all()
        width, height = 1000, 600
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_text = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        y = 30
        draw.text((40, y), "Countries Summary", font=font_title, fill=(0, 0, 0))
        y += 50
        draw.text((40, y), f"Last refreshed at (UTC): {last_refreshed.isoformat()} ", font=font_text, fill=(0, 0, 0))
        y += 30
        draw.text((40, y), f"Total countries: {total}", font=font_text, fill=(0, 0, 0))
        y += 40
        draw.text((40, y), "Top 5 by estimated GDP:", font=font_text, fill=(0, 0, 0))
        y += 30

        if not top5:
            draw.text((60, y), "No GDP data available", font=font_text, fill=(128, 0, 0))
        else:
            for i, c in enumerate(top5, start=1):
                gdp_str = f"{c.estimated_gdp:,.2f}" if c.estimated_gdp is not None else "N/A"
                draw.text((60, y), f"{i}. {c.name} — {gdp_str}", font=font_text, fill=(0, 0, 0))
                y += 26


        img.save(SUMMARY_IMAGE_PATH, format="PNG")

    @staticmethod
    def get_status():
        info = CountryRepo.get_refreshed_info()
        if not info:
            return {"total_countries": 0, "last_refreshed": None}, 200
        return {"total_countries" : info.total_countries or 0, "last_refreshed": info.last_refreshed.isoformat() if info.last_refresh else None}, 200

    @staticmethod
    def get_summary_image_path():
        if os.path.exists(SUMMARY_IMAGE_PATH):
            return SUMMARY_IMAGE_PATH
        return None

