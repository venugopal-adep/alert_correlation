import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import datetime

# Set page config
st.set_page_config(page_title="AIOps Alert Correlation Explorer", layout="wide")

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
st.title("AIOps ML-based Alert Correlation Explorer")

# Sidebar
with st.sidebar:
    st.header("Simulation Settings")
    num_alerts = st.slider("Number of alerts", 50, 500, 200)
    num_services = st.slider("Number of services", 3, 10, 5)
    time_range = st.slider("Time range (hours)", 1, 24, 6)
    correlation_strength = st.slider("Correlation strength", 0.1, 1.0, 0.7)

    if st.button("Run Simulation"):
        # Generate sample data
        def generate_alerts(n_alerts, n_services, time_range, correlation_strength):
            now = datetime.datetime.now()
            services = [f"Service_{i}" for i in range(n_services)]
            alert_types = ["CPU", "Memory", "Disk", "Network", "Application"]
            
            data = []
            for i in range(n_alerts):
                service = np.random.choice(services)
                alert_type = np.random.choice(alert_types)
                severity = np.random.choice(["Low", "Medium", "High", "Critical"])
                timestamp = now - datetime.timedelta(hours=np.random.uniform(0, time_range))
                
                # Introduce correlation
                if np.random.random() < correlation_strength and i > 0:
                    service = data[-1]['service']
                    alert_type = data[-1]['alert_type']
                    timestamp = data[-1]['timestamp'] + datetime.timedelta(minutes=np.random.randint(1, 10))
                
                data.append({
                    'alert_id': i,
                    'service': service,
                    'alert_type': alert_type,
                    'severity': severity,
                    'timestamp': timestamp
                })
            
            return pd.DataFrame(data)

        # Generate alerts
        alerts_df = generate_alerts(num_alerts, num_services, time_range, correlation_strength)

        # ML-based correlation (using DBSCAN clustering)
        def correlate_alerts(df):
            # Feature engineering
            df['time_value'] = df['timestamp'].astype('int64') // 10**9  # Convert to Unix timestamp
            
            # Encode categorical variables
            df_encoded = pd.get_dummies(df, columns=['service', 'alert_type', 'severity'])
            
            # Scale features
            scaler = StandardScaler()
            df_scaled = scaler.fit_transform(df_encoded.drop(['alert_id', 'timestamp'], axis=1))
            
            # Apply DBSCAN clustering
            dbscan = DBSCAN(eps=0.5, min_samples=3)
            df['cluster'] = dbscan.fit_predict(df_scaled)
            
            return df

        # Correlate alerts
        correlated_alerts = correlate_alerts(alerts_df)
        st.session_state['correlated_alerts'] = correlated_alerts
        st.success("Simulation completed! View results in the 'Results' tab.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Results", "📚 Learn", "🧠 Quiz", "ℹ️ About"])

with tab1:
    st.header("Correlation Results")
    if 'correlated_alerts' in st.session_state:
        correlated_alerts = st.session_state['correlated_alerts']
        
        # Visualization
        def plot_alert_correlation(df):
            fig = go.Figure()

            clusters = df['cluster'].unique()
            for cluster in clusters:
                cluster_data = df[df['cluster'] == cluster]
                fig.add_trace(go.Scatter(
                    x=cluster_data['timestamp'],
                    y=cluster_data['service'],
                    mode='markers',
                    marker=dict(size=10, symbol='circle'),
                    name=f'Cluster {cluster}' if cluster != -1 else 'Noise',
                    text=[f"Alert ID: {i}<br>Type: {t}<br>Severity: {s}" for i, t, s in zip(cluster_data['alert_id'], cluster_data['alert_type'], cluster_data['severity'])],
                    hoverinfo='text'
                ))

            fig.update_layout(
                title="Alert Correlation Visualization",
                xaxis_title="Timestamp",
                yaxis_title="Service",
                height=600,
                showlegend=True
            )

            return fig

        # Display plot
        st.plotly_chart(plot_alert_correlation(correlated_alerts), use_container_width=True)

        # Display correlation information
        st.subheader("Correlation Analysis")
        cluster_counts = correlated_alerts['cluster'].value_counts()
        st.write(f"Number of correlated alert groups: {len(cluster_counts[cluster_counts.index != -1])}")
        st.write(f"Number of uncorrelated alerts: {cluster_counts.get(-1, 0)}")

        # Interactive alert inspection
        st.subheader("Inspect Correlated Alerts")
        selected_cluster = st.selectbox("Select a cluster to inspect:", options=sorted(correlated_alerts['cluster'].unique()))
        cluster_alerts = correlated_alerts[correlated_alerts['cluster'] == selected_cluster].sort_values('timestamp')
        st.write(cluster_alerts[['alert_id', 'service', 'alert_type', 'severity', 'timestamp']])
    else:
        st.info("Run the simulation in the sidebar to see results here.")

