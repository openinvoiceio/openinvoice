import moneyed


def country_to_currency(country_code: str) -> str:
    for currency in moneyed.CURRENCIES.values():
        if country_code in currency.country_codes:
            return currency.code
    raise ValueError(f"Currency not found for country code {country_code}")
