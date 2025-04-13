import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from supabase import create_client, Client
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Alpha Database Viewer",
    page_icon="🚗",
    layout="wide",
)

# Title and description
st.title("Alpha Database Viewer")
ui.badges(badge_list=[("Live", "destructive"), ("Supabase", "default"), ("Streamlit", "primary"), ("shadcn", "secondary")], class_name="flex gap-2", key="main_badges")
st.caption("Supabase data visualization with auto-updates")

# Initialize Supabase client using streamlit secrets
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

# Get the Supabase client
supabase = init_supabase()

# Initialize session state for data
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame(columns=['ID', 'Plate Number', 'Call Sign'])
if 'auto_update' not in st.session_state:
    st.session_state['auto_update'] = True
if 'poll_interval' not in st.session_state:
    st.session_state['poll_interval'] = 3  # seconds

# Sidebar for search/filter options
with st.sidebar:
    st.header("Update Settings")
    auto_update = ui.switch(default_checked=st.session_state['auto_update'], label="Enable Auto Updates", key="auto_update_switch")
    st.session_state['auto_update'] = auto_update
    
    if auto_update:
        st.success("Auto updates enabled")
        # Allow the user to set poll interval
        interval_options = [
            {"label": "Fast (1 second)", "value": 1, "id": "i1"},
            {"label": "Normal (3 seconds)", "value": 3, "id": "i2"},
            {"label": "Slow (5 seconds)", "value": 5, "id": "i3"}
        ]
        poll_interval = ui.radio_group(options=interval_options, default_value=st.session_state['poll_interval'], key="interval_radio")
        st.session_state['poll_interval'] = poll_interval
        st.caption(f"Checking for updates every {poll_interval} seconds")
    else:
        st.info("Auto updates disabled")
        # Manual refresh button if auto updates are off
        refresh_btn = ui.button("Refresh Data Now", variant="outline", key="refresh_btn")
        if refresh_btn:
            st.session_state['trigger_refresh'] = True
    
    st.divider()
    
    st.header("Search Options")
    search_term = ui.input(placeholder="Search by ID, plate number, or call sign", key="search_input")
    
    # Filter options
    st.subheader("Filter By")
    filter_options = [
        {"label": "All Columns", "value": "All", "id": "f1"},
        {"label": "ID", "value": "ID", "id": "f2"},
        {"label": "Plate Number", "value": "Plate Number", "id": "f3"},
        {"label": "Call Sign", "value": "Call Sign", "id": "f4"}
    ]
    filter_column = ui.radio_group(options=filter_options, default_value="All", key="filter_radio")

# Function to fetch data from Supabase
def fetch_data(supabase_client):
    try:
        query = supabase_client.table('alpha').select('*')
        response = query.execute()
        
        if response.data:
            # Create DataFrame and rename columns to nicer format
            df = pd.DataFrame(response.data)
            
            # Rename columns for display
            df = df.rename(columns={
                'id': 'ID',
                'plate_number': 'Plate Number',
                'call_sign': 'Call Sign'
            })
            
            return df
        else:
            return pd.DataFrame(columns=['ID', 'Plate Number', 'Call Sign'])
            
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame(columns=['ID', 'Plate Number', 'Call Sign'])

# Function to filter data based on search terms
def filter_data(df, search=None, filter_col=None):
    if df.empty:
        return df
        
    filtered_df = df.copy()
    
    if search:
        if filter_col != "All":
            filtered_df = filtered_df[filtered_df[filter_col].astype(str).str.contains(search, case=False, na=False)]
        else:
            # Search across all columns
            mask = False
            for col in filtered_df.columns:
                mask = mask | filtered_df[col].astype(str).str.contains(search, case=False, na=False)
            filtered_df = filtered_df[mask]
    
    return filtered_df

# Main content area
tab_selection = ui.tabs(
    options=['Data Table', 'Statistics', 'Settings'], 
    default_value='Data Table', 
    key="main_tabs"
)

# Main content based on selected tab
if tab_selection == "Data Table":
    # Create a single placeholder for all data table content
    data_table_placeholder = st.empty()
    
    # Load initial data if needed
    if 'data' not in st.session_state or st.session_state['data'].empty or st.session_state.get('trigger_refresh', False):
        if supabase:
            with st.spinner("Loading data..."):
                st.session_state['data'] = fetch_data(supabase)
                if 'trigger_refresh' in st.session_state:
                    st.session_state['trigger_refresh'] = False
    
    # Auto-update loop
    while True:
        # Get the current data and apply filters
        current_data = st.session_state['data']
        filtered_data = filter_data(current_data, search_term, filter_column)
        
        # Update the UI with the latest data
        with data_table_placeholder.container():
            # Check for new data if auto-update is enabled
            if st.session_state['auto_update']:
                if supabase:
                    new_data = fetch_data(supabase)
                    
                    # Check if we have new data (more rows than before)
                    if len(new_data) > len(current_data):
                        st.success("✅ New data detected and loaded!")
                        st.session_state['data'] = new_data
                        filtered_data = filter_data(new_data, search_term, filter_column)
            
            # Display the data table
            if not filtered_data.empty:
                ui.table(data=filtered_data, maxHeight=500, key=f"data_table_{int(time.time())}")
                
                # Display record count and last check time
                current_time = datetime.now().strftime("%H:%M:%S")
                st.write(f"Showing {len(filtered_data)} records")
                if st.session_state['auto_update']:
                    st.write(f"Last checked: {current_time} (updating every {st.session_state['poll_interval']} seconds)")
                else:
                    st.write(f"Last updated: {current_time} (auto-update disabled)")
            else:
                st.info("No data available or no results match your search criteria.")
        
        # Wait for the specified interval before checking again
        time.sleep(st.session_state['poll_interval'] if st.session_state['auto_update'] else 3600)
        
        # If auto-update is disabled, break out of the loop
        if not st.session_state['auto_update']:
            break
            
