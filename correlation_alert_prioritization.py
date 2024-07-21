import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime

# Set page config
st.set_page_config(page_title="AIOps Alert Prioritization Explorer", layout="wide")

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
st.title("AIOps Alert Prioritization Explorer")

# Sidebar
with st.sidebar:
    st.header("Simulation Settings")
    num_alerts = st.slider("Number of alerts", 100, 1000, 500)
    num_services = st.slider("Number of services", 3, 10, 5)
    time_range = st.slider("Time range (hours)", 1, 24, 6)

    if st.button("Run Simulation"):
        # Generate sample data
        def generate_alerts(n_alerts, n_services, time_range):
            now = datetime.datetime.now()
            services = [f"Service_{i}" for i in range(n_services)]
            alert_types = ["CPU", "Memory", "Disk", "Network", "Application"]
            severities = ["Low", "Medium", "High", "Critical"]
            
            data = []
            for i in range(n_alerts):
                service = np.random.choice(services)
                alert_type = np.random.choice(alert_types)
                severity = np.random.choice(severities, p=[0.4, 0.3, 0.2, 0.1])  # Adjust probabilities for realism
                timestamp = now - datetime.timedelta(hours=np.random.uniform(0, time_range))
                
                data.append({
                    'alert_id': i,
                    'service': service,
                    'alert_type': alert_type,
                    'severity': severity,
                    'timestamp': timestamp
                })
            
            return pd.DataFrame(data)

        # Generate alerts
        alerts_df = generate_alerts(num_alerts, num_services, time_range)
        st.session_state['alerts'] = alerts_df
        st.success("Simulation completed! View results in the 'Results' tab.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Results", "🔥 Prioritization Heatmap", "🧠 Quiz", "ℹ️ About"])

