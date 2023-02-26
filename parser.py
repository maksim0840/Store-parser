import requests
from bs4 import BeautifulSoup
import re

#считывание заголовков headers и cookies с файла
file=open('headers.txt')
params=file.readlines()
for i in range(len(params)):
    params[i]=params[i].split(',,')
    for j in range(len(params[i])):
        params[i][j]=params[i][j].replace('\n','')
        params[i][j]=params[i][j].split('::')
file.close()
def get_headers(i):
    parameters_block={}
    for j in range(len(params[i])):
        parameters_block[params[i][j][0]]=params[i][j][1]
    return parameters_block

#получения айди товаров + ссылок - днс
def get_data_dns(product,page,cookies,headers,params):
    try:
        links_products=[]
        url=f'https://www.dns-shop.ru/search/?q={product}&order=discount&p={page}&stock=now'
        response = requests.post(url=url, params=params,cookies=cookies, headers=headers).json()
        response = response.get('html')
        soup = BeautifulSoup(response, 'lxml')
        links=soup.find_all('a',class_="catalog-product__image-link")
        for link in links:
            link=link['href'][:-1]
            link=link[:link.rfind("/")+1]
            links_products.append(link)
        elements = soup.find_all('div', class_='catalog-product ui-button-widget')
        data = 'data={"type":"product-buy","containers":['
        for i in range(len(elements)):
            id = elements[i]['data-product']
            data += '{"id":"' + str(i) + '","data":{"id":"' + id + '"}}'
            if i != len(elements) - 1:
                data += ','
        data += ']}'
        return [data,links_products]
    except:
        return [0,0]
#получение информации по товарам - днс
def get_discounts_dns(product,link):
    page=0
    discounts=[]
    cookies = get_headers(0)
    headers = get_headers(1)
    params = get_headers(2)
    while True:
        page+=1
        if link==0:
            data = get_data_dns(product, page, cookies, headers, params)
            if data==[0,0]:
                return discounts
            links=data[1]
            data=data[0]
        else:
            links=link[1]
            data=link[0]
        url='https://www.dns-shop.ru/ajax-state/product-buy/'
        response = requests.post(url=url, params=params, cookies=cookies, headers=headers, data=data)
        ids=response.json().get('data').get('states')
        flag=0
        for i in range(len(ids)):
            id=ids[i]
            id=id.get('data')
            name=id.get('name')
            price=id.get('price')
            current_price=price.get('min')
            if current_price!=None:
                old_price = price.get('current')
            else:
                old_price=price.get('previous')
                current_price=price.get('current')
                if old_price==None and link!=0:
                    old_price=current_price
            extra_discount = price.get('onlinePay')
            if (old_price==None and extra_discount==None) or current_price==None:
                continue
            if extra_discount!=None:
                if old_price==None:
                    old_price=current_price
                current_price=int(current_price)-int(extra_discount)
            profit=str(int(100-int(current_price)/(int(old_price)/100)))
            if profit=='0' and link==0:
                continue
            id_product=links[i]
            if id_product.find('https://')>=0:
                id_product=id_product.replace('https://www.dns-shop.ru/product/','')
                id_product=id_product[:id_product.find('/')]
            else:
                id_product=links[i].replace('product','')
                id_product=id_product.replace('/','')
            discounts.append([id_product,profit,str(current_price),name,'dns-shop.ru','https://www.dns-shop.ru' + links[i],product])
            if discounts[-1]!=[] and link==0 and discounts[-1][-1]!=product:
                discounts[-1]=discounts[-1]+[product]
            if link!=0:
                return [[id_product,profit,str(current_price),name,'dns-shop.ru']]
            flag=1
        if flag==0:
            break
    return discounts
#проверка товара dns
def check_product_dns(url):
    cookies = get_headers(0)
    headers = get_headers(1)
    response = requests.get(url=url,headers=headers, cookies=cookies).json()
    response = response.get('html')
    soup = BeautifulSoup(response, 'lxml')
    id = soup.find('script').text
    id = id[id.find('guid') + 7::]
    id = id[:id.find('"')]
    data='data={"type":"product-buy","containers":[{"id":"0","data":{"id":"'+id+'"}}]}'
    return [get_discounts_dns(0,[data,[url]])[0]+[url]]

#получение информации по товарам - ситилинк
def get_discounts_citilink(product):
    cookies = get_headers(3)
    headers = get_headers(4)
    discounts=[]
    page=0
    previous_page='0'
    while True:
        page+=1
        url=f'https://www.citilink.ru/search/?text={product}&pf=ms_action%2Cdiscount.price1_5%2Crating.any&f=discount.price1_5%2Crating.any&p={str(page)}'
        response = requests.get(url=url,headers=headers,cookies=cookies).text
        soup = BeautifulSoup(response, 'lxml')
        current_page=soup.find('span',class_='PaginationWidget__page')
        current_page=current_page.text
        if previous_page==current_page:
            return discounts
        previous_page=current_page
        cards=soup.find_all('div',class_='product_data__gtm-js')
        for card in cards:
            link='https://www.citilink.ru'+card.find('a')['href']
            id=re.findall(r'\d+', url)[-1]
            name=card.find('a',class_='ProductCardVertical__name').text
            old_price = card.find('span',class_='ProductCardVerticalPrice__price-old_current-price').text.replace('\n','').replace(' ','')
            current_price = card.find('span',class_='ProductCardVerticalPrice__price-current_current-price').text.replace('\n','').replace(' ','')
            profit = str(int(100 - int(current_price) / (int(old_price) / 100)))
            discounts.append([id,profit,str(current_price), name,'citilink.ru',link,product])