with tab2:
    st.header("Learn About AIOps Alert Correlation")
    st.markdown("""
    <div class="explanation">
        <h3>What's happening here?</h3>
        <p>This demo simulates ML-based Alert Correlation in AIOps:</p>
        <ol>
            <li>We generate sample alerts across different services and time ranges.</li>
            <li>The ML model (DBSCAN clustering) identifies correlations between alerts.</li>
            <li>Correlated alerts are grouped by color in the visualization.</li>
        </ol>
        <p><strong>Real-world application:</strong> In a large IT infrastructure, hundreds of alerts can be generated in a short time. 
        ML-based correlation helps identify related alerts that might stem from the same root cause, reducing alert fatigue and speeding up troubleshooting.</p>
        <p><strong>Understanding the results:</strong></p>
        <ul>
            <li>Each point represents an alert. Hover over points to see details.</li>
            <li>Alerts of the same color are considered correlated by the ML model.</li>
            <li>Grey points (if any) are considered "noise" or uncorrelated alerts.</li>
            <li>Closely grouped alerts of the same color likely indicate a common issue affecting multiple services or generating multiple alert types.</li>
        </ul>
        <p>Try adjusting the settings in the sidebar to see how they affect the alert patterns and correlations!</p>
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.header("Test Your Knowledge")
    st.markdown("""
    <div class="quiz-container">
        <p>Take this quick quiz to test your understanding of AIOps and Alert Correlation!</p>
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "question": "What is the main benefit of ML-based alert correlation in AIOps?",
            "options": [
                "It generates more alerts",
                "It reduces alert fatigue and helps identify root causes",
                "It makes the alerts more colorful",
                "It slows down the alert processing"
            ],
            "correct": 1
        },
        {
            "question": "In the context of this demo, what does a 'cluster' represent?",
            "options": [
                "A group of servers",
                "A type of alert",
                "A group of correlated alerts",
                "A time period"
            ],
            "correct": 2
        },
        {
            "question": "What might closely grouped alerts of the same color indicate in the visualization?",
            "options": [
                "A software bug in the visualization",
                "Unrelated alerts that happened by chance",
                "A common issue affecting multiple services",
                "The system is working perfectly"
            ],
            "correct": 2
        },
        {
            "question": "What does 'correlation strength' in the simulation settings control?",
            "options": [
                "The color intensity of the alerts",
                "The likelihood of alerts being related",
                "The number of services",
                "The time range of the simulation"
            ],
            "correct": 1
        },
        {
            "question": "Why is reducing alert fatigue important in IT operations?",
            "options": [
                "It saves electricity by generating fewer alerts",
                "It makes the dashboards look cleaner",
                "It helps IT staff focus on real issues more effectively",
                "It's not important, more alerts are always better"
            ],
            "correct": 2
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

with tab4:
    st.header("About This Demo")
    st.write("""
    This interactive demo was created to illustrate the concept of ML-based Alert Correlation in AIOps (Artificial Intelligence for IT Operations).

    Key features:
    1. Simulates alert generation across multiple services
    2. Uses DBSCAN clustering to correlate alerts
    3. Visualizes correlated alerts
    4. Provides an educational component with a quiz

    The demo is meant for educational purposes and simulates a simplified version of alert correlation. In real-world scenarios, more complex algorithms and additional factors would be considered.

    For more information on AIOps and alert correlation, please refer to academic papers and industry resources on the topic.
    """)

    st.subheader("Technologies Used")
    st.write("""
    - Streamlit: For the web application framework
    - Plotly: For interactive data visualization
    - Pandas & NumPy: For data manipulation
    - Scikit-learn: For the DBSCAN clustering algorithm
    """)

    st.subheader("Feedback")
    st.write("We hope you found this demo informative! If you have any feedback or suggestions, please feel free to reach out.")

# Run the Streamlit app
if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.write("Adjust the settings above and click 'Run Simulation' to start.")