with tab1:
    st.header("Alert Overview")
    if 'alerts' in st.session_state:
        alerts = st.session_state['alerts']
        
        # Display alert information
        st.subheader("Alert Statistics")
        st.write(f"Total number of alerts: {len(alerts)}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("Alerts per service:")
            st.write(alerts['service'].value_counts())
        with col2:
            st.write("Alerts by severity:")
            st.write(alerts['severity'].value_counts())

        # Visualization of alerts over time
        def plot_alerts_over_time(df):
            df['hour'] = df['timestamp'].dt.floor('H')
            hourly_counts = df.groupby(['hour', 'severity']).size().unstack(fill_value=0)

            fig = go.Figure()
            for severity in hourly_counts.columns:
                fig.add_trace(go.Scatter(
                    x=hourly_counts.index,
                    y=hourly_counts[severity],
                    mode='lines',
                    name=severity,
                    stackgroup='one'
                ))

            fig.update_layout(
                title="Alerts Over Time",
                xaxis_title="Time",
                yaxis_title="Number of Alerts",
                height=400,
                legend_title="Severity"
            )

            return fig

        st.plotly_chart(plot_alerts_over_time(alerts), use_container_width=True)

    else:
        st.info("Run the simulation in the sidebar to see results here.")

with tab2:
    st.header("Alert Prioritization Heatmap")
    if 'alerts' in st.session_state:
        alerts = st.session_state['alerts']

        # Create heatmap data
        def create_heatmap_data(df):
            severity_order = ["Critical", "High", "Medium", "Low"]
            heatmap_data = df.groupby(['service', 'severity']).size().unstack(fill_value=0)
            heatmap_data = heatmap_data.reindex(columns=severity_order)
            return heatmap_data

        heatmap_data = create_heatmap_data(alerts)

        # Create heatmap
        def plot_heatmap(data):
            fig = go.Figure(data=go.Heatmap(
                z=data.values,
                x=data.columns,
                y=data.index,
                colorscale='YlOrRd',
                hoverongaps = False))

            fig.update_layout(
                title="Alert Prioritization Heatmap",
                xaxis_title="Severity",
                yaxis_title="Service",
                height=500
            )

            return fig

        st.plotly_chart(plot_heatmap(heatmap_data), use_container_width=True)

        # Prioritization explanation
        st.subheader("Prioritized Services")
        priority_score = (heatmap_data['Critical'] * 4 + 
                          heatmap_data['High'] * 3 + 
                          heatmap_data['Medium'] * 2 + 
                          heatmap_data['Low'] * 1)
        priority_services = priority_score.sort_values(ascending=False)

        for service, score in priority_services.items():
            st.write(f"{service}: Priority Score = {score}")

        st.markdown("""
        <div class="explanation">
            <h3>Understanding Alert Prioritization</h3>
            <p>Alert Prioritization in AIOps helps IT teams focus on the most critical issues first. The heatmap above visualizes alert frequency across services and severities:</p>
            <ul>
                <li>Each row represents a service</li>
                <li>Each column represents a severity level</li>
                <li>The color intensity indicates the number of alerts (darker = more alerts)</li>
            </ul>
            <p><strong>Real-world example:</strong> Imagine you're managing a large e-commerce platform. The heatmap might show:</p>
            <ul>
                <li>Database service with many critical alerts: This could indicate persistent performance issues affecting the entire platform.</li>
                <li>Payment service with a mix of high and medium alerts: This might suggest intermittent issues that need attention to ensure smooth transactions.</li>
                <li>Logging service with mostly low severity alerts: While important, these might be less urgent compared to the database and payment issues.</li>
            </ul>
            <p>The Priority Score helps quantify which services need immediate attention. It's calculated by weighting alerts based on their severity:</p>
            <ul>
                <li>Critical alerts are weighted 4x</li>
                <li>High alerts are weighted 3x</li>
                <li>Medium alerts are weighted 2x</li>
                <li>Low alerts are weighted 1x</li>
            </ul>
            <p>This approach ensures that services with more severe alerts are prioritized, helping teams tackle the most impactful issues first.</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("Run the simulation in the sidebar to see the prioritization heatmap here.")

with tab3:
    st.header("Test Your Knowledge")
    st.markdown("""
    <div class="quiz-container">
        <p>Take this quick quiz to test your understanding of Alert Prioritization in AIOps!</p>
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "question": "What is the main goal of Alert Prioritization in AIOps?",
            "options": [
                "To generate more alerts",
                "To help IT teams focus on the most critical issues first",
                "To make colorful heatmaps",
                "To reduce the number of services monitored"
            ],
            "correct": 1,
            "explanation": "Alert Prioritization aims to help IT teams focus on the most critical issues first. For example, in an e-commerce platform, a critical issue with the payment system would be prioritized over a minor issue with the product recommendation system, ensuring that core business functions are addressed promptly."
        },
        {
            "question": "In the context of this demo, what does a dark red square in the heatmap represent?",
            "options": [
                "A service with no alerts",
                "A low priority issue",
                "A high number of alerts for a particular service and severity",
                "A service that's functioning perfectly"
            ],
            "correct": 2,
            "explanation": "A dark red square in the heatmap indicates a high number of alerts for a particular combination of service and severity. For instance, if the 'Database' row has a dark red square in the 'Critical' column, it means there are many critical alerts related to the database service, suggesting this should be a top priority for investigation."
        },
        {
            "question": "How is the Priority Score calculated in this demo?",
            "options": [
                "By counting the total number of alerts for each service",
                "By only considering critical alerts",
                "By weighting alerts based on their severity (e.g., Critical=4, High=3, etc.)",
                "Randomly"
            ],
            "correct": 2,
            "explanation": "The Priority Score is calculated by weighting alerts based on their severity. Critical alerts are given the highest weight (4), followed by High (3), Medium (2), and Low (1). This ensures that services with more severe alerts are prioritized. For example, a service with 5 critical alerts (5 * 4 = 20) would have a higher priority than a service with 10 low alerts (10 * 1 = 10)."
        },
        {
            "question": "Why might a service with fewer total alerts sometimes have a higher priority than a service with more alerts?",
            "options": [
                "The alert system is malfunctioning",
                "The service with fewer alerts might have more high-severity alerts",
                "Alerts are prioritized randomly",
                "Services with fewer alerts are always more important"
            ],
            "correct": 1,
            "explanation": "A service with fewer total alerts might have a higher priority if it has more high-severity alerts. For example, a database service with 5 critical alerts would be prioritized over a logging service with 20 low-severity alerts. This is because the potential impact of the critical database issues likely outweighs the numerous but less severe logging issues."
        },
        {
            "question": "In a real-world AIOps scenario, what additional factors might be considered for alert prioritization that are not included in this demo?",
            "options": [
                "The color preferences of the IT staff",
                "The weather conditions around the data center",
                "Service dependencies, business impact, and historical patterns",
                "The age of the servers"
            ],
            "correct": 2,
            "explanation": "Real-world AIOps systems often consider more complex factors like service dependencies, business impact, and historical patterns. For example"
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
    This interactive demo was created to illustrate the concept of Alert Prioritization in AIOps (Artificial Intelligence for IT Operations).

    Key features:
    1. Simulates alert generation across multiple services with varying severities
    2. Visualizes alerts over time
    3. Implements a basic alert prioritization system using a heatmap and priority scores
    4. Provides an educational component with a quiz

    The demo is meant for educational purposes and simulates a simplified version of alert prioritization. In real-world scenarios, more complex algorithms, additional factors, and domain-specific knowledge would be considered.

    For more information on AIOps and alert prioritization, please refer to academic papers and industry resources on these topics.
    """)

    st.subheader("Technologies Used")
    st.write("""
    - Streamlit: For the web application framework
    - Plotly: For interactive data visualization
    - Pandas & NumPy: For data manipulation and analysis
    """)

    st.subheader("Limitations and Future Improvements")
    st.write("""
    This demo has several limitations and could be improved in various ways:
    1. Implement machine learning models to predict alert severity and prioritize based on likely impact
    2. Include service dependency mapping to better understand the broader impact of alerts
    3. Incorporate historical data to identify patterns and recurring issues
    4. Add user feedback mechanisms to improve prioritization over time
    5. Integrate with real-time data sources for live alert prioritization

    These improvements would make the demo more closely resemble real-world AIOps systems.
    """)

    st.subheader("Feedback")
    st.write("We hope you found this demo informative and engaging! If you have any feedback, suggestions, or questions, please feel free to reach out.")

# Run the Streamlit app
if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.write("Adjust the settings above and click 'Run Simulation' to start.")