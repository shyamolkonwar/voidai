
import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import json

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8001/query" # IMPORTANT: Replace with your actual backend URL
st.set_page_config(page_title="FloatChat", layout="centered")

# --- Design & Styling ---
# Minimalist, monochromatic theme is handled by Streamlit's base theme.
# For the "Inter" font, a more complex setup is needed, so we'll stick to the default sans-serif for this simple app.
st.title("FloatChat")
st.markdown("Query oceanographic float data. For example: `Show me salinity profiles near the equator in March 2023`")

# --- Helper Functions ---
def display_map_and_table(data, summary):
    """Displays both map and table for geographic data."""
    st.markdown(f"> {summary}")
    
    # Extract latitude and longitude from the data rows
    if not data or not isinstance(data, list) or len(data) == 0:
        st.warning("Map data is incomplete.")
        return
    
    # Check if the data contains latitude and longitude fields
    has_coords = any('latitude' in row and 'longitude' in row for row in data if isinstance(row, dict))
    if not has_coords:
        st.warning("Map data is incomplete - no coordinate information found.")
        return
    
    # Extract coordinates and create dataframe
    map_data = []
    for i, row in enumerate(data):
        if isinstance(row, dict) and 'latitude' in row and 'longitude' in row:
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                # Create tooltip with available information
                tooltip_info = []
                for key, value in row.items():
                    if key not in ['latitude', 'longitude'] and value is not None:
                        tooltip_info.append(f"{key}: {value}")
                tooltip = f"Point {i+1}" + (f"\n{chr(10).join(tooltip_info[:3])}" if tooltip_info else "")
                
                map_data.append({
                    "lat": lat,
                    "lon": lon,
                    "tooltip": tooltip
                })
            except (ValueError, TypeError):
                continue  # Skip rows with invalid coordinates
    
    if not map_data:
        st.warning("No valid coordinate data found.")
        return
        
    map_df = pd.DataFrame(map_data)

    # Display the map
    st.subheader("Map View")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["lon", "lat"],
        get_color="[200, 30, 0, 160]",  # Red for visibility on a map
        get_radius=10000, # Radius in meters
        pickable=True,
    )

    # Set the initial view state
    view_state = pdk.ViewState(
        latitude=map_df["lat"].mean(),
        longitude=map_df["lon"].mean(),
        zoom=3,
        pitch=0,
    )

    # Render the deck.gl map
    st.pydeck_chart(pdk.Deck(
        map_style='''mapbox://styles/mapbox/light-v9''',
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "{tooltip}"}
    ))
    
    # Display the table
    st.subheader("Data Table")
    df = pd.DataFrame(data)
    
    # Format numeric columns for better readability
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32']:
            try:
                # Round to 4 decimal places for readability
                df[col] = df[col].round(4)
            except:
                pass
    
    # Display with pagination if there are many rows
    if len(df) > 10:
        st.write(f"Showing first 10 rows of {len(df)} total rows")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Add expandable section for full data
        with st.expander("View all data"):
            st.dataframe(df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

def display_table(data, summary):
    """Displays tabular data."""
    st.markdown(f"> {summary}")
    if not data:
        st.warning("Table data is empty.")
        return
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

def display_text(summary):
    """Displays a simple text summary."""
    st.markdown(f"> {summary}")

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["type"] == "map":
            display_map_and_table(message["content"]["data"], message["content"]["summary"])
        elif message["type"] == "table":
            display_table(message["content"]["data"], message["content"]["summary"])
        else: # text or user query
            st.markdown(message["content"])


# Accept user input
if prompt := st.chat_input("What are you looking for?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Backend Communication ---
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(BACKEND_URL, json={"query": prompt})
                response.raise_for_status()  # Raise an exception for bad status codes
                
                response_data = response.json()
                response_type = response_data.get("type", "text")
                
                # Store and display the appropriate response type
                if response_type == "map":
                    display_map_and_table(response_data.get("data"), response_data.get("summary", "Map response:"))
                    st.session_state.messages.append({"role": "assistant", "type": "map", "content": response_data})
                
                elif response_type == "table":
                    display_table(response_data.get("data"), response_data.get("summary", "Table response:"))
                    st.session_state.messages.append({"role": "assistant", "type": "table", "content": response_data})

                else: # "text" or any other case
                    summary = response_data.get("summary", "Sorry, I encountered an issue.")
                    display_text(summary)
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": summary})

            except requests.exceptions.RequestException as e:
                error_message = f"Could not connect to the backend at `{BACKEND_URL}`. Please ensure it's running. Error: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": error_message})
            except json.JSONDecodeError:
                error_message = "Received an invalid response from the backend. Expected JSON."
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": error_message})

