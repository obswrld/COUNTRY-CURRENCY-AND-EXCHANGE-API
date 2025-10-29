import os
import random
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont

from models.country_models import db, Country
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
                name=validated_data['name'],
                currency_code=validated_data['currency_code'].upper(),
                exchange_rate=validated_data['exchange_rate'],
                capital=validated_data.get('capital'),
                region=validated_data.get('region'),
                population=validated_data.get('population'),
                estimated_gdp=validated_data.get('estimated_gdp'),
                flag_url=validated_data.get('flag_url')
            )
            return {"message": "Country created successfully", "country": CountrySchema().dump(country)}, 201
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def get_all_countries():
        try:
            from flask import request
            region = request.args.get("region")
            currency = request.args.get("currency")
            sort = request.args.get("sort")

            filters = {}
            if region:
                filters["region"] = region
            if currency:
                filters["currency"] = currency

            countries = CountryRepo.get_all_countries(filters=filters, sort=sort)
            response = [
                {
                    "id": c.id,
                    "name": c.name,
                    "capital": c.capital,
                    "region": c.region,
                    "population": c.population,
                    "currency_code": c.currency_code,
                    "exchange_rate": c.exchange_rate,
                    "estimated_gdp": c.estimated_gdp,
                    "flag_url": c.flag_url,
                    "last_refreshed_at": c.last_refreshed_at.isoformat() if c.last_refreshed_at else None
                } for c in countries
            ]
            return response, 200
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def get_country_by_id_service(country_id):
        try:
            country = CountryRepo.get_country_by_id(country_id)
            if not country:
                return {"error": "Country not found"}, 404
            return CountrySchema().dump(country), 200
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def update_country_service(country_id, data):
        try:
            validated_data = CountrySchema().load(data, partial=True)
        except Exception as e:
            return {'error': str(e)}, 400
        try:
            country = CountryRepo.update_country(country_id, **validated_data)
            if not country:
                return {"error": "Country not found"}, 404
            return {"message": "Country updated successfully", "country": CountrySchema().dump(country)}, 200
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def delete_country_service(country_id):
        try:
            country = CountryRepo.get_country_by_id(country_id)
            if not country:
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
            return {"error":"External data source unavailable", "details":f"Could not fetch data from RestCountries API: {str(e)}"}, 503

        try:
            exchange_resp = requests.get(EXCHANGE_API, timeout=15)
            exchange_resp.raise_for_status()
            rates = exchange_resp.json().get('rates') or {}
            rates_map = {str(k).upper(): v for k, v in rates.items()}
        except Exception as e:
            return {"error":"External data source unavailable", "details":f"Could not fetch data from Exchange API: {str(e)}"}, 503

        last_refreshed = datetime.utcnow()
        total = 0
        try:
            with db.session.begin():
                for c in countries_data:
                    name = c.get('name')
                    capital = c.get('capital')
                    region = c.get('region')
                    population = c.get('population')
                    flag_url = c.get('flag')
                    currencies = c.get('currencies') or []

                    if currencies and isinstance(currencies, list) and len(currencies) > 0:
                        first = currencies[0] if isinstance(currencies[0], dict) else {}
                        currency_code = first.get("code")
                        currency_code = currency_code.upper() if currency_code else None
                    else:
                        currency_code = None

                    exchange_rate = None
                    estimated_gdp = None
                    try:
                        pop_val = int(population) if population else 0
                    except:
                        pop_val = 0

                    if currency_code:
                        exchange_rate = rates_map.get(currency_code)
                        if exchange_rate:
                            multiplier = random.randint(1000, 2000)
                            estimated_gdp = (pop_val * multiplier) / exchange_rate
                        else:
                            exchange_rate = None
                            estimated_gdp = None
                    else:
                        estimated_gdp = 0

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
            # update refresh info
            CountryRepo.update_refresh_info(total, last_refreshed)
        except Exception as e:
            return {"error": "Internal server error", "details": str(e)}, 500

        # generate image
        try:
            CountryService.generate_summary_image(last_refreshed)
        except Exception as e:
            return {"message": "Countries refreshed successfully", "total": total, "warning": f"image generation failed: {str(e)}"}, 200

        return {"message": "Countries refreshed successfully", "total": total}, 200

    @staticmethod
    def generate_summary_image(last_refreshed):
        os.makedirs(CACHE_DIR, exist_ok=True)
        total = db.session.query(Country).count()
        top5 = Country.query.filter(Country.estimated_gdp.isnot(None)).order_by(Country.estimated_gdp.desc()).limit(5).all()

        width, height = 1000, 600
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_text = ImageFont.truetype("arial.ttf", 20)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        y = 30
        draw.text((40, y), "Countries Summary", font=font_title, fill=(0, 0, 0))
        y += 50
        draw.text((40, y), f"Last refreshed at (UTC): {last_refreshed.isoformat()}", font=font_text, fill=(0, 0, 0))
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
            return {"total_countries": 0, "last_refreshed_at": None}, 200
        return {"total_countries": info.total_countries or 0,
                "last_refreshed_at": info.last_refreshed_at.isoformat() if info.last_refreshed_at else None}, 200

    @staticmethod
    def get_summary_image_path():
        if os.path.exists(SUMMARY_IMAGE_PATH):
            return SUMMARY_IMAGE_PATH
        return None
