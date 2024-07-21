import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import networkx as nx
import datetime

# Set page config
st.set_page_config(page_title="AIOps RCA Explorer", layout="wide")

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
st.title("AIOps Root Cause Analysis Explorer")

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
            root_cause = np.random.choice(services)
            for i in range(n_alerts):
                service = np.random.choice(services)
                alert_type = np.random.choice(alert_types)
                severity = np.random.choice(["Low", "Medium", "High", "Critical"])
                timestamp = now - datetime.timedelta(hours=np.random.uniform(0, time_range))
                
                # Introduce correlation and root cause
                if np.random.random() < correlation_strength:
                    service = root_cause
                    alert_type = "Application"
                    severity = "Critical"
                    timestamp = now - datetime.timedelta(minutes=np.random.randint(1, 30))
                
                data.append({
                    'alert_id': i,
                    'service': service,
                    'alert_type': alert_type,
                    'severity': severity,
                    'timestamp': timestamp
                })
            
            return pd.DataFrame(data), root_cause

        # Generate alerts
        alerts_df, root_cause = generate_alerts(num_alerts, num_services, time_range, correlation_strength)

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
        st.session_state['root_cause'] = root_cause
        st.success("Simulation completed! View results in the 'Results' tab.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Results", "🕵️ Root Cause Analysis", "🧠 Quiz", "ℹ️ About"])

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
    st.header("Root Cause Analysis")
    if 'correlated_alerts' in st.session_state:
        correlated_alerts = st.session_state['correlated_alerts']
        root_cause = st.session_state['root_cause']

        # Perform RCA
        def perform_rca(df, root_cause):
            # Create a graph of alert relationships
            G = nx.Graph()
            for _, row in df.iterrows():
                G.add_node(row['alert_id'], service=row['service'], alert_type=row['alert_type'], severity=row['severity'])
            
            # Connect alerts in the same cluster
            clusters = df['cluster'].unique()
            for cluster in clusters:
                if cluster != -1:
                    cluster_alerts = df[df['cluster'] == cluster]['alert_id'].tolist()
                    for i in range(len(cluster_alerts)):
                        for j in range(i+1, len(cluster_alerts)):
                            G.add_edge(cluster_alerts[i], cluster_alerts[j])
            
            # Find the most central node (potential root cause)
            centrality = nx.degree_centrality(G)
            most_central_alert = max(centrality, key=centrality.get)
            predicted_root_cause = G.nodes[most_central_alert]['service']
            
            return predicted_root_cause, G

        predicted_root_cause, alert_graph = perform_rca(correlated_alerts, root_cause)

        st.subheader("RCA Results")
        st.write(f"Predicted Root Cause: {predicted_root_cause}")
        st.write(f"Actual Root Cause: {root_cause}")

        if predicted_root_cause == root_cause:
            st.success("The RCA algorithm correctly identified the root cause!")
        else:
            st.warning("The RCA algorithm did not correctly identify the root cause. This can happen due to the complexity of alert patterns or limitations in the simulated data.")

        # Visualize alert relationships
        def plot_alert_relationships(G):
            pos = nx.spring_layout(G)
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')

            node_x = []
            node_y = []
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers',
                hoverinfo='text',
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    reversescale=True,
                    color=[],
                    size=10,
                    colorbar=dict(
                        thickness=15,
                        title='Node Connections',
                        xanchor='left',
                        titleside='right'
                    ),
                    line_width=2))

            node_adjacencies = []
            node_text = []
            for node, adjacencies in enumerate(G.adjacency()):
                node_adjacencies.append(len(adjacencies[1]))
                node_text.append(f"Alert ID: {adjacencies[0]}<br>Service: {G.nodes[adjacencies[0]]['service']}<br>Type: {G.nodes[adjacencies[0]]['alert_type']}<br>Severity: {G.nodes[adjacencies[0]]['severity']}")

            node_trace.marker.color = node_adjacencies
            node_trace.text = node_text

            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title='Alert Relationship Graph',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                annotations=[ dict(
                                    text="",
                                    showarrow=False,
                                    xref="paper", yref="paper",
                                    x=0.005, y=-0.002 ) ],
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            return fig

        st.plotly_chart(plot_alert_relationships(alert_graph), use_container_width=True)

        st.markdown("""
        <div class="explanation">
            <h3>Understanding Root Cause Analysis (RCA)</h3>
            <p>Root Cause Analysis in AIOps aims to identify the primary source of a problem that triggers multiple alerts across various services. Here's how it works in this demo:</p>
            <ol>
                <li>We create a graph where each node represents an alert, and edges connect related alerts (from the same cluster).</li>
                <li>We calculate the "centrality" of each node, which measures how connected it is to other nodes.</li>
                <li>The node with the highest centrality is considered the potential root cause.</li>
            </ol>
            <p><strong>Real-world example:</strong> Imagine a data center where a network switch fails. This could cause alerts from various services that depend on that switch, such as:
            <ul>
                <li>Database connection errors</li>
                <li>Web server timeouts</li>
                <li>Application performance degradation</li>
            </ul>
            RCA would help identify that the network switch failure is the root cause, rather than individual issues with the database, web server, or application.</p>
            <p><strong>Interpreting the graph:</strong></p>
            <ul>
                <li>Each node represents an alert. Larger, darker nodes have more connections and are more likely to be the root cause.</li>
                <li>Edges between nodes show relationships between alerts.</li>
                <li>Hover over nodes to see details about each alert.</li>
            </ul>
            <p>Remember, in real-world scenarios, RCA is much more complex and considers many more factors, including service dependencies, historical data, and expert knowledge.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Run the simulation in the sidebar to see RCA results here.")

with tab3:
    st.header("Test Your Knowledge")
    st.markdown("""
    <div class="quiz-container">
        <p>Take this quick quiz to test your understanding of Root Cause Analysis in AIOps!</p>
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "question": "What is the main goal of Root Cause Analysis in AIOps?",
            "options": [
                "To generate more alerts",
                "To identify the primary source of a problem causing multiple alerts",
                "To make pretty graphs",
                "To reduce the number of IT staff needed"
            ],
            "correct": 1,
            "explanation": "Root Cause Analysis aims to find the underlying cause of multiple related alerts. For example, a database server crash might cause alerts from web servers, application servers, and monitoring tools. RCA helps identify the database crash as the root cause, rather than treating each alert as a separate issue."
        },
        {
            "question": "In the context of this demo, what does a highly connected node in the alert relationship graph likely represent?",
            "options": [
                "An unimportant alert that can be ignored",
                "A potential root cause of the problem",
                "A bug in the alerting system",
                "A high-performing service"
            ],
            "correct": 1,
            "explanation": "A highly connected node often represents a potential root cause because it's related to many other alerts. For instance, if a core network switch fails, it might cause connection issues for multiple services, resulting in many related alerts. The alert for the switch failure would be highly connected in the graph."
        },
        {
                    "question": "Why is reducing alert fatigue important in IT operations?",
                    "options": [
                        "It saves electricity by generating fewer alerts",
                        "It makes the dashboards look cleaner",
                        "It helps IT staff focus on real issues more effectively",
                        "It's not important, more alerts are always better"
                    ],
                    "correct": 2,
                    "explanation": "Reducing alert fatigue is crucial because it allows IT staff to focus on significant issues. For example, if a single network switch failure generates 50 related alerts, it's more efficient for staff to address the root cause (the switch) rather than investigating each alert individually. This leads to faster problem resolution and more effective IT operations."
        },
        {
                    "question": "How does correlation strength affect Root Cause Analysis in this simulation?",
                    "options": [
                        "It doesn't affect RCA at all",
                        "Higher correlation strength makes RCA more accurate",
                        "Lower correlation strength makes RCA more accurate",
                        "Correlation strength only affects the color of alerts"
                    ],
                    "correct": 1,
                    "explanation": "Higher correlation strength typically makes RCA more accurate because it creates clearer patterns of related alerts. For instance, if a database failure has a high correlation strength, it might consistently cause alerts in the web server, application server, and monitoring system. This clear pattern makes it easier for the RCA algorithm to identify the database as the root cause."
        },
        {
                    "question": "In a real-world scenario, what additional factors might be considered in Root Cause Analysis that are not included in this demo?",
                    "options": [
                        "The color of the alerts",
                        "The mood of the IT staff",
                        "Historical data and known service dependencies",
                        "The brand of computers used in the data center"
                    ],
                    "correct": 2,
                    "explanation": "Real-world RCA often considers historical data and known service dependencies. For example, if there's a history of the authentication service failing during peak hours, and current alerts show similar patterns, the RCA might prioritize the authentication service as a potential root cause. Similarly, if we know that Service A depends on Service B, and both are showing alerts, the RCA might focus on Service B as the likely root cause."
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
    This interactive demo was created to illustrate the concepts of Alert Correlation and Root Cause Analysis (RCA) in AIOps (Artificial Intelligence for IT Operations).

    Key features:
    1. Simulates alert generation across multiple services
    2. Uses DBSCAN clustering for alert correlation
    3. Implements a simple graph-based approach for Root Cause Analysis
    4. Visualizes correlated alerts and alert relationships
    5. Provides an educational component with a quiz

    The demo is meant for educational purposes and simulates a simplified version of alert correlation and RCA. In real-world scenarios, more complex algorithms, additional factors, and domain-specific knowledge would be considered.

    For more information on AIOps, alert correlation, and root cause analysis, please refer to academic papers and industry resources on these topics.
    """)

    st.subheader("Technologies Used")
    st.write("""
    - Streamlit: For the web application framework
    - Plotly: For interactive data visualization
    - Pandas & NumPy: For data manipulation
    - Scikit-learn: For the DBSCAN clustering algorithm
    - NetworkX: For graph-based analysis in RCA
    """)

    st.subheader("Limitations and Future Improvements")
    st.write("""
    This demo has several limitations and could be improved in various ways:
    1. More sophisticated RCA algorithms could be implemented
    2. Additional factors like service dependencies could be incorporated
    3. The simulation could be made more realistic with more varied alert patterns
    4. Machine learning models could be used to predict future alerts or automate responses
    5. Integration with real-time data sources could make the demo more practical for actual use

    These improvements would make the demo more closely resemble real-world AIOps systems.
    """)

    st.subheader("Feedback")
    st.write("We hope you found this demo informative and engaging! If you have any feedback, suggestions, or questions, please feel free to reach out.")

# Run the Streamlit app
if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.write("Adjust the settings above and click 'Run Simulation' to start.")