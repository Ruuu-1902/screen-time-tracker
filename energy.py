import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from datetime import datetime, timedelta
import time

# Set page config
st.set_page_config(page_title="Time Blocking Color Wheel", layout="wide")

# Initialize session state variables
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'energy_patterns' not in st.session_state:
    # Default energy pattern (can be customized)
    st.session_state.energy_patterns = {
        "Morning (6-10 AM)": "High",
        "Mid-day (10-2 PM)": "Medium", 
        "Afternoon (2-6 PM)": "Medium",
        "Evening (6-10 PM)": "Low"
    }

# Color maps for different energy levels
energy_colors = {
    "High": "#FF5733",    # Bright orange/red
    "Medium": "#33A8FF",  # Blue
    "Low": "#9333FF"      # Purple
}

# App title and description
st.title("Time Blocking Color Wheel")
st.markdown("""
This app helps you match tasks to your natural energy patterns throughout the day.
Instead of scheduling by rigid time blocks, organize your work based on your energy levels.
""")

# Sidebar for configurations
with st.sidebar:
    st.header("Settings")
    
    # Energy pattern editor
    st.subheader("Your Energy Patterns")
    st.write("Define your typical energy levels during different parts of the day")
    
    # Let user customize their energy patterns
    for time_block, default_energy in st.session_state.energy_patterns.items():
        new_energy = st.selectbox(
            f"Energy level during {time_block}",
            options=["High", "Medium", "Low"],
            index=["High", "Medium", "Low"].index(default_energy),
            key=f"energy_{time_block}"
        )
        st.session_state.energy_patterns[time_block] = new_energy
    
    # Task category definitions
    st.subheader("Task Categories")
    st.write("Define what type of tasks work best at each energy level")
    
    task_types = {
        "High": st.text_area("High energy tasks (comma separated)", 
                            "Creative work, Problem solving, Learning new skills, Strategic thinking"),
        "Medium": st.text_area("Medium energy tasks (comma separated)", 
                              "Meetings, Routine work, Email management, Planning"),
        "Low": st.text_area("Low energy tasks (comma separated)", 
                           "Administrative tasks, Documentation, Low-stakes reading, Organized filing")
    }

# Create two columns for the main interface
col1, col2 = st.columns([3, 2])

with col1:
    st.header("Add New Tasks")
    
    # Task input form
    with st.form("task_form"):
        task_name = st.text_input("Task Description")
        task_energy = st.select_slider("Required Energy Level", 
                                      options=["Low", "Medium", "High"])
        task_duration = st.number_input("Estimated Duration (minutes)", 
                                       min_value=15, max_value=180, step=15, value=30)
        task_category = st.text_input("Category (optional)")
        
        submit_button = st.form_submit_button("Add Task")
        
        if submit_button and task_name:
            # Add task to session state
            st.session_state.tasks.append({
                "name": task_name,
                "energy": task_energy,
                "duration": task_duration,
                "category": task_category,
                "completed": False,
                "id": int(time.time())  # Use timestamp as unique ID
            })
            st.success(f"Added task: {task_name}")

    # Display and manage current tasks
    st.header("Your Task List")
    
    if not st.session_state.tasks:
        st.info("No tasks added yet. Add some tasks to get started!")
    else:
        # Group tasks by energy level
        for energy in ["High", "Medium", "Low"]:
            matching_tasks = [t for t in st.session_state.tasks if t["energy"] == energy and not t["completed"]]
            
            if matching_tasks:
                st.subheader(f"{energy} Energy Tasks")
                for task in matching_tasks:
                    cols = st.columns([4, 1, 1])
                    with cols[0]:
                        st.write(f"**{task['name']}** ({task['duration']} min)")
                    with cols[1]:
                        if st.button("Complete", key=f"complete_{task['id']}"):
                            # Mark task as completed
                            for t in st.session_state.tasks:
                                if t["id"] == task["id"]:
                                    t["completed"] = True
                            st.rerun()
                    with cols[2]:
                        if st.button("Remove", key=f"remove_{task['id']}"):
                            # Remove task from list
                            st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task["id"]]
                            st.rerun()

