import requests
import streamlit as st
import pandas as pd
import altair as alt
from altair import datum
import base64
import numpy as np
from vega_datasets import data
from nltk.stem import PorterStemmer
st.title("How could Acai change your Life")

# set the background image 
def set_bg_hack_url():
    st.markdown(
        f"""
        <style>
        .stApp{{
            background: url("https://i.ibb.co/ZV7CpDW/acai.png");
            background-size:cover
            
        }}
        .flip-card {{
            background-color: transparent;
            width: 300px;
            height: 300px;
            perspective: 1000px; /* Remove this if you don't want the 3D effect */
            padding: 10px;
        }}

        .flip-card-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            text-align: center;
            transition: transform 0.8s;
            transform-style: preserve-3d;
        }}

        .flip-card:hover .flip-card-inner {{
            transform: rotateY(180deg);
        }}

        .flip-card-front, .flip-card-back {{
            position: absolute;
            width: 100%;
            height: 100%;
            -webkit-backface-visibility: hidden; /* Safari */
            backface-visibility: hidden;
        }}

        .flip-card-front {{
            background: url("https://i.ibb.co/2dWXzMY/card-back.png");
            opacity:0.8
            background-size:cover
            color: black;
        }}

        .flip-card-back {{
            background-color: #d0ebfd;
            color: white;
            transform: rotateY(180deg);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    return


set_bg_hack_url()
############### Import the data#################


# load data
df_map = pd.read_csv("tradingData.csv",
                     usecols=['Countries', 'E/I', 'Value2021', 'Code'])
df_nutrition = pd.read_csv(
    "nutrition.csv", header=0)
acai_nutrition = pd.DataFrame(
    {'nutrition': df_nutrition.columns[3::], 'value': df_nutrition.iloc[4][3::].values})
df_recipe = pd.read_csv(
    'recipenlg.csv')
df_map.columns = ['Countries', 'Export', 'Value2021', 'Code']







############### Chart 1#################


countries = alt.topo_feature(data.world_110m.url, 'countries')
# The world image
world_map = alt.Chart(countries).mark_geoshape(
    fill='#EEEEEE',
    stroke='white'
)
# The export image
# hover在上面会出现这个国家具体出口量是多少
# hover在上面会出现这个国家具体排名
map_chart_export = alt.Chart(df_map).mark_geoshape().transform_filter(
    alt.datum.Export == 'E'
).transform_window(
    sort=[alt.SortField('Value2021', order='descending')],
    rank='rank()'
).encode(
    color=alt.Color('Value2021:Q', scale=alt.Scale(
        scheme='blues'), title='Main Export Countries'),
    tooltip=[alt.Tooltip('Value2021:Q', title='Export amount'), 'rank:Q']
).transform_lookup(
    lookup='Code',
    from_=alt.LookupData(countries, key='id', fields=[
                         "type", "properties", "geometry"])
)

# the import image
map_chart_import = alt.Chart(df_map).mark_geoshape().transform_filter(
    alt.datum.Export == 'I'
).transform_window(
    sort=[alt.SortField('Value2021', order='descending')],
    rank='rank()'
).encode(
    color=alt.Color('Value2021:Q', scale=alt.Scale(
        scheme='reds'), title='Main Import Countries'),
    tooltip=[alt.Tooltip('Value2021:Q', title='Import amount'), 'rank:Q']
).transform_lookup(
    lookup='Code',
    from_=alt.LookupData(countries, key='id', fields=[
                         "type", "properties", "geometry"])
)

Chart1 = (world_map+(map_chart_export+map_chart_import).resolve_scale(color='independent')).configure(
    background='transparent'
).project(
    'mercator'
).properties(
    width=800,
    height=600,
    title='Distribution of Top Import and Export Countries of Acai'
).configure_title(fontSize=24)

st.altair_chart(Chart1)


############### Chart 2#################
# 创建一个下拉框
# 把数据清洗一下
field = st.selectbox('Choose a nutrition to compare',
                     ('None', 'Total Fat', 'Cholesterol', 'Sodium', 'Potassium', 'Total Carbonhydrate', 'Protein', 'Vitamin C', 'Vitamin A', 'Calcium', 'Iron', 'Vitamin D'))


selection_single = alt.selection_single(encodings=['color'],fields=['nutrition'])
opacityCondition1 = alt.condition((alt.datum.nutrition == field) | (field == 'None'), alt.value(1), alt.value(0.2))
nutrition = alt.Chart(
    acai_nutrition,
    ).mark_arc().encode(
    theta=alt.Theta(field='value',type='quantitative'),
    color=alt.Color(field='nutrition',type='nominal',scale=alt.Scale(scheme='blues')),
    tooltip=['nutrition','value'],
    opacity=opacityCondition1
    ).properties(
      title='Nutrition(mg) in Acai per 100g'
    )
compare1 = alt.Chart(
    df_nutrition
).mark_bar(opacity=0.9, size=30, color='#7ba6f6').encode(
    x=alt.X('Icon:O',title='common fruits'),
    y=('Calories' if field=='None' else field),
    tooltip=['Fruit', ('Calories' if field == 'None' else field)],
).properties(
    width=500,
    title='Compare with other fruits'
)
Chart2 = alt.vconcat(nutrition, compare1).configure(background='transparent').configure_title(fontSize=24)
st.altair_chart(Chart2)


############### Chart 3#################
# 创建一个多选框
# 清洗数据同时给图和用html做成的flipped card
# data clean
# 把大小写和复数给置换掉
# 把无意义的字符给删掉
stemmer = PorterStemmer()
recipe_fruit = []
for r in df_recipe.iterrows():
  fruit = r[1]['NER'][2:-2].split('", "')
  for item in fruit:
    truename = stemmer.stem(item.lower())
    truename.replace('1/4','')
    if (truename not in recipe_fruit and truename != "acai"):
      recipe_fruit.append(truename)
for item in recipe_fruit:
  df_recipe[item] = 0
for i, r in df_recipe.iterrows():
  fruit = r['NER'][2:-2].split('", "')
  for item in fruit:
    df_recipe.at[i, item] = 1

friend_list = pd.DataFrame(
    {"fruit": recipe_fruit, "value": [0]*len(recipe_fruit)})
for i, r in friend_list.iterrows():
  friend_list.at[i, 'value'] = sum(df_recipe[r['fruit']])

slider = alt.binding_range(min=1,max=20,step=1,name="top N ingredients")
selection = alt.selection_single(bind=slider, fields=["topN"],init={"topN":20})
Chart3 = alt.Chart(friend_list).transform_window(
    sort=[alt.SortField('value', order='descending')],
    frequency_rank='rank(value)'
).mark_bar(color='#81CBE1',size=13).encode(
    alt.X('value:Q', title='Frequency'),
    alt.Y('fruit:N', sort=alt.EncodingSortField(
        field="value", order="descending"
    ), title='Ingredients with Acai')
).add_selection(
    selection
).transform_filter(
    alt.datum.frequency_rank <= selection.topN
).properties(
    width=800,
    title='Ingredients suitable for Acai'
).configure(background='transparent').configure_title(fontSize=24)
st.altair_chart(Chart3)
options = st.multiselect(
    'What fruit do you want to cook with Acai',
    ['banana', 'water', 'honey', 'almond milk',"granola",'salt','sugar','mango','coconut'],
    ['banana', 'water'])

num = 0;
for index,menu in df_recipe.iterrows():
    if num>=5:
        break;
    for item in options:
        if menu[item]==1:
            st.markdown(
                f"""
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <h1>{menu['title']}</h1>
                        </div>
                        <div class="flip-card-back">
                            <h1>Directions</h1>
                            <p style="color:black">{menu['directions'][2:-2]}</p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            num+=1
            break;


