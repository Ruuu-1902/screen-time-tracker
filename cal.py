import streamlit as st
import os
import datetime
import pickle
import pandas as pd
import numpy as np
import altair as alt
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Set page config with improved styling
st.set_page_config(
    page_title="Calendar Assistant",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    h1, h2, h3 {
        padding-top: 1rem;
    }
    .event-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .highlight {
        background-color: #ffffcc;
        padding: 2px 5px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    Gets authenticated Google Calendar service
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are not available or are invalid, ask the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Need to specify the path to your credentials.json file
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return the service
    service = build('calendar', 'v3', credentials=creds)
    return service

def create_calendar_heatmap(events_data, start_date, end_date):
    """
    Create a calendar heatmap visualization of events
    """
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Create a DataFrame with dates
    calendar_df = pd.DataFrame({
        'date': date_range,
        'count': 0
    })
    
    # Count events per day
    for event in events_data:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if 'T' in start:  # This is a dateTime
            event_date = datetime.datetime.fromisoformat(start.replace('Z', '+00:00')).date()
        else:  # This is a date
            event_date = datetime.datetime.strptime(start, "%Y-%m-%d").date()
        
        # Increment count for the day
        idx = calendar_df[calendar_df['date'].dt.date == event_date].index
        if len(idx) > 0:
            calendar_df.loc[idx, 'count'] += 1
    
    # Add day and month for grouping
    calendar_df['day'] = calendar_df['date'].dt.day_name()
    calendar_df['month'] = calendar_df['date'].dt.month_name()
    
    # Create heatmap with Altair
    heatmap = alt.Chart(calendar_df).mark_rect().encode(
        x=alt.X('date:O', title='Date', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('day:O', title='Day', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
        color=alt.Color('count:Q', scale=alt.Scale(scheme='blues'), legend=alt.Legend(title='Event Count')),
        tooltip=['date', 'day', 'count']
    ).properties(
        width=800,
        height=300,
        title='Calendar Activity Heatmap'
    )
    
    return heatmap

# Initialize session state if not already done
if 'service' not in st.session_state:
    st.session_state.service = None
if 'view' not in st.session_state:
    st.session_state.view = "upcoming"  # Default view

# Sidebar for navigation and authentication
with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/product/2x/calendar_2020q4_48dp.png", width=50)
    st.title("Calendar Assistant")
    
    # Authentication section
    if st.session_state.service is None:
        st.subheader("Authentication")
        auth_button = st.button("Connect to Google Calendar", key="auth_button")
        
        if auth_button:
            try:
                with st.spinner("Authenticating..."):
                    st.session_state.service = get_calendar_service()
                st.success("Authentication successful!")
                st.rerun()  # Updated from experimental_rerun
            except Exception as e:
                st.error(f"Authentication failed: {e}")
    else:
        st.success("✓ Connected to Google Calendar")
        
        # Navigation
        st.subheader("Navigation")
        views = {
            "upcoming": "Upcoming Events",
            "create": "Create New Event",
            "analytics": "Activity Analytics"
        }
        
        for key, label in views.items():
            if st.button(label, key=f"nav_{key}"):
                st.session_state.view = key
                st.rerun()  # Updated from experimental_rerun
        
        # Logout option
        if st.button("Logout", key="logout"):
            if os.path.exists('token.pickle'):
                os.remove('token.pickle')
            st.session_state.service = None
            st.rerun()  # Updated from experimental_rerun

# Main content area
if st.session_state.service is None:
    # Welcome screen
    st.title("Welcome to Calendar Assistant")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        ### Manage your schedule with ease
        
        This app allows you to:
        - 📆 View your upcoming events
        - ➕ Create new calendar events
        - 📊 Analyze your schedule with activity heatmaps
        
        Get started by connecting your Google Calendar using the button in the sidebar.
        """)
    
    with col2:
        st.image("https://www.gstatic.com/images/branding/product/2x/calendar_2020q4_512dp.png", width=200)
        
else:
    # Different views based on navigation
    if st.session_state.view == "upcoming":
        st.title("Upcoming Events")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", datetime.date.today())
        with col2:
            default_end = datetime.date.today() + datetime.timedelta(days=14)
            end_date = st.date_input("To", default_end)
        
        # Convert to datetime and format for API
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min).isoformat() + 'Z'
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max).isoformat() + 'Z'
        
        # Number of events to fetch
        max_events = st.slider("Maximum number of events to display", 1, 50, 10)
        
        # Get events
        with st.spinner("Loading events..."):
            events_result = st.session_state.service.events().list(
                calendarId='primary', 
                timeMin=start_datetime,
                timeMax=end_datetime,
                maxResults=max_events, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
        
        if not events:
            st.info("No events found for the selected period.")
        else:
            # Group events by date
            events_by_date = {}
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Format the start time for better display
                if 'T' in start:  # This is a dateTime
                    start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    event_date = start_dt.date()
                    formatted_time = start_dt.strftime("%H:%M")
                else:  # This is a date
                    event_date = datetime.datetime.strptime(start, "%Y-%m-%d").date()
                    formatted_time = "All day"
                
                if event_date not in events_by_date:
                    events_by_date[event_date] = []
                
                # Extract color if available
                event_color = event.get('colorId', '0')
                
                events_by_date[event_date].append({
                    "time": formatted_time,
                    "summary": event.get('summary', 'Untitled Event'),
                    "description": event.get('description', ''),
                    "location": event.get('location', ''),
                    "color": event_color
                })
            
            # Display events by date
            for date in sorted(events_by_date.keys()):
                st.subheader(date.strftime("%A, %B %d, %Y"))
                
                for event in events_by_date[date]:
                    with st.container():
                        st.markdown(f"""
                        <div class="event-card">
                            <strong>{event['time']}</strong> - 
                            <span class="highlight">{event['summary']}</span>
                            {f"<br><small>📍 {event['location']}</small>" if event['location'] else ""}
                            {f"<br><small>{event['description']}</small>" if event['description'] else ""}
                        </div>
                        """, unsafe_allow_html=True)
    
    elif st.session_state.view == "create":
        st.title("Create New Event")
        
        # Event details form
        with st.form("new_event_form"):
            event_title = st.text_input("📝 Event Title", placeholder="Meeting with Team")
            
            col1, col2 = st.columns(2)
            with col1:
                event_date = st.date_input("📅 Event Date", datetime.date.today())
                all_day = st.checkbox("All Day Event")
                if not all_day:
                    event_time = st.time_input("🕒 Start Time", datetime.time(hour=9, minute=0))
                    
                    duration_options = {
                        "15 minutes": 15,
                        "30 minutes": 30,
                        "45 minutes": 45,
                        "1 hour": 60,
                        "1.5 hours": 90,
                        "2 hours": 120,
                        "3 hours": 180,
                        "Custom": -1
                    }
                    duration_choice = st.selectbox("⏱️ Duration", options=list(duration_options.keys()))
                    
                    if duration_choice == "Custom":
                        col_h, col_m = st.columns(2)
                        with col_h:
                            duration_hours = st.number_input("Hours", 0, 10, 1)
                        with col_m:
                            duration_minutes = st.number_input("Minutes", 0, 59, 0)
                        total_minutes = duration_hours * 60 + duration_minutes
                    else:
                        total_minutes = duration_options[duration_choice]
            
            with col2:
                event_description = st.text_area("📋 Event Description", placeholder="Discuss project progress...")
                event_location = st.text_input("📍 Location", placeholder="Conference Room A or https://meet.google.com/...")
                
                # Color selection for event
                colors = {
                    "Default": "0",
                    "Lavender": "1",
                    "Sage": "2",
                    "Grape": "3",
                    "Flamingo": "4",
                    "Banana": "5",
                    "Tangerine": "6",
                    "Peacock": "7",
                    "Graphite": "8",
                    "Blueberry": "9",
                    "Basil": "10",
                    "Tomato": "11"
                }
                event_color = st.selectbox("🎨 Event Color", options=list(colors.keys()))
            
            # Notification options
            notifications = st.multiselect(
                "🔔 Notifications",
                options=["10 minutes before", "30 minutes before", "1 hour before", "1 day before"],
                default=["10 minutes before"]
            )
            
            # Submit button
            submit_button = st.form_submit_button("Create Event")
        
        if submit_button:
            if not event_title:
                st.error("Please enter an event title")
            else:
                # Calculate start and end time
                if all_day:
                    # All-day event
                    start = {
                        'date': event_date.strftime('%Y-%m-%d'),
                        'timeZone': 'UTC',
                    }
                    end_date = event_date + datetime.timedelta(days=1)
                    end = {
                        'date': end_date.strftime('%Y-%m-%d'),
                        'timeZone': 'UTC',
                    }
                else:
                    # Timed event
                    start_datetime = datetime.datetime.combine(event_date, event_time)
                    end_datetime = start_datetime + datetime.timedelta(minutes=total_minutes)
                    
                    start = {
                        'dateTime': start_datetime.isoformat(),
                        'timeZone': 'UTC',
                    }
                    end = {
                        'dateTime': end_datetime.isoformat(),
                        'timeZone': 'UTC',
                    }
                
                # Create reminders if specified
                reminders = {
                    'useDefault': False,
                    'overrides': []
                }
                
                for notification in notifications:
                    if notification == "10 minutes before":
                        reminders['overrides'].append({'method': 'popup', 'minutes': 10})
                    elif notification == "30 minutes before":
                        reminders['overrides'].append({'method': 'popup', 'minutes': 30})
                    elif notification == "1 hour before":
                        reminders['overrides'].append({'method': 'popup', 'minutes': 60})
                    elif notification == "1 day before":
                        reminders['overrides'].append({'method': 'popup', 'minutes': 1440})
                
                # Define the event
                event = {
                    'summary': event_title,
                    'location': event_location,
                    'description': event_description,
                    'start': start,
                    'end': end,
                    'colorId': colors[event_color],
                    'reminders': reminders
                }
                
                # Create the event
                try:
                    with st.spinner("Creating event..."):
                        created_event = st.session_state.service.events().insert(calendarId='primary', body=event).execute()
                    
                    st.success("Event created successfully!")
                    
                    # Show event details
                    st.markdown(f"""
                    ### Event Details
                    **Title:** {event_title}  
                    **When:** {event_date.strftime('%A, %B %d, %Y')} {'' if all_day else event_time.strftime('%H:%M')}  
                    **Duration:** {"All day" if all_day else f"{total_minutes // 60}h {total_minutes % 60}m"}  
                    **Location:** {event_location if event_location else "Not specified"}
                    
                    [View in Google Calendar]({created_event.get('htmlLink')})
                    """)
                except Exception as e:
                    st.error(f"Failed to create event: {e}")
    
    elif st.session_state.view == "analytics":
        st.title("Calendar Activity Analytics")
        
        # Date range for analytics
        st.subheader("Select Date Range")
        col1, col2 = st.columns(2)
        with col1:
            # Default to 3 months back
            default_start = datetime.date.today() - datetime.timedelta(days=90)
            analytics_start = st.date_input("From Date", default_start, key="analytics_start")
        with col2:
            analytics_end = st.date_input("To Date", datetime.date.today(), key="analytics_end")
        
        # Fetch events for the selected period
        if analytics_start <= analytics_end:
            start_datetime = datetime.datetime.combine(analytics_start, datetime.time.min).isoformat() + 'Z'
            end_datetime = datetime.datetime.combine(analytics_end, datetime.time.max).isoformat() + 'Z'
            
            with st.spinner("Loading calendar data..."):
                # Fetch up to 1000 events for analytics
                events_result = st.session_state.service.events().list(
                    calendarId='primary', 
                    timeMin=start_datetime,
                    timeMax=end_datetime,
                    maxResults=1000, 
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
            
            if not events:
                st.info("No events found for the selected period.")
            else:
                # Show total events
                st.metric("Total Events", len(events))
                
                # Create and display the heatmap
                st.subheader("Calendar Activity Heatmap")
                st.markdown("This heatmap shows your calendar activity pattern. Darker colors indicate more events scheduled on that day.")
                
                heatmap = create_calendar_heatmap(events, analytics_start, analytics_end)
                st.altair_chart(heatmap, use_container_width=True)
                
                # Event distribution by day of week
                st.subheader("Event Distribution by Day of Week")
                
                # Collect day of week data
                day_counts = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
                
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    
                    if 'T' in start:  # This is a dateTime
                        event_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    else:  # This is a date
                        event_dt = datetime.datetime.strptime(start, "%Y-%m-%d")
                    
                    day_name = event_dt.strftime("%A")
                    day_counts[day_name] += 1
                
                # Create bar chart
                days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                days_df = pd.DataFrame({
                    "Day": days_order,
                    "Count": [day_counts[day] for day in days_order]
                })
                
                day_chart = alt.Chart(days_df).mark_bar().encode(
                    x=alt.X('Day:N', sort=days_order),
                    y='Count:Q',
                    color=alt.Color('Count:Q', scale=alt.Scale(scheme='blues')),
                    tooltip=['Day', 'Count']
                ).properties(
                    width='container',
                    height=300,
                    title='Number of Events by Day of Week'
                )
                
                st.altair_chart(day_chart, use_container_width=True)
                
                # Event duration analysis (for timed events only)
                st.subheader("Event Duration Analysis")
                
                timed_events = []
                for event in events:
                    start = event['start'].get('dateTime')
                    end = event['end'].get('dateTime')
                    
                    if start and end:  # Only include timed events
                        start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                        
                        duration_minutes = (end_dt - start_dt).total_seconds() / 60
                        
                        timed_events.append({
                            "summary": event.get('summary', 'Untitled'),
                            "duration_minutes": duration_minutes
                        })
                
                if timed_events:
                    # Create duration dataframe
                    duration_df = pd.DataFrame(timed_events)
                    
                    # Add duration categories
                    def categorize_duration(minutes):
                        if minutes <= 15:
                            return "0-15 minutes"
                        elif minutes <= 30:
                            return "16-30 minutes"
                        elif minutes <= 60:
                            return "31-60 minutes"
                        elif minutes <= 120:
                            return "1-2 hours"
                        else:
                            return "2+ hours"
                    
                    duration_df['category'] = duration_df['duration_minutes'].apply(categorize_duration)
                    
                    # Count by category
                    category_counts = duration_df['category'].value_counts().reset_index()
                    category_counts.columns = ['Duration', 'Count']
                    
                    # Order categories
                    category_order = ["0-15 minutes", "16-30 minutes", "31-60 minutes", "1-2 hours", "2+ hours"]
                    category_counts['Duration'] = pd.Categorical(
                        category_counts['Duration'], 
                        categories=category_order, 
                        ordered=True
                    )
                    category_counts = category_counts.sort_values('Duration')
                    
                    # Create chart
                    duration_chart = alt.Chart(category_counts).mark_bar().encode(
                        x='Duration:N',
                        y='Count:Q',
                        color=alt.Color('Count:Q', scale=alt.Scale(scheme='blues')),
                        tooltip=['Duration', 'Count']
                    ).properties(
                        width='container',
                        height=300,
                        title='Event Duration Distribution'
                    )
                    
                    st.altair_chart(duration_chart, use_container_width=True)
                    
                    # Show average meeting duration
                    avg_duration = duration_df['duration_minutes'].mean()
                    st.metric("Average Event Duration", f"{avg_duration:.1f} minutes")
                else:
                    st.info("No timed events found for duration analysis.")
        else:
            st.error("End date must be after start date")

# Footer
st.markdown("---")
st.markdown("Calendar Assistant | Built with Streamlit")