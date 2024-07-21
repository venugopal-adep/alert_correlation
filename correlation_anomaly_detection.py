import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats
import datetime
from sklearn.ensemble import IsolationForest

# Set page config
st.set_page_config(page_title="AIOps Anomaly Detection Explorer", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .explanation, .quiz-container {
        background-color: #e7f3fe;
        border-left: 6px solid #2196F3;
        padding: 10px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e7f3fe;
    }
    .quiz-feedback {
        margin-top: 10px;
        padding: 10px;
        border-radius: 5px;
    }
    .correct {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .incorrect {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("AIOps Anomaly Detection in Alert Patterns Explorer")

# Sidebar
with st.sidebar:
    st.header("Simulation Settings")
    num_days = st.slider("Number of days", 30, 90, 60)
    num_services = st.slider("Number of services", 3, 10, 5)
    anomaly_frequency = st.slider("Anomaly frequency (days)", 1, 30, 7)
    anomaly_magnitude = st.slider("Anomaly magnitude", 1.5, 5.0, 3.0)

    if st.button("Run Simulation"):
        # Generate synthetic alert data
        def generate_alert_data(n_days, n_services, anomaly_freq, anomaly_mag):
            date_range = pd.date_range(end=pd.Timestamp.now(), periods=n_days)
            services = [f"Service_{i}" for i in range(n_services)]
            
            data = []
            for service in services:
                baseline = np.random.randint(10, 50)
                trend = np.random.uniform(-0.5, 0.5)
                seasonality = np.random.uniform(0, 10)
                
                for i, date in enumerate(date_range):
                    alerts = baseline + trend * i + seasonality * np.sin(2 * np.pi * i / 7)
                    
                    # Add noise (ensure positive scale)
                    noise_scale = max(0.1, alerts * 0.1)  # Ensure minimum positive scale
                    alerts += np.random.normal(0, noise_scale)
                    
                    # Inject anomalies
                    if i % anomaly_freq == 0:
                        alerts *= anomaly_mag
                    
                    data.append({
                        'date': date,
                        'service': service,
                        'alerts': max(0, int(alerts))  # Ensure non-negative integer
                    })
            
            return pd.DataFrame(data)

        # Generate alert data
        alert_data = generate_alert_data(num_days, num_services, anomaly_frequency, anomaly_magnitude)
        st.session_state['alert_data'] = alert_data
        st.success("Simulation completed! View results in the 'Results' tab.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Results", "🔍 Anomaly Detection", "🧠 Quiz", "ℹ️ About"])

with tab1:
    st.header("Alert Data Overview")
    if 'alert_data' in st.session_state:
        alert_data = st.session_state['alert_data']
        
        # Visualization of alerts over time
        def plot_alerts_over_time(df):
            fig = go.Figure()
            for service in df['service'].unique():
                service_data = df[df['service'] == service]
                fig.add_trace(go.Scatter(
                    x=service_data['date'],
                    y=service_data['alerts'],
                    mode='lines',
                    name=service
                ))

            fig.update_layout(
                title="Alerts Over Time",
                xaxis_title="Date",
                yaxis_title="Number of Alerts",
                height=500,
                legend_title="Service"
            )

            return fig

        st.plotly_chart(plot_alerts_over_time(alert_data), use_container_width=True)

        # Display alert statistics
        st.subheader("Alert Statistics")
        st.write(f"Total number of alerts: {alert_data['alerts'].sum()}")
        st.write("Alerts per service:")
        st.write(alert_data.groupby('service')['alerts'].sum().sort_values(ascending=False))

    else:
        st.info("Run the simulation in the sidebar to see results here.")

with tab2:
    st.header("Anomaly Detection")
    if 'alert_data' in st.session_state:
        alert_data = st.session_state['alert_data']

        # Perform anomaly detection
        def detect_anomalies(df):
            anomalies = {}
            for service in df['service'].unique():
                service_data = df[df['service'] == service]
                X = service_data[['alerts']].values
                
                # Use Isolation Forest for anomaly detection
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomaly_labels = iso_forest.fit_predict(X)
                
                anomalies[service] = service_data[anomaly_labels == -1]
            
            return anomalies

        anomalies = detect_anomalies(alert_data)

        # Visualization of alerts with anomalies
        def plot_alerts_with_anomalies(df, anomalies):
            fig = go.Figure()
            for service in df['service'].unique():
                service_data = df[df['service'] == service]
                fig.add_trace(go.Scatter(
                    x=service_data['date'],
                    y=service_data['alerts'],
                    mode='lines',
                    name=service
                ))
                
                # Add anomalies as scatter points
                service_anomalies = anomalies[service]
                fig.add_trace(go.Scatter(
                    x=service_anomalies['date'],
                    y=service_anomalies['alerts'],
                    mode='markers',
                    name=f'{service} Anomalies',
                    marker=dict(size=10, symbol='star', color='red')
                ))

            fig.update_layout(
                title="Alerts Over Time with Detected Anomalies",
                xaxis_title="Date",
                yaxis_title="Number of Alerts",
                height=500,
                legend_title="Service"
            )

            return fig

        st.plotly_chart(plot_alerts_with_anomalies(alert_data, anomalies), use_container_width=True)

        # Display anomaly statistics
        st.subheader("Anomaly Statistics")
        for service, anomaly_data in anomalies.items():
            st.write(f"{service}: {len(anomaly_data)} anomalies detected")

        st.markdown("""
        <div class="explanation">
            <h3>Understanding Anomaly Detection in Alert Patterns</h3>
            <p>Anomaly detection in AIOps helps identify unusual patterns in alert data that may indicate significant issues or changes in system behavior. Here's how it works in this demo:</p>
            <ol>
                <li>We generate synthetic alert data for multiple services over time, including normal variations and injected anomalies.</li>
                <li>We use the Isolation Forest algorithm to detect anomalies in the alert patterns for each service.</li>
                <li>Detected anomalies are highlighted as red stars on the graph.</li>
            </ol>
            <p><strong>Real-world example:</strong> Imagine you're monitoring a cloud-based e-commerce platform:</p>
            <ul>
                <li>Normal pattern: The number of alerts typically follows a weekly cycle, with more alerts during business hours and fewer on weekends.</li>
                <li>Anomaly: Suddenly, you see a spike in alerts for the database service on a Sunday night, much higher than usual. This could indicate an issue like:
                    <ul>
                        <li>An unexpected surge in user traffic, perhaps due to a viral social media post</li>
                        <li>A database performance problem or outage</li>
                        <li>A cyber attack attempt causing unusual database behavior</li>
                    </ul>
                </li>
            </ul>
            <p>Detecting these anomalies quickly can help IT teams respond proactively to potential issues before they escalate into major problems affecting user experience or business operations.</p>
            <p><strong>Interpreting the results:</strong></p>
            <ul>
                <li>Look for red stars on the graph, which indicate detected anomalies.</li>
                <li>Consider the context of each anomaly: Is it part of a pattern? Does it coincide with known events?</li>
                <li>Remember that not all anomalies are problematic - some may be due to positive events like a successful marketing campaign leading to increased traffic.</li>
            </ul>
            <p>In real-world AIOps, anomaly detection would be combined with other data sources and domain knowledge to provide more accurate and actionable insights.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("Run the simulation in the sidebar to see anomaly detection results here.")

with tab3:
    st.header("Test Your Knowledge")
    st.markdown("""
    <div class="quiz-container">
        <p>Take this quick quiz to test your understanding of Anomaly Detection in Alert Patterns for AIOps!</p>
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "question": "What is the main goal of Anomaly Detection in alert patterns for AIOps?",
            "options": [
                "To generate more alerts",
                "To identify unusual patterns that may indicate significant issues",
                "To reduce the number of alerts",
                "To make the alert graphs look more interesting"
            ],
            "correct": 1,
            "explanation": "Anomaly Detection in AIOps aims to identify unusual patterns in alert data that may indicate significant issues or changes in system behavior. For example, if a web service typically generates 50-100 alerts per day, a sudden spike to 1000 alerts could be flagged as an anomaly, prompting immediate investigation into potential problems like a DDoS attack or a major system failure."
        },
        {
            "question": "In the context of this demo, what do the red stars on the graph represent?",
            "options": [
                "Normal alert patterns",
                "Detected anomalies in the alert data",
                "Scheduled maintenance periods",
                "Holidays"
            ],
            "correct": 1,
            "explanation": "The red stars on the graph represent detected anomalies in the alert data. These are points where the alert pattern significantly deviates from the expected behavior. For instance, if an e-commerce platform's payment service usually has 10-20 alerts per hour, a red star might appear when there are suddenly 100 alerts in an hour, potentially indicating a problem with payment processing that requires immediate attention."
        },
        {
            "question": "Why is it important to consider context when interpreting anomalies in alert patterns?",
            "options": [
                "Context isn't important in anomaly detection",
                "To determine if the anomaly is due to a problem or a positive event",
                "To make the graphs look more colorful",
                "Anomalies are always bad and context doesn't matter"
            ],
            "correct": 1,
            "explanation": """Considering context is crucial when interpreting anomalies because not all anomalies indicate problems. For example:
            1. Problem scenario: A spike in database errors during normal operation hours could indicate a serious issue needing immediate attention.
            2. Positive scenario: A surge in alerts related to high traffic during a major sale event might be expected and even desirable.
            Understanding the context helps distinguish between anomalies that require urgent action and those that are part of normal business operations."""
        },
        {
            "question": "What is an advantage of using machine learning for anomaly detection in AIOps?",
            "options": [
                "It always provides perfect results",
                "It can identify complex patterns that might be missed by simple threshold-based systems",
                "It eliminates the need for human oversight",
                "It generates more alerts"
            ],
            "correct": 1,
            "explanation": """Machine learning for anomaly detection in AIOps can identify complex patterns that might be missed by simple threshold-based systems. For instance:
            1. Threshold system: Might only detect when the number of alerts exceeds a fixed number, like 100 per hour.
            2. ML system: Can learn normal patterns over time and detect subtle anomalies, like an unusual combination of alert types, even if the total number of alerts isn't extraordinarily high. This could catch issues early, before they escalate into major problems."""
        },
        {
            "question": "In a real-world AIOps scenario, what additional factors might be considered for anomaly detection that are not included in this demo?",
            "options": [
                "The color preferences of the IT staff",
                "The weather conditions around the data center",
                "Seasonality, trend, and correlation between different services",
                "The age of the servers"
            ],
            "correct": 2,
            "explanation": """Real-world AIOps anomaly detection often considers more complex factors like:
            1. Seasonality: E.g., recognizing that higher alert volumes during business hours are normal.
            2. Trend: Detecting long-term increases in alert frequency that might indicate gradually degrading performance.
            3. Correlation between services: Understanding that an anomaly in one service (e.g., database) might cause related anomalies in dependent services (e.g., web application).
            4. External factors: Correlating anomalies with known events like marketing campaigns, software releases, or global events affecting user behavior.
            These factors help create a more nuanced and accurate anomaly detection system, reducing false positives and providing more actionable insights."""
        }
    ]

    for i, q in enumerate(questions):
        st.subheader(f"Question {i+1}")
        user_answer = st.radio(q['question'], options=q['options'], key=f'q{i}')
        if st.button(f"Check Answer {i+1}"):
            if user_answer == q['options'][q['correct']]:
                st.markdown(f'<div class="quiz-feedback correct">Correct! Well done!</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="quiz-feedback incorrect">Incorrect. The correct answer is: {q["options"][q["correct"]]}</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='explanation'><strong>Explanation:</strong> {q['explanation']}</div>", unsafe_allow_html=True)

with tab4:
    st.header("About This Demo")
    st.write("""
    This interactive demo was created to illustrate the concept of Anomaly Detection in Alert Patterns for AIOps (Artificial Intelligence for IT Operations).

    Key features:
    1. Generates synthetic alert data for multiple services over time
    2. Simulates normal variations in alert patterns, including trends and seasonality
    3. Injects anomalies into the data""")