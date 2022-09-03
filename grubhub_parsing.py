#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import re
import sys
import threading
import traceback
import requests
from bs4 import BeautifulSoup

global_tries = 0


class MultiThreadClass(threading.Thread):

    def __init__(self, className, methodName, methodDescription, methodResultVariableName, *methodArgs):
        threading.Thread.__init__(self)
        self.className = className
        self.methodName = methodName
        self.methodDescription = methodDescription
        self.methodResultVariableName = methodResultVariableName
        self.methodArgs = methodArgs
        self.methodResults = None

    def run(self):
        method = getattr(self.className, self.methodName)
        result = method(*self.methodArgs)
        self.methodResults = result


class crawl_website:
    def crawl_restaurant(self, restaurant_link, session, restaurants_details, category_products_details,
                         products_topping_details, client_id):
        global global_tries
        restaurant_header = ['Restaurant Name', 'Restaurant Address', 'Restaurant City', 'Restaurant state',
                             'Restaurant Stars', 'Restaurant Review Count']
        if restaurant_link[-1] == '/':
            restaurant_id = restaurant_link.split('/')[-2]
        else:
            restaurant_id = restaurant_link.split('/')[-1]

        while global_tries < 3:
            # restaurant and products api
            res_pro_api = "https://api-gtm.grubhub.com/restaurants/{}?hideChoiceCategories=true&version=4&variationId=rtpFreeItems&orderType=standard&hideUnavailableMenuItems=true&hideMenuItems=false".format(
                restaurant_id)

            # print('fetching restaurant data')
            grub = session.get(res_pro_api)

            # print('status code returned: {}'.format(grub.status_code))
            if grub.status_code == 200:
                global_tries = 0
                restaurants_response = json.loads(grub.text)
                if 'restaurant' in restaurants_response:
                    restaurant = restaurants_response.get('restaurant', {})

                    # getting restaurant details
                    address = ''
                    city = ''
                    country = ''
                    review = 0
                    stars = 0
                    restaurant_name = restaurant.get('name', '')

                    if 'address' in restaurant:
                        address_line = restaurant['address']
                        address = address_line.get('street_address', '')
                        country = address_line.get('country', '')
                        city = address_line.get('locality', '')
                    if 'rating' in restaurant:
                        review = restaurant['rating'].get('rating_count', 0)
                        stars = restaurant['rating'].get('rating_value', 0)

                    restaurants_details.append([restaurant_name, address, city, country, review, stars])

                    for zip_detail in zip(restaurant_header, [restaurant_name, address, city, country, review, stars]):
                        print("{}: {}".format(zip_detail[0], zip_detail[1]))

                    if 'menu_category_list' in restaurant and restaurant['menu_category_list']:
                        menu_categories = restaurant['menu_category_list']
                        for menu_category in menu_categories:
                            if 'menu_item_list' in menu_category and menu_category['menu_item_list']:
                                category_products = menu_category['menu_item_list']
                                for category_product in category_products:
                                    category_name = category_product.get('menu_category_name', '')
                                    product_name = category_product.get('name', '')
                                    product_description = category_product.get('description', '')
                                    product_price = category_product['price']['amount'] / 100
                                    restaurant_detail = [category_name, product_name, product_description,
                                                         product_price]
                                    category_products_details.append(restaurant_detail)

                                    product_id = category_product['id']

                                    # getting restaurant products details
                                    # products detail api
                                    pro_api = "https://api-gtm.grubhub.com/restaurants/{}/menu_items/{}?time=1662059755411&hideUnavailableMenuItems=true&orderType=standard&version=4".format(
                                        restaurant_id, product_id)

                                    while global_tries < 3:

                                        product_topping_response = session.get(pro_api)
                                        # print('status code returned: {}'.format(product_topping_response.status_code))
                                        if product_topping_response.status_code == 200:
                                            global_tries = 0
                                            toppings = json.loads(product_topping_response.text)
                                            if 'choice_category_list' in toppings and toppings['choice_category_list']:
                                                for modifier in toppings['choice_category_list']:
                                                    modifier_name = modifier.get('name', '')
                                                    choices_list = modifier.get('choice_option_list', [])
                                                    modifier_min = modifier.get('min_choice_options', 0)
                                                    modifier_max = modifier.get('max_choice_options', len(choices_list))
                                                    for choice in choices_list:
                                                        choice_name = choice.get('description', '')
                                                        choice_price = choice['price']['amount'] / 100

                                                        already_exists = False
                                                        for products_topping_detail in products_topping_details:
                                                            if [modifier_name, modifier_min, modifier_max,
                                                                choice_name, choice_price] == products_topping_detail:
                                                                already_exists = True

                                                        if not already_exists:
                                                            products_topping_details.append(
                                                                [modifier_name, modifier_min, modifier_max,
                                                                 choice_name, choice_price])
                                            break
                                        else:
                                            global_tries += 1
                                            access_token = get_access_token(session, client_id)
                                            # update header with new token
                                            session.headers.update({'authorization': 'Bearer ' + access_token})

                                    # recommendation api
                                    # if you want recommended products uncomment below code.

                                    # recommendation_api = "https://api-gtm.grubhub.com/recommendations/menuitem/crosssell?restaurantId={}&menuItemIdsInCart={}&variationId=0.2_PriceCeiling%3D0.50".format(
                                    #     restaurant_id, product_id)
                                    # while global_tries < 3:
                                    #     product_recommendation = session.get(recommendation_api)
                                    #     # print('status code returned: {}'.format(product_recommendation.status_code))
                                    #     if product_recommendation.status_code == 200:
                                    #         global_tries = 0
                                    #         extra_toppings = json.loads(product_recommendation.text)
                                    #         if 'menu_item_recommendations_result' in extra_toppings and extra_toppings[
                                    #             'menu_item_recommendations_result']:
                                    #             extra_topping_list = extra_toppings['menu_item_recommendations_result']
                                    #             for extra_topping in extra_topping_list:
                                    #                 if 'menu_item_recommendation_list' in extra_topping and \
                                    #                         extra_topping['menu_item_recommendation_list']:
                                    #                     for recommended_item in extra_topping[
                                    #                         'menu_item_recommendation_list']:
                                    #                         choice_name = recommended_item.get('menu_item_name', '')
                                    #                         choice_price = recommended_item['menu_item_price'][
                                    #                                            'amount'] / 10
                                    #                         already_exists = False
                                    #                         for products_topping_detail in products_topping_details:
                                    #                             if ["Complete your meal", 0, 1,
                                    #                                 choice_name,
                                    #                                 choice_price] == products_topping_detail:
                                    #                                 already_exists = True
                                    #
                                    #                         if not already_exists:
                                    #                             products_topping_details.append(
                                    #                                 ["Complete your meal", 0, 1,
                                    #                                  choice_name, choice_price])
                                    #         break
                                    #     else:
                                    #         global_tries += 1
                                    #         access_token = get_access_token(session, client_id)
                                    #         # update header with new token
                                    #         session.headers.update({'authorization': 'Bearer ' + access_token})
                # break the while loop for refreshing/getting the new token
                break
            else:
                global_tries += 1
                access_token = get_access_token(session, client_id)
                # update header with new token
                session.headers.update({'authorization': 'Bearer ' + access_token})