#проверка товара citilink
def check_product_citilink(url):
    discounts=[]
    cookies = get_headers(3)
    headers = get_headers(4)
    headers['Accept']='*/*'
    id=re.findall(r'\d+', url)[-1]
    json_data = {
        'query': 'query($filter1:Catalog_ProductFilterInput!$input2:Catalog_ProductCourierDeliveryVariantsInput$input3:Action_ProductActionsInput!){product_b6304_9f535:product(filter:$filter1){id name isAvailable shortName description rating marks{fairMark}multiplicity hidingSettings{isFeedbacksHidden isReviewsHidden}social{discussionsCount feedbacksCount reviewsCount videosCount}category{id name slug parents{__typename id name slug}}brand{id name slug}images{citilink{__typename sources{__typename url size}}}images3d{__typename sources{__typename url size}}price{current old club isFairPrice bonusPoints clubPriceViewType}videos{__typename id title youtube{id preview{sources{__typename url size}}}}delivery{self{availabilityByDays{__typename deliveryTime storeCount}}courier{variants_f3235_1fac2:variants(input:$input2){__typename deliveryTime id type price}}}credit{credit{name payment period}installment{name payment period}}labels{__typename id type title target{action{id}inNewWindow url}textColor backgroundColor expirationTime}propertiesShort{__typename id name description value measure}searchDescription configuration{isInConfiguration canBeAddedToCurrentConfiguration}stock{lastAvailableTime}actions_d3327_75b81:actions(input:$input3){items{__typename id type shortDescription disclaimer}}}}',
        'variables': {'filter1': {'id': id},'input3': {'limit': 0}}}
    response = requests.post('https://www.citilink.ru/graphql/', cookies=cookies, headers=headers, json=json_data).json()
    response=response.get('data').get('product_b6304_9f535')
    name=response.get('name')
    price=response.get('price')
    current_price=price.get('current')
    old_price=price.get('old')
    if len(old_price)==0:
        old_price=current_price
    profit=str(int(100-int(current_price)/(int(old_price)/100)))
    discounts.append([id,profit,str(current_price),name,'citilink.ru',url])
    return discounts

#получение айдишников товаров - мвидео
def get_data_mvideo(product,page,cookies,headers):
    params = {
        'offset': str(24*page),
        'query': product,
        'filterParams': ['WyJza2lka2EiLCIiLCJkYSJd','WyJ0b2xrby12LW5hbGljaGlpIiwiIiwiZGEiXQ=='],
        'doTranslit': 'true'}
    url='https://www.mvideo.ru/bff/products/search'
    response = requests.get(url=url, params=params, cookies=cookies,headers=headers)
    ids=response.json().get('body').get('products')
    return ids
#получение названия товаров - мвидео
def get_names_mvideo(productIds,cookies,headers):
    json_data = {'productIds': productIds}
    names=[]
    url='https://www.mvideo.ru/bff/product-details/list'
    response = requests.post(url=url, cookies=cookies, headers=headers,json=json_data).json()
    blocks=response.get('body').get('products')
    for block in blocks:
        names.append(block.get('name'))
    return names
#получение информации по товарам - мвидео
def get_discounts_mvideo(product,ids):
    cookies = get_headers(5)
    headers = get_headers(6)
    page=0
    discounts=[]
    while True:
        try:
            if product!=0:
                ids=get_data_mvideo(product,page,cookies,headers)
                page += 1
                ids_str = ''
                for id in ids:
                    ids_str+=id+','
                ids_str=ids_str[:-1]
                params = {'productIds': ids_str}
            else:
                params = {'productIds': ids}
            names = get_names_mvideo(ids, cookies, headers)
            url='https://www.mvideo.ru/bff/products/prices'
            response = requests.get(url=url, params=params, cookies=cookies,headers=headers).json()
            cards=response.get('body')
            if cards is None:
                return discounts
            cards=cards.get('materialPrices')
            prices={}
            for i in range(len(cards)):
                cards[i]=cards[i].get('price')
                old_price=cards[i].get('basePrice')
                current_price=cards[i].get('salePrice')
                id=cards[i].get('productId')
                prices[id]=[current_price,old_price]
            for i in range(len(ids)):
                if product!=0:
                    price=prices[ids[i]]
                else:
                    price=prices[id]
                old_price=price[-1]
                current_price=price[0]
                link='https://www.mvideo.ru/products/'+ids[i]
                profit = str(int(100 - int(current_price) / (int(old_price) / 100)))
                discounts.append([ids[i],profit,str(current_price),names[i],'mvideo.ru',link])
                if discounts[-1] != [] and product != 0 and discounts[-1][-1]!=product:
                    discounts[-1] = discounts[-1] + [product]
                if product==0:
                    return [discounts[0][:-1]]
        except:
            if product==0:
                return [[ids[0],profit,str(current_price),names[0],'mvideo.ru']]
            return discounts
#проверка товара mvideo
def check_product_mvideo(url):
    id=re.findall(r'\d+', url)
    if len(id)!=1:
        id=id[-1]
    else:
        id=id[0]
    return [get_discounts_mvideo(0,[id])[0]+[url]]