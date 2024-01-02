import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from bs4 import BeautifulSoup
import requests
import pandas as pd
import urllib.parse

session = requests.Session()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US, en;q=0.5'
}

def get_product_details(soup):
    title = soup.find("span", attrs={"id": 'productTitle'}).get_text(strip=True) if soup.find("span", attrs={"id": 'productTitle'}) else "No Title"
    price = soup.find("span", attrs={'class': 'a-price'}).find("span", attrs={'class': 'a-offscreen'}).get_text(strip=True) if soup.find("span", attrs={'class': 'a-price'}) else "No Price"
    
    return {
        'title': title,
        'price': price
    }

def scrape_amazon(url):
    try:
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()  
        soup = BeautifulSoup(response.content, "lxml")
        search_results = soup.find_all("div", {"data-component-type": "s-search-result"})
        product_details_list = []

        for result in search_results:
            a_tag = result.find("a", {"class": "a-link-normal s-no-outline"})
            if a_tag and 'href' in a_tag.attrs:
                product_url = "https://www.amazon.com" + a_tag['href']
                product_page = session.get(product_url, headers=HEADERS)
                product_soup = BeautifulSoup(product_page.content, "lxml")
                product_details = get_product_details(product_soup)
                product_details_list.append(product_details)
        
        return product_details_list
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(fluid=True, children=[
    dbc.Row(justify="center", children=[
        dbc.Col(md=8, children=[
            dcc.Input(id='url-input', type='url', placeholder='Enter Amazon search URL...', className="mb-3 form-control"),
            dbc.Button('Fetch', id='fetch-button', color="primary", n_clicks=0, className="mb-3"),
            html.Div(id='product-info')
        ])
    ]),
    dbc.Row(justify="center", children=[
        dbc.Col(md=8, children=[
            html.A('Download Data', id='download-link', download="product_data.csv", href="", target="_blank", className="btn btn-secondary")
        ])
    ])
])

@app.callback(
    Output('product-info', 'children'),
    Output('download-link', 'href'),
    [Input('fetch-button', 'n_clicks')],
    [State('url-input', 'value')]
)
def fetch_product_info(n_clicks, url):
    if n_clicks > 0 and url:
        products = scrape_amazon(url)
        product_info = [
            dbc.Card(
                dbc.CardBody([
                    html.H4(product['title'], className="card-title"),
                    html.P(f"Price: {product['price']}", className="card-text"),
                ]), className="mb-3"
            ) for product in products
        ]

        df = pd.DataFrame(products)
        csv_string = df.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)

        return product_info, csv_string
    return [], ""

if __name__ == '__main__':
    app.run_server(debug=True)