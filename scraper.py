import requests
import os
import psycopg2
from dotenv import load_dotenv
import time

load_dotenv()


def extrage_abonati(conn):
    """Trage din baza de date lista tuturor ID urilor care s-au abonat."""
    with conn.cursor() as cur:
        cur.execute("SELECT chat_id FROM abonati_telegram;")
        randuri = cur.fetchall()
        # Returnam lista de ID-uri [123, 456] sau lista goala []
        return [rand[0] for rand in randuri]


def adauga_abonat_nou(conn, chat_id):
    """Verifica daca ID ul exista deja. Daca nu, il adauga in tabel."""
    with conn.cursor() as cur:
        cur.execute("SELECT chat_id FROM abonati_telegram WHERE chat_id = %s;", (chat_id,))
        exista = cur.fetchone()

        if not exista:
            cur.execute("INSERT INTO abonati_telegram (chat_id) VALUES (%s);", (chat_id,))
            conn.commit()
            print(f"Utilizator nou adaugat in agenda: {chat_id}")


def trimite_notificare_telegram(conn, mesaj):
    token = os.getenv("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    lista_abonati = extrage_abonati(conn)

    if not lista_abonati:
        print("Nu avem niciun abonat in baza de date.")
        return

    print(f"Trimit mesaj catre {len(lista_abonati)} abonati...")

    for chat_id in lista_abonati:
        payload = {
            "chat_id": chat_id,
            "text": mesaj
        }
        try:
            requests.post(url, json=payload)
            time.sleep(0.1)  # Pauza
        except Exception as e:
            print(f"Eroare la trimiterea pe Telegram pt {chat_id}: {e}")


def citeste_abonati_noi_telegram(conn):
    """
    Verifica daca cineva a trimis vreun mesaj bot ului recent (ex: /start)
    si adauga ID-ul in baza de date.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        raspuns = requests.get(url).json()
        if raspuns.get("ok"):
            mesaje = raspuns.get("result", [])
            for mesaj in mesaje:
                # Extragem id-ul chat-ului
                try:
                    chat_id = mesaj["message"]["chat"]["id"]
                    adauga_abonat_nou(conn, chat_id)
                except KeyError:
                    # In caz ca update ul nu e un mesaj de text
                    continue
    except Exception as e:
        print(f"Eroare la citirea inbox-ului Telegram: {e}")

def gaseste_cartier(titlu, descriere):
    # Unim titlul si descrierea si le facem cu litere mici ca sa cautam usor oriunde in text
    text_complet = f"{titlu} {descriere}".lower()

    strazi_spre_cartiere = {
        '9 mai': 'Centru',
        'unirii': 'Centru',
        'nicolae balcescu': 'Centru',
        'stefan cel mare': 'Nord',
        'militari': 'Nord',
        'neagoe voda': 'Cornisa',
        'milcov': 'Sud',
        'aeroportului': 'Aeroport'
    }

    # Cautam intai strazile in textul anuntului
    for strada, cartier_asociat in strazi_spre_cartiere.items():
        if strada in text_complet:
            return cartier_asociat

    # Daca nu gasim o strada din lista, cautam numele cartierului direct
    cartiere_bacau = [
        'mioritei', 'nord', 'sud', 'centru', 'cornisa', 'bistrita lac',
        'gara', 'republicii', 'letea', 'ura', 'aviatori',
        'alecu russo', 'banca nationala', 'energiei', 'marasti', 'tache'
    ]

    for cartier in cartiere_bacau:
        if cartier in text_complet:
            return cartier.title()

    return 'Necunoscut'

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def extrage_date_de_pe_site():
    print("Ne conectam la API-ul site-ului...")
    import requests

    cookies = {
        'onap': '1a0578830f0x17c126ff-1-1a0578830f0x17c126ff-48-1788176998309',
        'lqstatus': '1788176018726|||||0|1788174938726|0',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Aug+31+2026+14%3A18%3A38+GMT%2B0300+(Eastern+European+Summer+Time)&version=202601.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=V10%3A0%2C&consentId=81d294fb-aa0c-4ee8-87a2-41ed89d8a06f&interactionCount=1&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0%2Cgad%3A0&intType=5&crTime=1788174938360&geolocation=RO%3BBC&AwaitingReconsent=false',
        'PHPSESSID': '94o8dk7g8mqt3u5pg6iotls4lr',
        'OTAdditionalConsentString': '2~~dv.89.320.959.1109.1421.1423.1659.1985.1987.2008.2072.2135.2275.2322.2465.2501.2627.2833.2958.2999.3028.3225.3226.3231.3235.3236.3237.3238.3240.3244.3250.3251.3253.3257.3260.3270.3272.3288.3290.3292.3293.3296.3299.3300.3306.3307.3309.3314.3315.3316.3318.3324.3328.3330.3331.3531.3731.3831.4131.4531.4631.4731.4831.5231.6931.7235.7831.7931.8931.10231.10631.10831.11031.11531.13632.13731.14034.14133.14237.15731.16831.16931.21233.23031.25131.25931.26031.26631.27731.27831.28031.28731.29631.30532.32531.33931.34231.34631.36831.39131.39531.40632.41131.41531.43631.43731.43831.45931.47232.47531.48131.49231.49332.49431.50831.52831.54231.56831.56931.57131.57231',
        'OptanonAlertBoxClosed': '2026-08-31T11:15:38.166Z',
        'eupubconsent-v2': 'CQpzgIgQpzgIgAcABBROCuFwAAAAAAAAAAYgAAAAAAFBACYADgASAEHAI4ATQBKwCZQE2gKQAWEAsQBf4DFgGQgNTAbQA24BugEBAkECACgAKgAcAA8ACCAF4AagA8ACKAEwAKoAbwA_ACEgEMARIAjgBNACtAGAAMMAZYA2QBzgDuAHtAPsA_QCAAEUgIuAjABGgCTAEpgJ-AoMBUQFXALmAXoAxQBogDaAG4AOIAe0BDsCPQJEATsAocBR4CkQFNgLYAXIAuwBeYDDYGRgZIAycBlwDMwGcwNXA1kBsYDbwG6gOTAcuBC4dBEAAXABQAFQAOAAggBcAGoAPAAmABVAC6AG8AP0AhgCJAE0AKMAVoAwABhgDRAGyAOcAdwA9oB9gH7ARQBGICOgJMASmAn4CgwFRAVcAsQBc4C8gL0AYoA2gBuADiAHmAPaAfYBDoCL4EegSIAmQBOwCh4FHgUgApsBVgCxQFsALdAXJAuwC7QF5gL6AYaAx6BkYGSQMnAyqBlgGXAMzAZyA02Bq4GsANvAbqA4sByYDlxwCSABwAHgAXABIAGgARwAywByAEAgIOAhABHACaAHSAQgAlYBMQCZQE2gKTAV2AsQBagC_wGLAMhAZMA0YBqYDXgG0ANsAbcA3QBx4DloHOgc-BAQhAZAAWABQAFwANQAqgBvAGAAOcAdwBFACUgFBgKiAq4BcwDFAG0AR6AqwBYoC0QFyALsAZGAycBnJAAiAA8ANAAywByAEcALEAm0BSYCxAGeANTAbYA24BugDlgHPgQEJQHQAFgAUAA4ADwAJgAVYBDAESAI4AUYArQBgADZAH5AVEBVwC5gGKAQ6Ai-BHoEiAKPAWKAtgBdgC84GRgZIAycBnIDWAG3kgCAAFwB3AEAAIOARwBKwCYgE2gKTAX-AxYBlgDPAG6AOWAgIUgbAALgAoACoAHAAQAA0AB4AEwAKoAfoBDAESAKMAVoAwABogDZAHOAO-AfgB-gEWAIxAR0BIgCUgFBgKiAq4BcwC8gGKANoAbgA9oB9gEOgIvgR6BIgCdgFDgKQAU2AqwBYoC2AFyALtAXmAvoBhsDIwMkAZPAywDLgGcwNYA1kBt4DdQHJlADYAFwASAAuABkAI4AZYA5AB3AD7AIAAQcAsQBrwDtgH_ATEAm0BUgCuwGLAMmAZ4A1MBrwDdAHLAQEAAA.YAAAAAAAAAAA.IKENR3G_fbXlj-TZ16bpkeYxf99hrrsQxBgbIsm4FyLvW7JwC32EbJEwapiIKmRIAu3DBIQFtHAjUBUChKIAVLTDMaEyEoTNKJ6BEiDMRYyJQCEhum4BDWQCZYsrvZkdwmR-N6dr-2dzyy5hnn3KtfuS1UJicKYcgAAAAAAAAAAAAAEAQAAAAFAAAAAAIAAAAAAAAAAAAgAAAAAAAF-QAAAAABAA',
        'laquesis': 'eupp-4152@a#platf-2733716@a#platf-2733973@a#platf-28743@b#rnk-3021@a',
        'laquesisff': 'aut-1425#aut-388#buy-2279#buy-2489#carparts-312#cars-78563#dat-2874#dc-83#de-2724#decision-256#decision-657#do-3481#euads-3204#euonb-114#eus-1773#f8nrp-1779#jobs-7611#kuna-307#mart-1341#oec-1238#oesx-2798#oesx-4295#olxmd-2105#pay-287#pos-1043#pos-2021#pos-2216#posting-1419#posting-1638#rm-28#rm-707#rm-780#rm-824#rm-852#sd-3192#srt-1346#srt-1434#srt-1593#srt-1758#srt-684#uacc-529#udp-1535#up-90',
        'deviceGUID': 'd72a2eb1-7820-42c7-89be-69e519e52b79',
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Sec-Fetch-Site': 'same-origin',
        'Accept-Language': 'ro',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Sec-Fetch-Mode': 'cors',
        'Origin': 'https://www.olx.ro',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.5.2 Safari/605.1.15',
        # 'Content-Length': '7226',
        'Referer': 'https://www.olx.ro/imobiliare/apartamente-garsoniere-de-vanzare/bacau/?currency=EUR&search%5Border%5D=filter_float_price:asc',
        # 'Cookie': 'onap=1a0578830f0x17c126ff-1-1a0578830f0x17c126ff-48-1788176998309; lqstatus=1788176018726|||||0|1788174938726|0; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Aug+31+2026+14%3A18%3A38+GMT%2B0300+(Eastern+European+Summer+Time)&version=202601.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=V10%3A0%2C&consentId=81d294fb-aa0c-4ee8-87a2-41ed89d8a06f&interactionCount=1&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0%2Cgad%3A0&intType=5&crTime=1788174938360&geolocation=RO%3BBC&AwaitingReconsent=false; PHPSESSID=94o8dk7g8mqt3u5pg6iotls4lr; OTAdditionalConsentString=2~~dv.89.320.959.1109.1421.1423.1659.1985.1987.2008.2072.2135.2275.2322.2465.2501.2627.2833.2958.2999.3028.3225.3226.3231.3235.3236.3237.3238.3240.3244.3250.3251.3253.3257.3260.3270.3272.3288.3290.3292.3293.3296.3299.3300.3306.3307.3309.3314.3315.3316.3318.3324.3328.3330.3331.3531.3731.3831.4131.4531.4631.4731.4831.5231.6931.7235.7831.7931.8931.10231.10631.10831.11031.11531.13632.13731.14034.14133.14237.15731.16831.16931.21233.23031.25131.25931.26031.26631.27731.27831.28031.28731.29631.30532.32531.33931.34231.34631.36831.39131.39531.40632.41131.41531.43631.43731.43831.45931.47232.47531.48131.49231.49332.49431.50831.52831.54231.56831.56931.57131.57231; OptanonAlertBoxClosed=2026-08-31T11:15:38.166Z; eupubconsent-v2=CQpzgIgQpzgIgAcABBROCuFwAAAAAAAAAAYgAAAAAAFBACYADgASAEHAI4ATQBKwCZQE2gKQAWEAsQBf4DFgGQgNTAbQA24BugEBAkECACgAKgAcAA8ACCAF4AagA8ACKAEwAKoAbwA_ACEgEMARIAjgBNACtAGAAMMAZYA2QBzgDuAHtAPsA_QCAAEUgIuAjABGgCTAEpgJ-AoMBUQFXALmAXoAxQBogDaAG4AOIAe0BDsCPQJEATsAocBR4CkQFNgLYAXIAuwBeYDDYGRgZIAycBlwDMwGcwNXA1kBsYDbwG6gOTAcuBC4dBEAAXABQAFQAOAAggBcAGoAPAAmABVAC6AG8AP0AhgCJAE0AKMAVoAwABhgDRAGyAOcAdwA9oB9gH7ARQBGICOgJMASmAn4CgwFRAVcAsQBc4C8gL0AYoA2gBuADiAHmAPaAfYBDoCL4EegSIAmQBOwCh4FHgUgApsBVgCxQFsALdAXJAuwC7QF5gL6AYaAx6BkYGSQMnAyqBlgGXAMzAZyA02Bq4GsANvAbqA4sByYDlxwCSABwAHgAXABIAGgARwAywByAEAgIOAhABHACaAHSAQgAlYBMQCZQE2gKTAV2AsQBagC_wGLAMhAZMA0YBqYDXgG0ANsAbcA3QBx4DloHOgc-BAQhAZAAWABQAFwANQAqgBvAGAAOcAdwBFACUgFBgKiAq4BcwDFAG0AR6AqwBYoC0QFyALsAZGAycBnJAAiAA8ANAAywByAEcALEAm0BSYCxAGeANTAbYA24BugDlgHPgQEJQHQAFgAUAA4ADwAJgAVYBDAESAI4AUYArQBgADZAH5AVEBVwC5gGKAQ6Ai-BHoEiAKPAWKAtgBdgC84GRgZIAycBnIDWAG3kgCAAFwB3AEAAIOARwBKwCYgE2gKTAX-AxYBlgDPAG6AOWAgIUgbAALgAoACoAHAAQAA0AB4AEwAKoAfoBDAESAKMAVoAwABogDZAHOAO-AfgB-gEWAIxAR0BIgCUgFBgKiAq4BcwC8gGKANoAbgA9oB9gEOgIvgR6BIgCdgFDgKQAU2AqwBYoC2AFyALtAXmAvoBhsDIwMkAZPAywDLgGcwNYA1kBt4DdQHJlADYAFwASAAuABkAI4AZYA5AB3AD7AIAAQcAsQBrwDtgH_ATEAm0BUgCuwGLAMmAZ4A1MBrwDdAHLAQEAAA.YAAAAAAAAAAA.IKENR3G_fbXlj-TZ16bpkeYxf99hrrsQxBgbIsm4FyLvW7JwC32EbJEwapiIKmRIAu3DBIQFtHAjUBUChKIAVLTDMaEyEoTNKJ6BEiDMRYyJQCEhum4BDWQCZYsrvZkdwmR-N6dr-2dzyy5hnn3KtfuS1UJicKYcgAAAAAAAAAAAAAEAQAAAAFAAAAAAIAAAAAAAAAAAAgAAAAAAAF-QAAAAABAA; laquesis=eupp-4152@a#platf-2733716@a#platf-2733973@a#platf-28743@b#rnk-3021@a; laquesisff=aut-1425#aut-388#buy-2279#buy-2489#carparts-312#cars-78563#dat-2874#dc-83#de-2724#decision-256#decision-657#do-3481#euads-3204#euonb-114#eus-1773#f8nrp-1779#jobs-7611#kuna-307#mart-1341#oec-1238#oesx-2798#oesx-4295#olxmd-2105#pay-287#pos-1043#pos-2021#pos-2216#posting-1419#posting-1638#rm-28#rm-707#rm-780#rm-824#rm-852#sd-3192#srt-1346#srt-1434#srt-1593#srt-1758#srt-684#uacc-529#udp-1535#up-90; deviceGUID=d72a2eb1-7820-42c7-89be-69e519e52b79',
        'Sec-Fetch-Dest': 'empty',
        'x-client': 'DESKTOP',
        'Priority': 'u=3, i',
    }

    json_data = {
        'query': 'query ListingSearchQuery(\n  $searchParameters: [SearchParameter!] = []\n  $fetchPayAndShip: Boolean = false\n  $searchOptions: SearchOptions\n) {\n  clientCompatibleListings(searchParameters: $searchParameters, searchOptions: $searchOptions) {\n    __typename\n    ... on ListingSuccess {\n      __typename\n      data {\n        _nodeId\n        id\n        location {\n          city {\n            id\n            name\n            normalized_name\n            _nodeId\n          }\n          district {\n            id\n            name\n            normalized_name\n            _nodeId\n          }\n          region {\n            id\n            name\n            normalized_name\n            _nodeId\n          }\n        }\n        last_refresh_time\n        delivery {\n          rock {\n            active\n            mode\n            offer_id\n          }\n        }\n        created_time\n        category {\n          id\n          type\n          _nodeId\n        }\n        contact {\n          courier\n          chat\n          name\n          negotiation\n          phone\n        }\n        business\n        omnibus_pushup_time\n        photos {\n          link\n          height\n          rotation\n          width\n        }\n        promotion {\n          highlighted\n          top_ad\n          options\n          premium_ad_page\n          urgent\n          b2c_ad_page\n          seller_badge_x_years_with_olx\n        }\n        protect_phone\n        shop {\n          subdomain\n        }\n        title\n        status\n        url\n        user {\n          id\n          uuid\n          _nodeId\n          about\n          b2c_business_page\n          banner_desktop\n          banner_mobile\n          company_name\n          created\n          is_online\n          last_seen\n          logo\n          logo_ad_page\n          name\n          other_ads_enabled\n          photo\n          seller_type\n          social_network_account_type\n          verification {\n            status\n          }\n          businessProfiles {\n            services {\n              icon {\n                url\n                id\n              }\n              location {\n                city\n              }\n              businessName\n              foundationYear\n              templateName\n            }\n          }\n        }\n        offer_type\n        params {\n          key\n          name\n          type\n          value {\n            __typename\n            ... on GenericParam {\n              key\n              label\n            }\n            ... on CheckboxesParam {\n              label\n              checkboxParamKey: key\n            }\n            ... on PriceParam {\n              value\n              type\n              negotiable\n              label\n              currency\n              converted_value\n              converted_currency\n              arranged\n              budget\n            }\n            ... on SalaryParam {\n              from\n              to\n              arranged\n              converted_currency\n              converted_from\n              converted_to\n              currency\n              gross\n              type\n            }\n            ... on DynamicMultiChoiceCompatibilityListParam {\n              __typename\n            }\n            ... on ErrorParam {\n              message\n            }\n          }\n        }\n        description\n        external_url\n        partner {\n          code\n        }\n        map {\n          lat\n          lon\n          radius\n          show_detailed\n          zoom\n        }\n        safedeal {\n          allowed_quantity\n          weight_grams\n        }\n        valid_to_time\n        isGpsrAvailable\n        payAndShip @include(if: $fetchPayAndShip) {\n          sellerPaidDeliveryEnabled\n        }\n      }\n      metadata {\n        filter_suggestions {\n          clear_on_change\n          break_line\n          category\n          label\n          name\n          type\n          unit\n          values {\n            label\n            value\n          }\n          constraints {\n            type\n          }\n          search_label\n          option {\n            ranges\n            order\n            orderForSearch\n            fakeCategory\n          }\n        }\n        filters {\n          clear_on_change\n          break_line\n          category\n          label\n          name\n          type\n          unit\n          values {\n            label\n            value\n          }\n          constraints {\n            type\n          }\n          search_label\n          option {\n            ranges\n            order\n            orderForSearch\n            fakeCategory\n          }\n        }\n        x_request_id\n        search_id\n        total_elements\n        visible_total_count\n        source\n        search_suggestion {\n          url\n          type\n          changes {\n            category_id\n            city_id\n            distance\n            district_id\n            query\n            region_id\n            strategy\n            excluded_category_id\n          }\n        }\n        facets {\n          category {\n            id\n            count\n            label\n            url\n          }\n          category_id_1 {\n            count\n            id\n            label\n            url\n          }\n          category_id_2 {\n            count\n            id\n            label\n            url\n          }\n          category_without_exclusions {\n            count\n            id\n            label\n            url\n          }\n          category_id_3_without_exclusions {\n            id\n            count\n            label\n            url\n          }\n          city {\n            count\n            id\n            label\n            url\n          }\n          district {\n            count\n            id\n            label\n            url\n          }\n          owner_type {\n            count\n            id\n            label\n            url\n          }\n          region {\n            id\n            count\n            label\n            url\n          }\n          scope {\n            id\n            count\n            label\n            url\n          }\n        }\n        new\n        promoted\n      }\n      links {\n        first {\n          href\n        }\n        next {\n          href\n        }\n        previous {\n          href\n        }\n        self {\n          href\n        }\n      }\n    }\n    ... on ListingError {\n      __typename\n      error {\n        code\n        detail\n        status\n        title\n        validation {\n          detail\n          field\n          title\n        }\n      }\n    }\n  }\n}\n',
        'variables': {
            'searchParameters': [
                {
                    'key': 'offset',
                    'value': '0',
                },
                {
                    'key': 'limit',
                    'value': '40',
                },
                {
                    'key': 'category_id',
                    'value': '907',
                },
                {
                    'key': 'region_id',
                    'value': '3',
                },
                {
                    'key': 'city_id',
                    'value': '34959',
                },
                {
                    'key': 'currency',
                    'value': 'EUR',
                },
                {
                    'key': 'sort_by',
                    'value': 'filter_float_price:asc',
                },
                {
                    'key': 'suggest_filters',
                    'value': 'true',
                },
                {
                    'key': 'sl',
                    'value': '1a0578830f0x17c126ff',
                },
            ],
            'fetchPayAndShip': False,
            'searchOptions': None,
        },
    }

    toate_anunturile = []
    offset = 0
    limit = 40
    pagina = 1

    # Incepem bucla de paginare
    while True:
        print(f"Procesam pagina {pagina} ...")

        # Actualizam valoarea 'offset' dinamic, in interiorul JSON-ului
        for param in json_data['variables']['searchParameters']:
            if param['key'] == 'offset':
                param['value'] = str(offset)

        try:
            # Facem cererea catre OLX
            response = requests.post(
                'https://www.olx.ro/apigateway/graphql',
                cookies=cookies,
                headers=headers,
                json=json_data
            )

            date_brute = response.json()
            lista_anunturi = date_brute['data']['clientCompatibleListings']['data']

            # Daca lista este goala, am terminat toate paginile
            if not lista_anunturi:
                print("Am ajuns la finalul paginilor pe OLX!")
                break

            # Procesam ofertele de pe aceasta pagina
            for item in lista_anunturi:
                try:
                    titlu = item.get('title', 'Fara titlu')

                    descriere = item.get('description', '')

                    oras = item['location']['city']['name']

                    # Incercam intai sa luam cartierul oficial din API
                    cartier = item['location'].get('district', {}).get('name', 'Necunoscut') if item['location'].get(
                        'district') else 'Necunoscut'

                    # Daca API-ul ne zice "Necunoscut", cautam in titlu
                    if cartier == 'Necunoscut':
                        cartier = gaseste_cartier(titlu, descriere)

                    pret = 0
                    suprafata = 0

                    for param in item.get('params', []):
                        if param.get('key') == 'price':
                            valoare_pret = param.get('value', {}).get('value', 0)
                            if valoare_pret:
                                pret = int(valoare_pret)
                        elif param.get('key') == 'm':
                            valoare_mp = param.get('value', {}).get('label', '0').split(' ')[0]
                            if valoare_mp.isdigit():
                                suprafata = int(valoare_mp)

                    if pret == 0:
                        continue

                    if suprafata < 15 or suprafata > 400:
                        continue

                    pret_pe_mp = pret / suprafata

                    # Daca pretul pe metru patrat sare de 4000, inseamna clar ca pretul total a fost pus in Lei.
                    if pret_pe_mp > 4000:
                        pret = int(pret / 4.97)

                    # Recalculam pretul pe mp dupa posibila conversie
                    pret_pe_mp_corectat = pret / suprafata

                    # Daca pretul pe mp este aberant de mic (sub 400 Euro/mp), pretul a fost trecut ca euro in rubrica lei, si convertit gresit la euro
                    if pret_pe_mp_corectat < 400:
                        pret = int(pret * 4.97)

                    anunt = {
                        "id_anunt": str(item['id']),
                        "url": item['url'],
                        "oras": oras,
                        "cartier": cartier,
                        "suprafata_mp": suprafata,
                        "pret": pret
                    }
                    toate_anunturile.append(anunt)


                except Exception as e:
                    continue

            # Pregatim citirea pentru urmatoarea pagina
            offset += limit
            pagina += 1

            # Oprim scriptul 3 secunde
            time.sleep(3)

        except Exception as e:
            print(f"Eroare la paginarea paginii {pagina}: {e}")
            break  # Iesim din bucla daca pica conexiunea

    print(f"EXTRAGERE COMPLETA! Am strans in total {len(toate_anunturile)} anunturi.")
    return toate_anunturile


def salveaza_in_baza_de_date(anunturi):
    """
    LOAD & TRANSFORM: Salvarea datelor fara a pierde istoricul
    """
    conn = get_connection()
    cursor = conn.cursor()

    anunturi_noi_azi = 0
    scaderi_pret_azi = 0

    for anunt in anunturi:
        # Verificam daca apartamentul exista deja in tabelul static
        cursor.execute("SELECT id_apartament FROM apartamente WHERE id_anunt_original = %s", (anunt["id_anunt"],))
        rezultat = cursor.fetchone()

        if rezultat is None:
            # Apartamentul este nou. Il inseram in tabelul 'apartamente'
            anunturi_noi_azi += 1

            cursor.execute("""
                INSERT INTO apartamente (id_anunt_original, url_anunt, oras, cartier, suprafata_mp)
                VALUES (%s, %s, %s, %s, %s) RETURNING id_apartament;
            """, (anunt["id_anunt"], anunt["url"], anunt["oras"], anunt["cartier"], anunt["suprafata_mp"]))

            id_apartament = cursor.fetchone()[0]
            print(f"Apartament nou gasit si salvat: {anunt['cartier']} ({anunt['pret']}€)")
        else:
            # Apartamentul exista deja. Ii luam id-ul
            id_apartament = rezultat[0]
            print(f"Apartament existent gasit in baza de date: {anunt['cartier']}")

        # Verificam care a fost ultimul pret pentru acest apartament
        cursor.execute("""
            SELECT pret FROM istoric_preturi 
            WHERE id_apartament = %s 
            ORDER BY data_inregistrarii DESC LIMIT 1;
        """, (id_apartament,))
        ultimul_pret_inregistrat = cursor.fetchone()

        # Adaugam un rand nou doar daca pretul s-a schimbat
        if ultimul_pret_inregistrat is None or ultimul_pret_inregistrat[0] != anunt["pret"]:
            cursor.execute("""
                INSERT INTO istoric_preturi (id_apartament, pret)
                VALUES (%s, %s);
            """, (id_apartament, anunt["pret"]))

            if ultimul_pret_inregistrat is not None:
                pret_vechi = ultimul_pret_inregistrat[0]
                pret_nou = anunt["pret"]

                if pret_nou < pret_vechi:
                    scaderi_pret_azi += 1
                    print(f"SCADERE DE PRET! De la {pret_vechi}€ la {pret_nou}€")

                    # Construim si trimitem alerta DOAR la scadere de pret
                    mesaj_alerta = (
                        f"SCADERE DE PRET!\n\n"
                        f"Cartier: {anunt['cartier']}\n"
                        f"Suprafata: {anunt['suprafata_mp']} mp\n"
                        f"Pret vechi: {pret_vechi}€\n"
                        f"Pret nou: {pret_nou}€\n\n"
                        f"Link: {anunt['url']}"
                    )
                    trimite_notificare_telegram(mesaj_alerta)
                else:
                    print(f"Pretul a CRESCUT de la {pret_vechi}€ la {pret_nou}€.")
            else:
                print(f"Pret initial setat: {anunt['pret']}€")
        else:
            print(f"Pretul a ramas neschimbat ({anunt['pret']}€).")

    # Trimitere raport zilnic
    cursor.execute("SELECT COUNT(*) FROM apartamente;")
    total_apartamente = cursor.fetchone()[0]

    mesaj_raport = (
        f"Buna dimineata! Iata raportul imobiliar de azi:\n\n"
        f"Total oferte monitorizate: {total_apartamente}\n"
        f"Anunturi noi aparute azi: {anunturi_noi_azi}\n"
        f"Scaderi de pret azi: {scaderi_pret_azi}\n\n"
        f"Intra pe Radar pentru detalii:\n"
        f"https://alexandruachillef-flip-finder-dashboard-k6l87l.streamlit.app"
    )

    # Trimitem raportul ca o concluzie a scriptului
    trimite_notificare_telegram(mesaj_raport)
    print("Raport zilnic trimis pe Telegram cu succes!")

    # Salvam modificarile
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("Pornim scraper-ul Flip Finder...")

    conn = get_connection()
    citeste_abonati_noi_telegram(conn)
    conn.close()

    date_extrase = extrage_date_de_pe_site()

    salveaza_in_baza_de_date(date_extrase)

    print("Rulare completa!")