elif tab_selection == "Statistics":
    # Create a placeholder for statistics content
    stats_placeholder = st.empty()
    
    # Get data for stats
    if 'data' in st.session_state and not st.session_state['data'].empty:
        df = st.session_state['data']
        
        with stats_placeholder.container():
            st.header("Data Statistics")
            
            # Display basic statistics
            st.subheader("Summary")
            cols = st.columns(3)
            
            with cols[0]:
                ui.card(
                    title="Total Records", 
                    content=str(len(df)), 
                    description="Number of entries in database", 
                    key="card1"
                ).render()
            
            with cols[1]:
                ui.card(
                    title="Unique Plate Numbers", 
                    content=str(df['Plate Number'].nunique()), 
                    description="Count of distinct plates", 
                    key="card2"
                ).render()
            
            with cols[2]:
                ui.card(
                    title="Unique Call Signs", 
                    content=str(df['Call Sign'].nunique()), 
                    description="Count of distinct call signs", 
                    key="card3"
                ).render()
            
            # Show auto-update status
            st.subheader("Update Status")
            if st.session_state['auto_update']:
                st.success(f"✅ Auto-updates are enabled. Switch to the Data Table tab to see live updates.")
            else:
                st.warning("⚠️ Auto-updates are disabled. Enable it in the sidebar to get live updates.")
    else:
        with stats_placeholder.container():
            st.info("No data available yet. Switch to Data Table tab first.")

elif tab_selection == "Settings":
    settings_placeholder = st.empty()
    
    with settings_placeholder.container():
        st.header("Application Settings")
        
        # Dark mode toggle
        dark_mode = ui.switch(default_checked=True, label="Dark Mode", key="dark_mode_switch")
        
        # Auto-update settings
        st.subheader("Auto-Update Explanation")
        auto_update_explanation = """
        This application features automatic data refreshing from your Supabase database.
        
        How it works:
        1. The app will periodically check for new data at your specified interval
        2. If new data is detected, it will be automatically loaded
        3. A notification will appear briefly to inform you of the update
        4. The table will remain stable and won't reset your scroll position
        
        To enable or disable auto-updates, use the toggle in the sidebar.
        """
        st.markdown(auto_update_explanation)
        
        # Export options
        st.subheader("Export Options")
        export_options = [
            {"label": "CSV", "value": "CSV", "id": "e1"},
            {"label": "Excel", "value": "Excel", "id": "e2"},
            {"label": "JSON", "value": "JSON", "id": "e3"}
        ]
        export_format = ui.radio_group(options=export_options, default_value="CSV", key="export_radio")
        
        if 'data' in st.session_state and not st.session_state['data'].empty:
            df = st.session_state['data']
            
            export_btn = ui.button("Export Data", variant="outline", key="export_btn")
            if export_btn:
                if export_format == "CSV":
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="alpha_data.csv",
                        mime="text/csv",
                    )
                elif export_format == "Excel":
                    # For Excel, we need to use a BytesIO object
                    import io
                    buffer = io.BytesIO()
                    df.to_excel(buffer, index=False)
                    buffer.seek(0)
                    st.download_button(
                        label="Download Excel",
                        data=buffer,
                        file_name="alpha_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                elif export_format == "JSON":
                    json = df.to_json(orient="records")
                    st.download_button(
                        label="Download JSON",
                        data=json,
                        file_name="alpha_data.json",
                        mime="application/json",
                    )
        else:
            st.error("No data available to export. Switch to the Data Table tab first.")
        
        # About section
        st.subheader("About")
        st.write("This application was created using Streamlit and the streamlit-shadcn-ui package.")
        st.write("Database: Supabase with auto-updates")
        st.write("Table: alpha (id, plate_number, call_sign)")

        # Help dialog
        help_btn = ui.button("Need Help?", key="help_btn")
        ui.alert_dialog(
            show=help_btn, 
            title="Database Connection Help", 
            description="This app uses Streamlit secrets to connect to your Supabase database. Make sure your secrets.toml file is properly configured with your Supabase URL and API key.", 
            confirm_label="OK", 
            cancel_label="Cancel", 
            key="help_dialog"
        )

# Footer
st.divider()
st.caption("Created with Streamlit and shadcn UI components.")