# define and add a proper header
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'authorization': 'Bearer',
    'content-type': 'application/json;charset=UTF-8'
}


def get_client_id(session):
    client = []
    try:
        static_content_api = 'https://www.grubhub.com/eat/static-content?contentOnly=1'
        soup = BeautifulSoup(session.get(static_content_api).text, 'html.parser')
        client = re.findall("beta_[a-zA-Z0-9]+", str(soup.find('script', {'type': 'text/javascript'})))
        # client=['beta_UmWlpstzQSFmocLy3h1UieYcVST']
        # print(client)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    return client


def get_access_token(session, client_id):
    # print('getting new access token')
    access = ''
    try:
        data = '{"brand":"GRUBHUB","client_id":"' + client_id[0] + '","device_id":-708763761,"scope":"anonymous"}'
        resp = session.post('https://api-gtm.grubhub.com/auth', data=data)

        # refresh = json.loads(resp.text)['session_handle']['refresh_token']
        access = json.loads(resp.text)['session_handle']['access_token']
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    return access


def main(restaurants_links):
    global global_tries
    restaurants_details = []
    category_products_details = []
    products_topping_details = []

    threads_dict = {}
    threads_dictionary = {}
    users_search_threads = []
    restaurant_id_appended_list = []
    concurrent_threads_no = 2
    threads_appended = 0

    # creating session and getting client/accesstoken to authorize further apis
    # print('creating session and getting client/accesstoken to authorize further apis')
    session = requests.Session()
    client_id = get_client_id(session)
    session.headers.update(headers)
    access_token = get_access_token(session, client_id)
    # update header with new token
    session.headers.update({'authorization': 'Bearer ' + access_token})
    # print('session created')

    # iterate over restaurants and fetch their data
    # print('iterate over restaurants and fetch their data')
    for restaurant_link in restaurants_links:
        if restaurant_link[-1] == '/':
            restaurant_id = restaurant_link.split('/')[-2]
        else:
            restaurant_id = restaurant_link.split('/')[-1]

        params = [restaurant_link, session, restaurants_details, category_products_details,
                  products_topping_details, client_id]
        threads_dict[restaurant_id] = MultiThreadClass(crawl_website(), "crawl_restaurant",
                                                       "scrape restaurant " + restaurant_id,
                                                       "scrape_retaurant_" + restaurant_id, *params)
        # print("starting thread against restaurant id: {} ".format(restaurant_id))
        threads_dict[restaurant_id].start()
        users_search_threads.append(threads_dict[restaurant_id])
        threads_appended += 1
        restaurant_id_appended_list.append(restaurant_id)

        if threads_appended == concurrent_threads_no or (
                len(restaurants_links) - len(threads_dictionary) < concurrent_threads_no and threads_appended == len(
            restaurants_links) - len(threads_dictionary)):
            scraping_threads_results = {}
            for t in users_search_threads:
                t.join()
                scraping_threads_results[t.methodResultVariableName] = t.methodResults

            for restaurant_fetched_id in restaurant_id_appended_list:
                if 'scrape_retaurant_' + str(restaurant_fetched_id) in scraping_threads_results:
                    threads_dictionary[str(restaurant_fetched_id)] = scraping_threads_results[
                        'scrape_retaurant_' + str(restaurant_fetched_id)]

            users_search_threads = []
            threads_dict = {}
            restaurant_id_appended_list = []
            threads_appended = 0

    with open('grubhub_restaurants_prodcucts.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Category Name', 'Item Name', 'Item Description', 'Item Price'])
        for data in category_products_details:
            writer.writerow(data)
        writer.writerow(['Modifier Group Name', 'Modifier Min', 'Modifier Max', 'Option Name', 'Option Price'])
        for data in products_topping_details:
            writer.writerow(data)


if __name__ == "__main__":
    restaurants_links = [
        'https://www.grubhub.com/restaurant/dosa-love-893-e-el-camino-real-sunnyvale/3024935',
        'https://www.grubhub.com/restaurant/beaus-breakfast-burritos-1404-madison-ave-new-york/3235140',
        'https://www.grubhub.com/restaurant/impeckable-wings-901-nw-24th-st-san-antonio/3159434',
        'https://www.grubhub.com/restaurant/the-vegan-grill-5155-3rd-st-san-francisco/2994242'
    ]
    main(restaurants_links)
