import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="AIOps Rule-based Correlation Demo", layout="wide")

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
    .small-font {
        font-size: 0.8rem;
    }
    .explanation {
        background-color: #e1f5fe;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Generate synthetic alert data (same as before)
def generate_alert_data(num_hours, num_services):
    alerts = []
    start_time = datetime.now() - timedelta(hours=num_hours)
    services = [f"Service_{i}" for i in range(1, num_services + 1)]
    alert_types = ['CPU Usage', 'Memory Usage', 'Disk Space', 'Network Latency', 'Error Rate']
    
    for hour in range(num_hours):
        current_time = start_time + timedelta(hours=hour)
        for service in services:
            if np.random.random() < 0.2:  # 20% chance of an alert
                alert_type = np.random.choice(alert_types)
                severity = np.random.choice(['Low', 'Medium', 'High'], p=[0.6, 0.3, 0.1])
                value = np.random.randint(50, 100)
                alerts.append({
                    'timestamp': current_time,
                    'service': service,
                    'alert_type': alert_type,
                    'severity': severity,
                    'value': value,
                    'message': f"{alert_type} alert on {service}: {value}%"
                })
    return pd.DataFrame(alerts)

# Sidebar controls
st.sidebar.header("Simulation Controls")
num_hours = st.sidebar.slider("Number of hours to simulate", 1, 48, 24)
num_services = st.sidebar.slider("Number of services", 3, 10, 5)

# Generate data
df = generate_alert_data(num_hours, num_services)

# Main content
st.title("Interactive Rule-based Alert Correlation Demo")

st.markdown("""
<div class="explanation">
<h4>What is Rule-based Alert Correlation?</h4>
<p>Rule-based alert correlation is a method used in IT operations to group related alerts together based on predefined criteria. This helps reduce alert noise and allows operators to focus on significant issues more easily.</p>
<p><strong>Example:</strong> Imagine you have a rule that says "Group all high-severity CPU usage alerts from the same service within 15 minutes." This could help you identify when a service is experiencing sustained high CPU usage, which might indicate a more serious problem than occasional spikes.</p>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Alert Dashboard", "Rule Creation", "Correlated Alerts", "Quiz"])

with tab1:
    st.header("Alert Dashboard")
    
    st.markdown("""
    <div class="explanation">
    This dashboard provides an overview of all alerts in the system. It helps you understand the distribution of alerts across different services and types, as well as their occurrence over time.
    </div>
    """, unsafe_allow_html=True)

    # Alert count by service
    service_counts = df['service'].value_counts()
    fig_service = px.bar(service_counts, x=service_counts.index, y=service_counts.values,
                         labels={'x': 'Service', 'y': 'Number of Alerts'},
                         title='Alerts by Service')
    st.plotly_chart(fig_service, use_container_width=True)
    
    st.markdown("""
    <div class="explanation">
    <strong>Interpretation:</strong> This chart shows which services are generating the most alerts. 
    A service with an unusually high number of alerts might require closer investigation.
    </div>
    """, unsafe_allow_html=True)

    # Alert count by type
    type_counts = df['alert_type'].value_counts()
    fig_type = px.pie(values=type_counts.values, names=type_counts.index,
                      title='Distribution of Alert Types')
    st.plotly_chart(fig_type, use_container_width=True)
    
    st.markdown("""
    <div class="explanation">
    <strong>Interpretation:</strong> This pie chart shows the proportion of different types of alerts. 
    If one type of alert is dominating, it might indicate a systemic issue.
    </div>
    """, unsafe_allow_html=True)

    # Alert timeline
    fig_timeline = px.scatter(df, x='timestamp', y='service', color='severity',
                              hover_data=['alert_type', 'value', 'message'],
                              labels={'timestamp': 'Time', 'service': 'Service'},
                              title='Alert Timeline')
    fig_timeline.update_traces(marker=dict(size=10))
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("""
    <div class="explanation">
    <strong>Interpretation:</strong> This timeline shows when alerts are occurring across different services. 
    Look for patterns like multiple services having alerts at the same time, which might indicate a broader issue.
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.header("Rule Creation")

    st.markdown("""
    <div class="explanation">
    Here you can create rules to correlate alerts. Each rule defines criteria for grouping related alerts together.
    <br><br>
    <strong>Example:</strong> A rule might say "Group all high-severity memory usage alerts from Service_1 that exceed 90% within a 10-minute window." 
    This could help identify sustained memory issues in Service_1.
    </div>
    """, unsafe_allow_html=True)

    # Rule creation form
    with st.form("rule_creation"):
        st.subheader("Create a New Rule")
        rule_name = st.text_input("Rule Name", help="Give your rule a descriptive name")
        
        col1, col2 = st.columns(2)
        with col1:
            service = st.selectbox("Service", ['Any'] + list(df['service'].unique()), help="Select a specific service or 'Any' for all services")
            alert_type = st.selectbox("Alert Type", ['Any'] + list(df['alert_type'].unique()), help="Select a specific alert type or 'Any' for all types")
        with col2:
            severity = st.selectbox("Severity", ['Any', 'Low', 'Medium', 'High'], help="Select the minimum severity level for alerts")
            threshold = st.number_input("Value Threshold", min_value=0, max_value=100, value=75, help="Minimum value for the alert to be considered (e.g., 75% CPU usage)")
        
        time_window = st.slider("Time Window (minutes)", 1, 60, 15, help="Time range within which to group related alerts")
        
        submitted = st.form_submit_button("Create Rule")
        
        if submitted:
            if rule_name:
                if 'rules' not in st.session_state:
                    st.session_state.rules = []
                
                new_rule = {
                    'name': rule_name,
                    'service': service,
                    'alert_type': alert_type,
                    'severity': severity,
                    'threshold': threshold,
                    'time_window': time_window
                }
                st.session_state.rules.append(new_rule)
                st.success(f"Rule '{rule_name}' created successfully!")
            else:
                st.error("Please provide a name for the rule.")

    # Display existing rules
    if 'rules' in st.session_state and st.session_state.rules:
        st.subheader("Existing Rules")
        for i, rule in enumerate(st.session_state.rules):
            st.write(f"**{rule['name']}**")
            st.markdown(f"""
            <p class="small-font">
            Service: {rule['service']}, 
            Alert Type: {rule['alert_type']}, 
            Severity: {rule['severity']}, 
            Threshold: {rule['threshold']}, 
            Time Window: {rule['time_window']} minutes
            </p>
            """, unsafe_allow_html=True)
            if st.button(f"Delete Rule {i+1}"):
                st.session_state.rules.pop(i)
                st.experimental_rerun()
    else:
        st.info("No rules created yet. Use the form above to create rules.")

with tab3:
    st.header("Correlated Alerts")

    st.markdown("""
    <div class="explanation">
    This section shows you the results of applying your correlation rules to the alert data. 
    It helps you see patterns and related alerts that might indicate larger issues.
    <br><br>
    <strong>Example:</strong> If you see multiple high-severity CPU alerts grouped together for a single service, 
    it might indicate a persistent performance problem that requires immediate attention.
    </div>
    """, unsafe_allow_html=True)

    if 'rules' in st.session_state and st.session_state.rules:
        selected_rule = st.selectbox("Select a rule to apply", 
                                     [rule['name'] for rule in st.session_state.rules])
        
        rule = next(rule for rule in st.session_state.rules if rule['name'] == selected_rule)
        
        # Apply the rule to the dataset
        filtered_df = df.copy()
        if rule['service'] != 'Any':
            filtered_df = filtered_df[filtered_df['service'] == rule['service']]
        if rule['alert_type'] != 'Any':
            filtered_df = filtered_df[filtered_df['alert_type'] == rule['alert_type']]
        if rule['severity'] != 'Any':
            filtered_df = filtered_df[filtered_df['severity'] == rule['severity']]
        filtered_df = filtered_df[filtered_df['value'] >= rule['threshold']]
        
        # Group alerts within the time window
        correlated_alerts = []
        for _, group in filtered_df.groupby('service'):
            group = group.sort_values('timestamp')
            for i, alert in group.iterrows():
                window_end = alert['timestamp'] + timedelta(minutes=rule['time_window'])
                correlated = group[(group['timestamp'] >= alert['timestamp']) & 
                                   (group['timestamp'] <= window_end)]
                if len(correlated) > 1:
                    correlated_alerts.append(correlated)
        
        if correlated_alerts:
            st.subheader(f"Correlated Alerts for Rule: {selected_rule}")
            for i, alerts in enumerate(correlated_alerts):
                st.write(f"Correlation Group {i+1}")
                st.dataframe(alerts[['timestamp', 'service', 'alert_type', 'severity', 'value', 'message']])
                
            # Visualization of correlated alerts
            fig = go.Figure()
            for i, alerts in enumerate(correlated_alerts):
                fig.add_trace(go.Scatter(
                    x=alerts['timestamp'],
                    y=alerts['service'],
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=alerts['severity'].map({'Low': 'green', 'Medium': 'orange', 'High': 'red'})
                    ),
                    text=alerts['message'],
                    hoverinfo='text',
                    name=f"Group {i+1}"
                ))
            fig.update_layout(
                title="Correlated Alerts Timeline",
                xaxis_title="Time",
                yaxis_title="Service",
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <div class="explanation">
            <strong>How to interpret:</strong> Each group of markers represents a set of correlated alerts. 
            Alerts in the same group occurred within the time window specified by the rule and met all other criteria. 
            This grouping can help you identify related issues or cascading failures across services.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No correlated alerts found for the selected rule.")
    else:
        st.info("No rules available. Please create rules in the 'Rule Creation' tab.")

with tab4:
    st.header("Rule-based Correlation Quiz")

    st.markdown("""
    <div class="explanation">
    Test your understanding of rule-based alert correlation with this quiz. 
    Each question is designed to reinforce key concepts and help you think about how to apply rule-based correlation in real-world scenarios.
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "question": "What is the main purpose of rule-based alert correlation?",
            "options": [
                "To generate more alerts",
                "To group related alerts based on predefined criteria",
                "To replace human operators",
                "To increase system downtime"
            ],
            "correct": 1,
            "explanation": "Rule-based correlation aims to group related alerts based on predefined criteria, helping to reduce alert noise and identify patterns or issues more easily."
        },
        {
            "question": "Which of the following is NOT typically a parameter in a rule-based correlation system?",
            "options": [
                "Service name",
                "Alert type",
                "Time window",
                "Network topology"
            ],
            "correct": 3,
            "explanation": "While service name, alert type, and time window are common parameters in rule-based correlation, network topology is more relevant to topology-based correlation approaches."
        },
        {
            "question": "What is the purpose of a 'time window' in rule-based correlation?",
            "options": [
                "To schedule alert generation",
                "To group alerts that occur close together in time",
                "To set working hours for the IT team",
                "To determine how long an alert should be displayed"
            ],
            "correct": 1,
            "explanation": "The time window in rule-based correlation is used to group alerts that occur within a specified time frame, helping to identify related issues that happen close together."
        },
        {
            "question": "Why might you set a threshold value in a correlation rule?",
            "options": [
                "To determine the color of the alert",
                "To filter out low-severity or low-impact alerts",
                "To set the maximum number of correlated alerts",
                "To define the number of services monitored"
            ],
            "correct": 1,
            "explanation": "Threshold values in correlation rules are often used to filter out low-severity or low-impact alerts, focusing on more significant issues that meet or exceed the specified threshold."
        },
        {
            "question": "What is a potential drawback of rule-based correlation?",
            "options": [
                "It's too simple to implement",
                "It can't handle any type of alert",
                "It may miss complex patterns not explicitly defined in rules",
                "It always produces too many correlated alert groups"
            ],
            "correct": 2,
            "explanation": "A potential drawback of rule-based correlation is that it may miss complex patterns or relationships between alerts that are not explicitly defined in the rules, potentially overlooking some important correlations."
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
                st.markdown(f"""
                <div class="explanation">
                <strong>Explanation:</strong> {q['explanation']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"You've already answered this question.")
            st.markdown(f"""
            <div class="explanation">
            <strong>Explanation:</strong> {q['explanation']}
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.questions_answered == len(questions):
        st.subheader("Quiz Complete!")
        st.write(f"Your score: {st.session_state.quiz_score}/{len(questions)}")
        if st.button("Retake Quiz"):
            for i in range(len(questions)):
                st.session_state[f'q{i}_answered'] = False
            st.session_state.quiz_score = 0
            st.session_state.questions_answered = 0
            st.experimental_rerun()
        
        st.markdown("""
        <div class="explanation">
        <strong>Why this quiz matters:</strong> Understanding these concepts helps you create more effective correlation rules and interpret the results better. 
        This knowledge can lead to faster problem resolution and improved system reliability in real-world IT operations.
        </div>
        """, unsafe_allow_html=True)