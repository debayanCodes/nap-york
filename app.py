import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import numpy as np
from wordcloud import WordCloud

# Configure the page
st.set_page_config(
    page_title="GitHub Repositories Analytics",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
        .stPlotlyChart {
            background-color: #ffffff;
            border-radius: 5px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats-box {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and preprocess the dataset with caching"""
    data = pd.read_csv("github_dataset.csv")
    data['language'] = data['language'].fillna('Not Specified')
    data['stars_count'] = data['stars_count'].fillna(0).astype(int)
    data['forks_count'] = data['forks_count'].fillna(0).astype(int)
    data['contributors'] = data['contributors'].fillna(0).astype(int)
    data['issues_count'] = data['issues_count'].fillna(0).astype(int)
    if 'created_at' in data.columns:
        data['created_at'] = pd.to_datetime(data['created_at'], errors='coerce')
    return data

def format_number(num):
    """Format large numbers for better readability"""
    if num >= 1e6:
        return f"{num/1e6:.1f}M"
    elif num >= 1e3:
        return f"{num/1e3:.1f}K"
    return f"{num:.0f}"

# Load data
try:
    data = load_data()

    # Title and description
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("🚀 GitHub Repositories Analytics Dashboard")
    with col2:
        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    st.write("An interactive dashboard analyzing GitHub repository trends and metrics.")

    # Sidebar filters
    with st.sidebar:
        st.header("📎 Filters")

        # Language filter with select all option
        all_languages = ['All'] + sorted(data['language'].unique().tolist())
        selected_languages = st.multiselect(
            "Select Languages",
            all_languages,
            default=['All']
        )

        # Star count range filter
        star_range = st.slider(
            "Stars Count Range",
            min_value=int(data['stars_count'].min()),
            max_value=int(data['stars_count'].max()),
            value=(int(data['stars_count'].min()), int(data['stars_count'].max()))
        )

        # Date range filter if available
        if 'created_at' in data.columns:
            date_range = st.date_input(
                "Date Range",
                value=(data['created_at'].min(), data['created_at'].max())
            )

    # Apply filters
    filtered_data = data.copy()

    # Check if any specific language is selected; if not, default to "All"
    if selected_languages and 'All' not in selected_languages:
        filtered_data = filtered_data[filtered_data['language'].isin(selected_languages)]

    # Check for a valid star range
    if star_range:
        filtered_data = filtered_data[
            (filtered_data['stars_count'] >= star_range[0]) & 
            (filtered_data['stars_count'] <= star_range[1])
        ]

    # Check if 'created_at' column exists and date_range is defined
    if 'created_at' in data.columns and date_range:
        filtered_data = filtered_data[
            (filtered_data['created_at'] >= pd.to_datetime(date_range[0])) & 
            (filtered_data['created_at'] <= pd.to_datetime(date_range[1]))
        ]

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Repositories", len(filtered_data))
    with col2:
        st.metric("Total Stars", format_number(filtered_data['stars_count'].sum()))
    with col3:
        st.metric("Total Forks", format_number(filtered_data['forks_count'].sum()))
    with col4:
        st.metric("Avg Contributors", format_number(int(filtered_data['contributors'].mean())))

    # Main content in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Detailed Analysis", "📈 Trends", "🌐 Geographical Distribution"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            # Language Distribution
            st.subheader("Language Distribution")
            lang_dist = filtered_data['language'].value_counts().head(10)
            fig = px.pie(
                values=lang_dist.values,
                names=lang_dist.index,
                title="Top 10 Languages",
                hole=0.3
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Stars vs Forks
            st.subheader("Stars vs Forks Correlation")
            fig = px.scatter(
                filtered_data,
                x='stars_count',
                y='forks_count',
                color='language',
                size='contributors',
                hover_data=['repositories'],
                log_x=True,
                log_y=True,
                title="Stars vs Forks (log scale)"
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Top Repositories Table
        st.subheader("Top Repositories")
        top_repos = filtered_data.nlargest(10, 'stars_count')[
            ['repositories', 'language', 'stars_count', 'forks_count', 'contributors']
        ]

        # Format the numbers in the table
        top_repos['stars_count'] = top_repos['stars_count'].apply(format_number)
        top_repos['forks_count'] = top_repos['forks_count'].apply(format_number)

        st.dataframe(top_repos, hide_index=True)

        # Issues vs Contributors
        st.subheader("Issues vs Contributors Analysis")
        fig = px.scatter(
            filtered_data,
            x='issues_count',
            y='contributors',
            color='language',
            size='stars_count',
            hover_data=['repositories'],
            title="Issues vs Contributors Correlation"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Time series analysis if date column is available
        if 'created_at' in filtered_data.columns:
            st.subheader("Repository Creation Trends")
            filtered_data['created_at'] = pd.to_datetime(filtered_data['created_at'])
            monthly_trends = filtered_data.resample('M', on='created_at').size()

            fig = px.line(
                x=monthly_trends.index,
                y=monthly_trends.values,
                title="Monthly Repository Creation Trend"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Repository Age Distribution
        st.subheader("Repository Age Distribution")
        if 'created_at' in filtered_data.columns:
            filtered_data['age'] = (datetime.now() - filtered_data['created_at']).dt.days
            fig = px.histogram(
                filtered_data,
                x='age',
                title="Repository Age Distribution",
                nbins=30
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        # Geographical Distribution
        st.subheader("Geographical Distribution of Repositories")
        if 'country' in filtered_data.columns:
            country_dist = filtered_data['country'].value_counts().reset_index()
            country_dist.columns = ['country', 'count']
            fig = px.choropleth(
                country_dist,
                locations="country",
                locationmode='country names',
                color="count",
                hover_name="country",
                title="Geographical Distribution of Repositories"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Repository Topics Word Cloud
    st.subheader("Repository Topics Word Cloud")
    if 'topics' in filtered_data.columns:
        topics = ' '.join(filtered_data['topics'].dropna().astype(str))
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(topics)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)

    # Download Filtered Data
    st.subheader("Download Filtered Data")
    st.download_button(
        label="Download Filtered GitHub Data as CSV",
        data=filtered_data.to_csv(index=False),
        file_name="filtered_github_data.csv",
        mime="text/csv"
    )

    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center'>
            <p>Built with Streamlit • Data sourced from GitHub API
            <br>Last updated: {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

except FileNotFoundError:
    st.error("Dataset file not found. Please make sure the file 'github_dataset.csv' exists.")
except pd.errors.EmptyDataError:
    st.error("The dataset file is empty. Please provide a valid dataset.")
except pd.errors.ParserError:
    st.error("Error parsing the dataset file. Please check the file format.")
except KeyError as e:
    st.error(f"Column missing: {e}. Please ensure the dataset has all required columns.")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.warning("Please make sure the dataset file exists and contains the required columns.")
