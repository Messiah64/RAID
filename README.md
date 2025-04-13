# Supabase Data Viewer with Streamlit-Shadcn

A modern, elegant Streamlit application to view and query your Supabase "alpha" table data using streamlit-shadcn-ui components.

## Features

- 🔄 **Smart polling** - Checks for new database entries at customizable intervals (1, 3, or 5 seconds)
- 🔔 New data notifications that alert you when changes are detected
- 🔐 Secure connection to Supabase using Streamlit secrets
- 🔍 Search and filter functionality across all columns
- 📊 Beautiful data presentation with properly labeled columns
- 📈 Basic statistics and insights with card visualizations
- 💾 Export data in multiple formats (CSV, Excel, JSON)
- 🌓 Dark mode support with easy toggling

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt

# Note: Make sure you have the latest version of streamlit-shadcn-ui
pip install streamlit-shadcn-ui --upgrade
```

### 2. Configure Environment Variables

1. Copy `.env.template` to a new file named `.env`
2. Edit the `.env` file and add your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_api_key_here
   ```

### 3. Run the Application

```bash
streamlit run app.py
```

## Usage Guide

1. **Connect to Database**:
   - Enter your Supabase URL and API key in the sidebar (if not using environment variables)
   - Click "Connect to Database"

2. **View and Search Data**:
   - Use the search box to find specific records
   - Filter by column using the dropdown
   - Click "Refresh Data" to update the view

3. **Statistics**:
   - Switch to the "Statistics" tab to see data insights
   - View counts of unique values and other metrics

4. **Export Data**:
   - Go to the "Settings" tab
   - Select your preferred export format
   - Click "Export Data" and then the download button

## Table Structure

The application is designed to work with the "alpha" table in Supabase:

```sql
create table public.alpha (
  id text not null default 'error_id'::text,
  plate_number text null default 'error_plate'::text,
  call_sign text null default 'error_callsign'::text,
  constraint alpha_pkey primary key (id)
) TABLESPACE pg_default;
```

## Customization

You can customize the application by:

1. Modifying the theme in the `theme()` function
2. Adding additional columns to the `columns` list
3. Creating new tabs with different visualizations
4. Extending the statistics functionality

## Troubleshooting

- If you encounter connection issues, verify your Supabase credentials
- Make sure your Supabase instance is running and accessible
- Check if the "alpha" table exists in your database
