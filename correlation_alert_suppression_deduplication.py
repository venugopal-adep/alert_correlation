import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import datetime
import hashlib

# Set page config
st.set_page_config(page_title="AIOps Alert Suppression & Deduplication Explorer", layout="wide")

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
st.title("AIOps Alert Suppression & Deduplication Explorer")

# Sidebar
with st.sidebar:
    st.header("Simulation Settings")
    num_alerts = st.slider("Number of alerts", 50, 1000, 500)
    num_services = st.slider("Number of services", 3, 10, 5)
    time_range = st.slider("Time range (hours)", 1, 24, 6)
    duplication_rate = st.slider("Duplication rate", 0.1, 0.9, 0.5)
    suppression_window = st.slider("Suppression window (minutes)", 1, 60, 15)

    if st.button("Run Simulation"):
        # Generate sample data
        def generate_alerts(n_alerts, n_services, time_range, duplication_rate):
            now = datetime.datetime.now()
            services = [f"Service_{i}" for i in range(n_services)]
            alert_types = ["CPU", "Memory", "Disk", "Network", "Application"]
            
            data = []
            for i in range(n_alerts):
                service = np.random.choice(services)
                alert_type = np.random.choice(alert_types)
                severity = np.random.choice(["Low", "Medium", "High", "Critical"])
                timestamp = now - datetime.timedelta(hours=np.random.uniform(0, time_range))
                
                # Introduce duplication
                if np.random.random() < duplication_rate and i > 0:
                    duplicate_alert = data[np.random.randint(0, len(data))]
                    service = duplicate_alert['service']
                    alert_type = duplicate_alert['alert_type']
                    severity = duplicate_alert['severity']
                    timestamp = duplicate_alert['timestamp'] + datetime.timedelta(seconds=np.random.randint(1, 300))
                
                data.append({
                    'alert_id': i,
                    'service': service,
                    'alert_type': alert_type,
                    'severity': severity,
                    'timestamp': timestamp
                })
            
            return pd.DataFrame(data)

        # Generate alerts
        alerts_df = generate_alerts(num_alerts, num_services, time_range, duplication_rate)
        st.session_state['original_alerts'] = alerts_df
        st.success("Simulation completed! View results in the 'Results' tab.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Results", "🧹 Suppression & Deduplication", "🧠 Quiz", "ℹ️ About"])

with tab1:
    st.header("Original Alerts")
    if 'original_alerts' in st.session_state:
        original_alerts = st.session_state['original_alerts']
        
        # Visualization
        def plot_alerts(df, title):
            fig = go.Figure()

            for service in df['service'].unique():
                service_data = df[df['service'] == service]
                fig.add_trace(go.Scatter(
                    x=service_data['timestamp'],
                    y=[service] * len(service_data),
                    mode='markers',
                    name=service,
                    text=[f"Alert ID: {i}<br>Type: {t}<br>Severity: {s}" for i, t, s in zip(service_data['alert_id'], service_data['alert_type'], service_data['severity'])],
                    hoverinfo='text'
                ))

            fig.update_layout(
                title=title,
                xaxis_title="Timestamp",
                yaxis_title="Service",
                height=400,
                showlegend=True
            )

            return fig

        # Display plot
        st.plotly_chart(plot_alerts(original_alerts, "Original Alerts"), use_container_width=True)

        # Display alert information
        st.subheader("Alert Statistics")
        st.write(f"Total number of alerts: {len(original_alerts)}")
        st.write(f"Alerts per service:")
        st.write(original_alerts['service'].value_counts())

    else:
        st.info("Run the simulation in the sidebar to see results here.")

