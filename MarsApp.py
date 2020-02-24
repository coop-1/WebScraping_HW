from flask import Flask, jsonify, request, flash, render_template
import pymongo
from bs4 import BeautifulSoup
from splinter import Browser
import pandas as pd
import requests

def scrapeData():
    
    executable_path = {'executable_path': r'/Users/crobinson1205/Desktop/chromedriver'}
    browser = Browser('chrome', **executable_path, headless=False)

    mongo_export = {}


    #view website
    url = 'https://mars.nasa.gov/news/'
    browser.visit(url)
    website  = browser.html


    #get title and content from website
    article_soup = BeautifulSoup(website, 'html.parser')


    content = article_soup.find('div',class_ = 'react_grid_list').find('div').find('ul').find('li').find('div').find(class_ = 'rollover_description_inner').text


    title = article_soup.find('div',class_ = 'react_grid_list').find('div').find('ul').find('li').find('div').find('a').find(class_ = 'bottom_gradient').text

    article_soup_dict = {}
    article_soup_dict["title"] = title
    article_soup_dict["content"] = content


    #get image from jpl space
    url = 'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars'
    browser.visit(url)
    website = browser.html

    image_soup = BeautifulSoup(website, 'html.parser')
    main_section = image_soup.find(class_="centered_text clearfix main_feature primary_media_feature single")
    image_con = main_section.find(class_ ="default floating_text_area ms-layer")
    image_str = image_con.find('a').get('data-fancybox-href')
    image_link = f'https://www.jpl.nasa.gov{image_str}'

    image_soup_dict = {}
    image_soup_dict["link"] = image_link


    #mars twitter weather
    url = 'https://twitter.com/marswxreport?lang=en/tweets'
    data = requests.get(url) 
    twitter_soup = BeautifulSoup(data.text, 'html.parser')

    mars_weather_tweet = twitter_soup.find_all('div', attrs={"class": "tweet"})[0]
    mars_weather_tweet.find('p').text

    found = False
    i = 0
    while found == False:
        mars_weather_tweet = twitter_soup.find_all('div', attrs={"class": "tweet"})[i]
        mars_weather_text = mars_weather_tweet.find('p').text
        if (mars_weather_text.find('InSight sol') != -1) and (mars_weather_text.find('ºC') != -1) and (mars_weather_text.find('ºF') != -1) and (mars_weather_text.find('m/s') != -1):
            weather_report = mars_weather_tweet.find('p').text
            found = True
        
        i+=1
        
    weather_soup_dict = {}
    weather_soup_dict["report"] = weather_report


    #mars facts
    url = 'https://space-facts.com/mars/'
    browser.visit(url)
    website = browser.html

    fact_soup = BeautifulSoup(website, 'html.parser')
    mars_facts = fact_soup.find('table',id="tablepress-p-mars")

    mars_facts_rows = mars_facts.find_all('tr')
    mars_table = {}

    i = 0
    for i in range(len(mars_facts_rows)):
        mars_elements = []
        key = mars_facts_rows[i].find('td',class_ = 'column-1').text
        value = mars_facts_rows[i].find('td',class_ = 'column-2').text
        mars_table[key]=[value]

    mars_df = pd.DataFrame(mars_table)
    mars_df = mars_df.transpose()

    mars_df = mars_df.rename_axis('Description')
    mars_df = mars_df.rename(columns = {0:'Value'})

    # mars_df
    mars_df.to_html()

    fact_soup_dict = {}
    fact_soup_dict["facts"] = mars_df.to_html()


    #mars hemispheres pictures
    url = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'

    browser.visit(url)

    website = browser.html

    hemisphere_soup = BeautifulSoup(website, 'html.parser')
    hemisphere_soup.select('.itemLink.product-item')[0]

    all_mars_pics = []

    j = 0

    i = 0

    while i < len(hemisphere_soup.select('.itemLink.product-item h3')):
        
        hemisphere_soup = BeautifulSoup(website, 'html.parser')
        
        pics_link = hemisphere_soup.select('.itemLink.product-item')[j].get('href')
        
        destination = f'https://astrogeology.usgs.gov{pics_link}'
        
        planet_pics = {}
        
        browser.visit(destination)
        
        destinaton_site = browser.html
        
        destination_soup = BeautifulSoup(destinaton_site,'html.parser')
        
        final_pic = browser.links.find_by_text('Sample')
        
        planet_pics['url'] = final_pic['href']

        all_mars_pics.append(planet_pics)
        
        j += 2
        
        i += 1

    hemisphere_soup_list = []
    hemisphere_soup_list.append(all_mars_pics)

    mongo_export = {}
    mongo_export['article_soup'] = article_soup_dict
    mongo_export['image_soup'] = image_soup_dict
    mongo_export['fact_soup'] = fact_soup_dict
    mongo_export['hemisphere_soup'] = hemisphere_soup_list
    mongo_export['weather_soup'] = weather_soup_dict
    mongo_export

    browser.quit()

    #pymongo
    conn = 'mongodb://localhost:27017'
    client = pymongo.MongoClient(conn)

    db = client.marsDB

    mars = db.mars_info

    mars.update({},mongo_export, upsert = True)

######################################   FLASK APP   ######################################

conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)

mars_data = client["marsDB"]["mars_info"]

results = mars_data.find_one()

mars_article = results["article_soup"]
mars_image = results["image_soup"]['link']
mars_fact = results["fact_soup"]['facts']
mars_weather = results["weather_soup"]['report']
mars_hemi1 = results["hemisphere_soup"][0][0]['url']
mars_hemi2 = results["hemisphere_soup"][0][1]['url']
mars_hemi3 = results["hemisphere_soup"][0][2]['url']
mars_hemi4 = results["hemisphere_soup"][0][3]['url']


app = Flask(__name__, template_folder='templates')

@app.route("/")
def index():
     return render_template(
    "index.html", 
     article_soup = mars_article, 
     mars_image = mars_image,
     mars_facts = mars_fact,
     hemi1 = mars_hemi1,
     hemi2 = mars_hemi2,
     hemi3 = mars_hemi3,
     hemi4 = mars_hemi4,
     weather_soup = mars_weather
     )

@app.route("/scrapeData")
def scrape():
    
    scrapeData()

    mars_data = client["marsDB"]["mars_info"]

    results = mars_data.find_one()

    mars_article = results["article_soup"]
    mars_image = results["image_soup"]['link']
    mars_fact = results["fact_soup"]['facts']
    mars_weather = results["weather_soup"]['report']
    mars_hemi1 = results["hemisphere_soup"][0][0]['url']
    mars_hemi2 = results["hemisphere_soup"][0][1]['url']
    mars_hemi3 = results["hemisphere_soup"][0][2]['url']
    mars_hemi4 = results["hemisphere_soup"][0][3]['url']

    
    return "DATA UPDATED"


if __name__ == "__main__":
    app.run(debug=True)