import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import plotly.graph_objects as go
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

def display_map_with_sentiment_with_location(data, sentiment, geo_df, location=None):
    def get_most_positive_sentiment_per_location(data, sentiment):
        # Konversi data ke DataFrame pandas
        df = pd.DataFrame(data, columns=['location', 'Tokoh', 'Sentiment', 'jumlah'])

        # Mengelompokkan data berdasarkan lokasi
        grouped = df.groupby('location')

        # Membuat DataFrame baru untuk hasil akhir
        result = pd.DataFrame(columns=['location', 'Tokoh', 'Sentiment', 'jumlah'])

        # Loop melalui setiap grup lokasi
        for group_name, group_df in grouped:
            # Mengambil sentimen positif terbanyak
            max_positive_sentiment = group_df[group_df['Sentiment'] == sentiment].sort_values('jumlah', ascending=False).iloc[0]

            # Menambahkan hasil ke DataFrame akhir
            result = result.append(max_positive_sentiment)

        # Mengembalikan DataFrame akhir
        return result
    
    # Menggabungkan data dan menghitung jumlah sentimen per lokasi dan tokoh
    count_sentiment_tokoh_loc = data.groupby(['location', 'Sentiment', 'Tokoh'])['location'].count().reset_index(name="jumlah")
    merge2 = geo_df.merge(count_sentiment_tokoh_loc, on='location')
    merge2 = merge2[['location', 'Tokoh', 'Sentiment', 'jumlah']]
    
    # Melakukan filter berdasarkan lokasi jika parameter location diberikan
    if location:
        merge2 = merge2[merge2['location'] == location]

    # Mendapatkan sentimen positif terbanyak per lokasi
    fil = get_most_positive_sentiment_per_location(merge2, sentiment)

    # Menggabungkan dengan data geospasial
    fil = geo_df.merge(fil, on='location')
    fil = gpd.GeoDataFrame(fil, geometry='geometry')
    fil = fil[['location', 'Tokoh', 'Sentiment', 'jumlah', 'geometry']]

    # Membuat peta menggunakan folium
    map_indo = folium.Map(location=[-2.5489, 118.0149], tiles='cartodbdark_matter', zoom_start=5, zoom_control=False,
               scrollWheelZoom=False,
               dragging=False)

    style_function = lambda x: {
        "fillColor": "#FF0000" if x["properties"]["Tokoh"] == "Ganjar Pranowo" else
                    "#0000FF" if x["properties"]["Tokoh"] == "Anies Baswedan" else
                    "#FFFF00",
        "fill": True,
        "fill_opacity": 0.7,
        "line_opacity": 0.2,
        "color": False
    }

    color = folium.GeoJson(fil, style_function=style_function)
    folium.GeoJsonTooltip(['location']).add_to(color)
    color.add_to(map_indo)

    st_map=st_folium(map_indo, width=1500, height=450)
    return st_map

def create_cumulative_line_chart(df, sentiment:int):
    # Filter data sentimen positif
    positive_df = df[df['Sentiment'] == sentiment]

    # Menghitung jumlah kemunculan sentimen positif per tanggal dan tokoh
    sentiment_counts = positive_df.groupby(['date', 'Tokoh']).size().reset_index(name='count')

    # Menghitung jumlah akumulatif dari nilai sebelumnya
    sentiment_counts['cumulative_count'] = sentiment_counts.groupby('Tokoh')['count'].cumsum()

    # Membuat line chart menggunakan Plotly
    fig = go.Figure()

    # Mengatur warna untuk setiap tokoh
    colors = {'Ganjar Pranowo': 'darkred', 'Anies Baswedan': 'darkblue', 'Prabowo Subianto': 'darkgoldenrod'}

    # Loop melalui setiap tokoh yang ada dalam dataframe
    for tokoh in sentiment_counts['Tokoh'].unique():
        data_tokoh = sentiment_counts[sentiment_counts['Tokoh'] == tokoh]
        fig.add_trace(go.Scatter(x=data_tokoh['date'], y=data_tokoh['cumulative_count'], mode='lines',
                                 name=tokoh, line=dict(color=colors[tokoh])))

    # Mengatur judul dan label sumbu
    fig.update_layout(title='Cumulative Line Chart Sentiment Positif per Tokoh',
                      xaxis_title='Date',
                      yaxis_title='Cumulative Sentiment Count')

    # Menampilkan line chart menggunakan Streamlit
    st.plotly_chart(fig)
    
