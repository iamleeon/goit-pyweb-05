import aiohttp
import asyncio
import json
import platform
import sys
from datetime import datetime, timedelta


class HttpError(Exception):
    pass


async def request(api_url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    raise HttpError(f"Error: {response.status} for {api_url}")
        except aiohttp.ClientError as err:
            raise HttpError(f'Connection error: {api_url}', str(err))


async def currency_exchange_rate_for_date(date: str):
    url = 'https://api.privatbank.ua/p24api/exchange_rates?date=' + date
    try:
        result_from_api = await request(url)
        filtered_result = {
            "EUR": {
                "sale": None,
                "purchase": None
            },
            "USD": {
                "sale": None,
                "purchase": None
            }
        }

        if additional_currency:
            filtered_result[additional_currency] = {
                "sale": None,
                "purchase": None
            }

        for rate in result_from_api.get("exchangeRate", []):
            if rate.get("currency") in filtered_result:
                filtered_result[rate.get("currency")] = {
                    "sale": rate.get("saleRate"),
                    "purchase": rate.get("purchaseRate")
                }

        return {date: filtered_result}

    except HttpError as err:
        print(err)
        return None


async def main(date: int, additional_currency: str):
    today = datetime.today()
    tasks = []

    for day in range(date):
        date = (today - timedelta(days=day)).strftime('%d.%m.%Y')
        tasks.append(currency_exchange_rate_for_date(date))

    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    valid_currencies = ["AUD", "AZN", "BYN", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP", "GEL", "ILS",
                        "KZT", "NOK", "PLN", "SEK", "TMT", "UAH", "USD", "UZS"]

    try:
        requested_days = sys.argv[1]
        requested_days = int(requested_days)
        if requested_days == 1:
            print(f'The currency exchange rate for today:')
        elif 2 <= requested_days <= 10:
            print(f'The currency exchange rate for the last ' + str(requested_days) + ' days:')
        elif requested_days > 10:
            print(f'The currency exchange rate can be shown for a maximum of the last 10 days.')
            sys.exit(0)
        else:
            print(f'Unexpected argument. Please use a number between 1 and 10.')
            sys.exit(0)

        if len(sys.argv) > 2:
            additional_currency = sys.argv[2].upper()
            if additional_currency not in valid_currencies:
                print(f"Unsupported currency: {additional_currency}. "
                      f"List of the supported currencies: {valid_currencies}.\n")
                additional_currency = None
        else:
            additional_currency = None

    except ValueError:
        print(f'Unexpected argument. Please use a number between 1 and 10.')
        sys.exit(0)

    r = asyncio.run(main(requested_days, additional_currency))
    result_str = json.dumps(r, indent=4)
    print(result_str)
