import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate synthetic data
def generate_alert_data(start_date, num_days, num_systems):
    date_range = pd.date_range(start=start_date, periods=num_days * 24, freq='H')
    systems = [f'System {i+1}' for i in range(num_systems)]
    
    data = []
    for system in systems:
        base_rate = np.random.randint(1, 5)
        for date in date_range:
            if np.random.random() < 0.1:  # 10% chance of an alert
                severity = np.random.choice(['Low', 'Medium', 'High'], p=[0.6, 0.3, 0.1])
                num_alerts = np.random.poisson(base_rate)
                data.append({
                    'timestamp': date,
                    'system': system,
                    'num_alerts': num_alerts,
                    'severity': severity
                })
    
    return pd.DataFrame(data)

# Set page config
st.set_page_config(page_title="AIOps Alert Correlation Demo", layout="wide")

# Custom CSS to improve appearance
st.markdown("""
<style>
    .stTab {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .stTabContent {
        background-color: white;
        padding: 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.header("Simulation Controls")
num_days = st.sidebar.slider("Number of days to analyze", 7, 30, 14)
num_systems = st.sidebar.slider("Number of systems", 3, 10, 5)
correlation_window = st.sidebar.slider("Correlation window (hours)", 1, 24, 4)

# Generate data
start_date = datetime.now() - timedelta(days=num_days)
df = generate_alert_data(start_date, num_days, num_systems)

# Main content
st.title("Interactive Time-based Alert Correlation Demo")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Alert Timeline", "Correlation Analysis", "Insights", "Quiz"])

with tab1:
    st.header("Alert Timeline")
    
    fig = go.Figure()

    for system in df['system'].unique():
        system_data = df[df['system'] == system]
        fig.add_trace(go.Scatter(
            x=system_data['timestamp'],
            y=system_data['num_alerts'],
            mode='markers',
            name=system,
            marker=dict(
                size=system_data['num_alerts'] * 2,
                color=system_data['severity'].map({'Low': 'green', 'Medium': 'orange', 'High': 'red'}),
                symbol=system_data['severity'].map({'Low': 'circle', 'Medium': 'square', 'High': 'diamond'})
            )
        ))

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Alerts",
        hovermode="closest",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Correlation Analysis")

    col1, col2 = st.columns(2)

    with col1:
        selected_system = st.selectbox("Select a system to analyze", df['system'].unique())

        # Calculate correlations
        correlations = {}
        for system in df['system'].unique():
            if system != selected_system:
                df_selected = df[df['system'] == selected_system].set_index('timestamp')['num_alerts']
                df_other = df[df['system'] == system].set_index('timestamp')['num_alerts']
                
                aligned_data = pd.concat([df_selected, df_other], axis=1).fillna(0)
                aligned_data.columns = ['selected', 'other']
                
                rolling_corr = aligned_data['selected'].rolling(window=correlation_window).corr(aligned_data['other'])
                correlations[system] = rolling_corr.mean()

        # Display correlations
        correlation_df = pd.DataFrame.from_dict(correlations, orient='index', columns=['Correlation'])
        correlation_df = correlation_df.sort_values('Correlation', ascending=False)

        st.write(f"Average correlation with other systems (window: {correlation_window} hours):")
        st.dataframe(correlation_df)

    with col2:
        st.subheader("Potential Related Alerts")

        threshold = st.slider("Correlation threshold", 0.0, 1.0, 0.5, 0.05)
        related_systems = correlation_df[correlation_df['Correlation'] >= threshold].index.tolist()

        if related_systems:
            st.write(f"Systems with correlation >= {threshold}:")
            for system in related_systems:
                st.write(f"- {system}")
            
            # Display alerts from related systems
            st.write("Recent alerts from related systems:")
            related_alerts = df[df['system'].isin(related_systems)].sort_values('timestamp', ascending=False).head(10)
            st.dataframe(related_alerts[['timestamp', 'system', 'num_alerts', 'severity']])
        else:
            st.write(f"No systems found with correlation >= {threshold}")

    # Correlation heatmap
    st.subheader("Correlation Heatmap")

    # Calculate correlation matrix
    pivot_df = df.pivot_table(index='timestamp', columns='system', values='num_alerts', aggfunc='sum').fillna(0)
    corr_matrix = pivot_df.rolling(window=correlation_window).corr().groupby(level=0).mean()

    # Create heatmap
    heatmap = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='Viridis',
        zmin=-1, zmax=1
    ))

    heatmap.update_layout(
        title=f"Alert Correlation Heatmap (Window: {correlation_window} hours)",
        height=600
    )

    st.plotly_chart(heatmap, use_container_width=True)

with tab3:
    st.header("Insights")

    col1, col2, col3 = st.columns(3)

    total_alerts = df['num_alerts'].sum()
    most_active_system = df.groupby('system')['num_alerts'].sum().idxmax()
    most_severe_system = df[df['severity'] == 'High'].groupby('system').size().idxmax()

    with col1:
        st.metric("Total Alerts", total_alerts)
    with col2:
        st.metric("Most Active System", most_active_system)
    with col3:
        st.metric("System with Most High-Severity Alerts", most_severe_system)

    st.subheader("Alert Distribution by Severity")
    severity_dist = df['severity'].value_counts().sort_index()
    st.bar_chart(severity_dist)

    st.subheader("Top 5 Time Periods with Highest Alert Volume")
    hourly_alerts = df.set_index('timestamp').resample('H')['num_alerts'].sum().sort_values(ascending=False).head()
    st.bar_chart(hourly_alerts)

with tab4:
    st.header("AIOps Alert Correlation Quiz")

    questions = [
        {
            "question": "What is the primary goal of alert correlation in AIOps?",
            "options": [
                "To generate more alerts",
                "To reduce alert fatigue and identify root causes",
                "To increase system downtime",
                "To replace human operators entirely"
            ],
            "correct": 1,
            "explanation": "Alert correlation aims to reduce the number of alerts that operators need to handle by grouping related alerts together. This helps in identifying root causes more quickly and reduces alert fatigue."
        },
        {
            "question": "Which of the following is an example of time-based correlation?",
            "options": [
                "Grouping alerts from different systems that occur within 5 minutes of each other",
                "Correlating alerts based on the physical location of servers",
                "Grouping alerts with the same severity level",
                "Correlating alerts based on the team responsible for each system"
            ],
            "correct": 0,
            "explanation": "Time-based correlation groups alerts that occur close together in time. For example, if a network switch fails, it might trigger alerts from multiple dependent systems within a short time window."
        },
        {
            "question": "Why is the correlation window important in alert analysis?",
            "options": [
                "It determines the color of the alerts",
                "It sets the maximum number of alerts allowed",
                "It defines the time range for considering alerts as potentially related",
                "It specifies the minimum severity level of alerts to analyze"
            ],
            "correct": 2,
            "explanation": "The correlation window defines the time range within which alerts are considered potentially related. A larger window might catch more related alerts but could also introduce false correlations."
        },
        {
            "question": "What does a high correlation between two systems suggest?",
            "options": [
                "The systems are completely unrelated",
                "There might be a dependency or shared resource between the systems",
                "One system is more important than the other",
                "The alerts from these systems should be ignored"
            ],
            "correct": 1,
            "explanation": "A high correlation between two systems suggests that their alerts often occur together. This could indicate a dependency (e.g., a database and the application using it) or a shared resource (e.g., two systems on the same network segment)."
        },
        {
            "question": "How can insights from alert correlation be used to improve system reliability?",
            "options": [
                "By ignoring all alerts",
                "By adding more alerting systems",
                "By identifying recurring patterns and addressing root causes",
                "By increasing the threshold for all alerts"
            ],
            "correct": 2,
            "explanation": "Alert correlation can reveal patterns, such as cascading failures or recurring issues. By identifying these patterns, teams can address root causes, implement preventive measures, and improve overall system reliability."
        }
    ]

    # Initialize session state for quiz scores if not already done
    if 'quiz_score' not in st.session_state:
        st.session_state.quiz_score = 0
        st.session_state.questions_answered = 0

    for i, q in enumerate(questions):
        st.subheader(f"Question {i+1}")
        st.write(q["question"])
        
        # Use session state to store the user's answer
        if f'q{i}_answered' not in st.session_state:
            st.session_state[f'q{i}_answered'] = False

        if not st.session_state[f'q{i}_answered']:
            answer = st.radio(f"Select your answer for question {i+1}:", q["options"], key=f"q{i}")
            if st.button(f"Submit Answer for Question {i+1}"):
                st.session_state[f'q{i}_answered'] = True
                st.session_state.questions_answered += 1
                if q["options"].index(answer) == q["correct"]:
                    st.session_state.quiz_score += 1
                    st.success("Correct!")
                else:
                    st.error("Incorrect.")
                st.write(f"Explanation: {q['explanation']}")
        else:
            st.info(f"You've already answered this question. Explanation: {q['explanation']}")

    if st.session_state.questions_answered == len(questions):
        st.subheader("Quiz Complete!")
        st.write(f"Your score: {st.session_state.quiz_score}/{len(questions)}")
        if st.button("Retake Quiz"):
            for i in range(len(questions)):
                st.session_state[f'q{i}_answered'] = False
            st.session_state.quiz_score = 0
            st.session_state.questions_answered = 0
            st.experimental_rerun()