def create_barchart(df, sentiment):
    # Filter the DataFrame to include only the specified sentiment
    df_filtered = df[df['Sentiment'] == sentiment]

    # Group the filtered DataFrame by 'Tokoh' and calculate the count of each 'Sentiment'
    grouped_data = df_filtered.groupby(['Tokoh', 'Sentiment']).size().reset_index(name='Count')

    # Define colors for each tokoh
    colors = {'Ganjar Pranowo': 'darkred', 'Anies Baswedan': 'darkblue', 'Prabowo Subianto': 'darkgoldenrod'}

    # Create a bar chart using Plotly Go
    fig = go.Figure()
    for tokoh, color in colors.items():
        data = grouped_data[grouped_data['Tokoh'] == tokoh]
        fig.add_trace(go.Bar(x=data['Tokoh'], y=data['Count'], name=tokoh, marker_color=color))

    # Add annotations to the chart
    for idx, row in grouped_data.iterrows():
        fig.add_annotation(
            x=row['Tokoh'],
            y=row['Count'],
            text=row['Count'],
            showarrow=True,
            arrowhead=1,
            font=dict(color='white'),
            xanchor='center',
            yanchor='bottom'
        )

    # Customize the layout of the chart
    fig.update_layout(
        title=f'Sentiment Analysis by Tokoh ({sentiment})',
        xaxis_title='Tokoh',
        yaxis_title='Count',
        barmode='stack'
    )

    # Display the chart using Streamlit
    st.plotly_chart(fig)
    
def get_latest_date(df):
    # Mengambil tanggal terbaru
    tanggal_terbaru = df['date'].max()
    return tanggal_terbaru


def main():
    #TITLE
    APP_TITLE = "Klasifikasi Opini publik di Twitter terhadap bakal calon Presiden Indonesia Tahun 2024 secara Real Time"
    st.set_page_config(APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    #READ MYSQSL DATA
    # query = "SELECT * FROM hasil_scraping"
    #READ DATA
    data_df = pd.read_csv("data/data.csv")
    geo_df = gpd.read_file('data/indonesia-prov.geojson')
    #mengganti value Status
    replacement_mapping_dict = {
        "DI. ACEH" : "ACEH",
        "NUSATENGGARA BARAT" : "NUSA TENGGARA BARAT",
        "DAERAH ISTIMEWA YOGYAKARTA" : "DI YOGYAKARTA",
        "BANGKA BELITUNG" : "KEPULAUAN BANGKA BELITUNG"
    }
    geo_df["Propinsi"] = geo_df["Propinsi"].replace(replacement_mapping_dict)
    geo_df.rename(columns={'Propinsi': 'location'}, inplace=True)
    
    #MERGE
    merged_gdf = geo_df.merge(data_df, on='location')
    merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry='geometry')   
    
    st.markdown(f'<h3 style="color: gray;border-radius:50%;" >sumber: www.twitter.com</h3>',unsafe_allow_html=True)
    latest_date = get_latest_date(data_df)
    st.markdown("Data Update : "+latest_date)
    st.metric(label="Akurasi", value='75 %')
    # Using "with" notation
    with st.container():
         ganjar, anies, prabowo = st.columns(3)
         with ganjar:
            st.subheader("Ganjar Pranowo")
            image = Image.open('images/ganjar.png')
            width = 100
            height = 100
            resized_image = image.resize((width, height))
            st.image(resized_image)
             
         with anies:
            st.subheader("Anies Baswedan")
            image = Image.open('images/anies.png')
            width = 100
            height = 100
            resized_image = image.resize((width, height))
            st.image(resized_image)
             
         with prabowo:
            st.subheader("Prabowo Subianto")
            image = Image.open('images/prabowo.png')
            width = 100
            height = 100
            resized_image = image.resize((width, height))
            st.image(resized_image)
    with st.container():
        st.subheader("Jumlah Sentiment Positif terbanyak tiap Provinsi")
        display_map_with_sentiment_with_location(merged_gdf, 1, geo_df)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Grafik Sentimen Positif Bakal Calon Presiden")
            create_cumulative_line_chart(data_df, 1)
        with col2:
            st.subheader("Jumlah Sentimen Positif Bakal Calon Presiden")
            create_barchart(data_df, 1)
    
if __name__ == "__main__":
    main()