with col2:
    st.header("Time Blocking Color Wheel")
    
    # Create the color wheel visualization
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Convert energy patterns to data for the wheel
    time_blocks = list(st.session_state.energy_patterns.keys())
    energy_levels = list(st.session_state.energy_patterns.values())
    
    # Calculate angles for time blocks
    block_count = len(time_blocks)
    theta = np.linspace(0.0, 2 * np.pi, block_count, endpoint=False)
    width = 2 * np.pi / block_count
    
    # Create the wheel (outer ring for time blocks)
    bars = ax.bar(
        theta, 
        height=1.0, 
        width=width, 
        bottom=1.0,  # Inner radius
        alpha=0.7,
        color=[energy_colors[level] for level in energy_levels]
    )
    
    # Add time block labels
    for angle, label in zip(theta, time_blocks):
        x = (1.0 + 0.5) * np.cos(angle + width/2)  # Middle of the bar
        y = (1.0 + 0.5) * np.sin(angle + width/2)
        ax.text(angle + width/2, 2.2, label, 
                ha='center', va='center', rotation=np.degrees(angle + width/2))
    
    # Add task markers to the wheel
    active_tasks = [t for t in st.session_state.tasks if not t["completed"]]
    
    if active_tasks:
        # Group tasks by energy level
        for energy_level in ["High", "Medium", "Low"]:
            matching_tasks = [t for t in active_tasks if t["energy"] == energy_level]
            
            if matching_tasks:
                # Find time blocks with this energy level
                matching_blocks = [i for i, level in enumerate(energy_levels) if level == energy_level]
                
                if matching_blocks:
                    # Place tasks in the matching time blocks
                    for i, task in enumerate(matching_tasks):
                        # Distribute tasks within matching time blocks
                        block_idx = matching_blocks[i % len(matching_blocks)]
                        task_angle = theta[block_idx] + width/2
                        
                        # Calculate position (vary radius slightly for multiple tasks)
                        offset = (i // len(matching_blocks)) * 0.15
                        radius = 1.5 - offset
                        
                        # Plot task marker
                        ax.plot(task_angle, radius, 'o', 
                                markersize=10, 
                                color='white', 
                                markeredgecolor=energy_colors[energy_level])
                        
                        # Add task name
                        task_name = task["name"]
                        if len(task_name) > 15:
                            task_name = task_name[:12] + "..."
                            
                        ax.text(task_angle, radius + 0.1, 
                                task_name, 
                                ha='center', va='bottom', 
                                fontsize=8,
                                rotation=np.degrees(task_angle) - 90)
    
    # Configure the polar plot
    ax.set_theta_zero_location("N")  # 0 at the top
    ax.set_theta_direction(-1)  # Clockwise
    ax.set_rticks([])  # No radial ticks
    ax.set_xticks([])  # No angular ticks
    ax.spines['polar'].set_visible(False)  # Hide the outer circle
    
    # Add center labels
    ax.text(0, 0, "Time\nBlocking\nWheel", ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Add a legend for energy levels
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color, markersize=10, 
                                  label=level)
                      for level, color in energy_colors.items()]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.15))
    
    st.pyplot(fig)
    
    # Display energy level recommendations
    st.subheader("Recommended Task Types")
    for energy, tasks in task_types.items():
        st.markdown(f"**{energy} Energy:** {tasks}")

# Display summary statistics
st.header("Task Summary")
if st.session_state.tasks:
    total_tasks = len(st.session_state.tasks)
    completed_tasks = len([t for t in st.session_state.tasks if t["completed"]])
    total_minutes = sum(t["duration"] for t in st.session_state.tasks)
    
    # Create metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tasks", total_tasks)
    col2.metric("Completed", f"{completed_tasks}/{total_tasks}")
    col3.metric("Total Time", f"{total_minutes} min")
    
    # Show task distribution by energy level
    st.subheader("Task Distribution by Energy Level")
    
    energy_counts = {
        "High": len([t for t in st.session_state.tasks if t["energy"] == "High"]),
        "Medium": len([t for t in st.session_state.tasks if t["energy"] == "Medium"]),
        "Low": len([t for t in st.session_state.tasks if t["energy"] == "Low"])
    }
    
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(energy_counts.keys(), energy_counts.values(), color=[energy_colors[k] for k in energy_counts.keys()])
    ax.set_ylabel("Number of Tasks")
    st.pyplot(fig)
else:
    st.info("Add some tasks to see your summary statistics!")

# Add a completed tasks section (collapsible)
with st.expander("View Completed Tasks"):
    completed = [t for t in st.session_state.tasks if t["completed"]]
    if completed:
        for task in completed:
            st.write(f"✓ {task['name']} ({task['energy']} energy, {task['duration']} min)")
            
        if st.button("Clear Completed Tasks"):
            st.session_state.tasks = [t for t in st.session_state.tasks if not t["completed"]]
            st.success("Cleared all completed tasks!")
            st.rerun()
    else:
        st.write("No completed tasks yet.")

# Add instructions for using the app
with st.expander("How to Use This App"):
    st.markdown("""
    ### How to Use the Time Blocking Color Wheel
    
    1. **Define your energy patterns** in the sidebar to match your natural daily rhythms
    2. **Add tasks** with their estimated duration and required energy level
    3. **View the color wheel** to see how tasks align with your energy patterns
    4. **Complete tasks** throughout the day based on your current energy level
    
    The color wheel helps you visualize when to do different types of work based on your energy, rather than just the clock time. This works with your body's natural rhythms instead of against them.
    
    **Tips:**
    - Schedule high-energy tasks during your peak energy periods
    - Save administrative and routine tasks for low-energy periods
    - Review your wheel at the start of each day to plan effectively
    - Adjust your energy patterns if you notice they don't match reality
    """)

# Footer
st.markdown("---")
st.caption("Time Blocking Color Wheel - Work with your natural energy patterns")