with tab2:
    st.header("Alert Suppression & Deduplication")
    if 'original_alerts' in st.session_state:
        original_alerts = st.session_state['original_alerts']

        # Perform suppression and deduplication
        def suppress_and_deduplicate(df, suppression_window):
            df = df.sort_values('timestamp')
            
            # Create a hash for each alert based on service, type, and severity
            df['alert_hash'] = df.apply(lambda row: hashlib.md5(f"{row['service']}_{row['alert_type']}_{row['severity']}".encode()).hexdigest(), axis=1)
            
            # Initialize suppression window
            suppression_end = {}
            
            processed_alerts = []
            for _, alert in df.iterrows():
                current_time = alert['timestamp']
                alert_hash = alert['alert_hash']
                
                # Check if the alert is within the suppression window
                if alert_hash in suppression_end and current_time <= suppression_end[alert_hash]:
                    continue
                
                # If not suppressed, add to processed alerts and update suppression window
                processed_alerts.append(alert)
                suppression_end[alert_hash] = current_time + datetime.timedelta(minutes=suppression_window)
            
            return pd.DataFrame(processed_alerts)

        processed_alerts = suppress_and_deduplicate(original_alerts, suppression_window)
        st.session_state['processed_alerts'] = processed_alerts

        # Display processed alerts plot
        st.plotly_chart(plot_alerts(processed_alerts, "Processed Alerts (After Suppression & Deduplication)"), use_container_width=True)

        # Display statistics
        st.subheader("Alert Reduction Statistics")
        original_count = len(original_alerts)
        processed_count = len(processed_alerts)
        reduction_percentage = ((original_count - processed_count) / original_count) * 100

        st.write(f"Original number of alerts: {original_count}")
        st.write(f"Alerts after suppression & deduplication: {processed_count}")
        st.write(f"Alert reduction: {reduction_percentage:.2f}%")

        st.markdown("""
        <div class="explanation">
            <h3>Understanding Alert Suppression & Deduplication</h3>
            <p>Alert Suppression and Deduplication are techniques used in AIOps to reduce alert fatigue and improve the efficiency of IT operations. Here's how they work:</p>
            <ol>
                <li><strong>Alert Deduplication:</strong> This process identifies and combines duplicate alerts. In this demo, we consider alerts as duplicates if they have the same service, alert type, and severity.</li>
                <li><strong>Alert Suppression:</strong> This technique prevents similar alerts from being raised within a specific time window after the initial alert. In this demo, the suppression window is adjustable in the sidebar.</li>
            </ol>
            <p><strong>Real-world example:</strong> Imagine a network switch that's flapping (rapidly going up and down). Without suppression and deduplication, this could generate hundreds of similar alerts in a short time. With these techniques:
            <ul>
                <li>The first alert about the switch going down would be raised.</li>
                <li>Subsequent alerts about the same switch within the suppression window would be suppressed.</li>
                <li>If the switch stabilizes and then fails again after the suppression window, a new alert would be raised.</li>
            </ul>
            This approach significantly reduces the number of alerts that operators need to handle, allowing them to focus on unique and critical issues.</p>
            <p><strong>Interpreting the results:</strong></p>
            <ul>
                <li>Compare the "Original Alerts" and "Processed Alerts" graphs to see the reduction in alert volume.</li>
                <li>The Alert Reduction Statistics show the effectiveness of suppression and deduplication.</li>
                <li>Adjust the "Duplication rate" and "Suppression window" in the sidebar to see how they affect the results.</li>
            </ul>
            <p>Remember, in real-world scenarios, more sophisticated algorithms might be used, considering factors like alert context, historical patterns, and service dependencies.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Run the simulation in the sidebar to see suppression and deduplication results here.")

with tab3:
    st.header("Test Your Knowledge")
    st.markdown("""
    <div class="quiz-container">
        <p>Take this quick quiz to test your understanding of Alert Suppression and Deduplication in AIOps!</p>
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "question": "What is the main goal of Alert Suppression and Deduplication in AIOps?",
            "options": [
                "To generate more alerts",
                "To reduce alert fatigue and improve operational efficiency",
                "To make alert graphs look prettier",
                "To increase the workload of IT staff"
            ],
            "correct": 1,
            "explanation": "Alert Suppression and Deduplication aim to reduce the number of redundant or repetitive alerts, thereby decreasing alert fatigue and allowing IT staff to focus on unique and critical issues. For example, if a server experiences rapid CPU spikes, instead of sending hundreds of similar alerts, these techniques would ensure only a few key alerts are sent, making it easier for staff to manage and respond effectively."
        },
        {
            "question": "In the context of this demo, what does the 'Suppression window' control?",
            "options": [
                "The time range for generating alerts",
                "The number of services monitored",
                "The time period during which similar alerts are suppressed after an initial alert",
                "The color of the alert markers on the graph"
            ],
            "correct": 2,
            "explanation": "The Suppression window determines how long similar alerts are suppressed after an initial alert is raised. For instance, if set to 15 minutes, after an alert about high CPU usage on a server, any similar alerts for that server would be suppressed for the next 15 minutes. This prevents a flood of repetitive alerts during ongoing issues, giving operators time to investigate and respond."
        },
        {
            "question": "How does Alert Deduplication differ from Alert Suppression?",
            "options": [
                "Deduplication removes alerts, while suppression doesn't",
                "Suppression is time-based, while deduplication is content-based",
                "Deduplication only works on critical alerts, while suppression works on all alerts",
                "There is no difference; they are the same thing"
            ],
            "correct": 1,
            "explanation": "While both techniques reduce alert volume, they work differently. Deduplication identifies and combines alerts with identical content (e.g., same service, type, and severity) regardless of time. Suppression, on the other hand, prevents similar alerts within a specific time window. For example, deduplication might combine multiple 'disk full' alerts for the same server into one, while suppression would prevent new 'disk full' alerts for that server for a set time after the first alert."
        },
        {
            "question": "What potential risk should be considered when implementing aggressive alert suppression?",
            "options": [
                "It might make the alerts more colorful",
                "It could potentially hide important follow-up alerts",
                "It will increase the number of alerts",
                "It will slow down the alerting system"
            ],
            "correct": 1,
            "explanation": "While suppression is beneficial, overly aggressive suppression could potentially hide important follow-up alerts. For instance, if a 1-hour suppression window is set for network alerts, and a switch goes down, comes back up, and goes down again within that hour, the second failure might be missed. It's crucial to balance reducing alert noise with ensuring critical information isn't lost."
        },
        {
            "question": "In a real-world AIOps scenario, what additional factors might be considered for alert suppression and deduplication that are not included in this demo?",
            "options": [
                "The color preferences of the IT staff",
                "The weather conditions around the data center",
                "Historical alert patterns and service dependencies",
                "The brand of the alerting software"
            ],
            "correct": 2,
            "explanation": "Real-world AIOps systems often consider more complex factors like historical alert patterns and service dependencies. For example, if a database server often experiences brief CPU spikes without real issues, the system might learn to suppress these alerts. Or, if a web server alert always follows a database alert, the system might combine these into a single, more informative alert about the overall system state."
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
    st.write("""
    This interactive demo was created to illustrate the concepts of Alert Suppression and Deduplication in AIOps (Artificial Intelligence for IT Operations).

    Key features:
    1. Simulates alert generation across multiple services with controllable duplication rate
    2. Implements basic alert suppression and deduplication techniques
    3. Visualizes the impact of these techniques on alert volume
    4. Provides an educational component with a quiz

    The demo is meant for educational purposes and simulates a simplified version of alert suppression and deduplication. In real-world scenarios, more complex algorithms, additional factors, and domain-specific knowledge would be considered.

    For more information on AIOps, alert suppression, and deduplication, please refer to academic papers and industry resources on these topics.
    """)

    st.subheader("Technologies Used")
    st.write("""
    - Streamlit: For the web application framework
    - Plotly: For interactive data visualization
    - Pandas & NumPy: For data manipulation and analysis
    - Scikit-learn: For potential future machine learning implementations
    - Hashlib: For creating unique hashes for alert deduplication
    """)

    st.subheader("Limitations and Future Improvements")
    st.write("""
    This demo has several limitations and could be improved in various ways:
    1. More sophisticated suppression and deduplication algorithms could be implemented
    2. Machine learning models could be used to predict which alerts are likely to be duplicates or need suppression
    3. The simulation could be made more realistic with more varied alert patterns and inter-service dependencies
    4. Time-based analysis could be added to show how alert patterns change over time
    5. Integration with real-time data sources could make the demo more practical for actual use

    These improvements would make the demo more closely resemble real-world AIOps systems.
    """)

    st.subheader("Feedback")
    st.write("We hope you found this demo informative and engaging! If you have any feedback, suggestions, or questions, please feel free to reach out.")

# Run the Streamlit app
if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.write("Adjust the settings above and click 'Run Simulation' to start.")