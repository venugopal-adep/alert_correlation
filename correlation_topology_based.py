import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="AIOps Topology-based Correlation Demo", layout="wide")

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

# Generate synthetic topology
def generate_topology(num_nodes):
    G = nx.random_tree(n=num_nodes)
    nodes = list(G.nodes())
    node_types = np.random.choice(['Server', 'Router', 'Switch', 'Database'], size=num_nodes)
    nx.set_node_attributes(G, dict(zip(nodes, node_types)), 'type')
    return G

# Generate synthetic alert data
def generate_alert_data(G, num_hours):
    alerts = []
    start_time = datetime.now() - timedelta(hours=num_hours)
    for hour in range(num_hours):
        current_time = start_time + timedelta(hours=hour)
        for node in G.nodes():
            if np.random.random() < 0.1:  # 10% chance of an alert
                severity = np.random.choice(['Low', 'Medium', 'High'], p=[0.6, 0.3, 0.1])
                alerts.append({
                    'timestamp': current_time,
                    'node': node,
                    'severity': severity,
                    'message': f"Alert on {G.nodes[node]['type']} {node}"
                })
    return pd.DataFrame(alerts)

# Sidebar controls
st.sidebar.header("Simulation Controls")
num_nodes = st.sidebar.slider("Number of nodes", 10, 50, 20)
num_hours = st.sidebar.slider("Number of hours to simulate", 1, 48, 24)

# Generate data
G = generate_topology(num_nodes)
df = generate_alert_data(G, num_hours)

# Main content
st.title("Interactive Topology-based Alert Correlation Demo")
st.write("""
This demo simulates a network topology and alert system to show how alerts can be correlated based on network structure.
It helps IT teams quickly identify related issues and potential root causes of problems in complex systems.
""")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Network Topology", "Alert Timeline", "Path Analysis", "Quiz"])

with tab1:
    st.header("Network Topology")
    st.write("""
    This graph shows the simulated network structure. Each node represents a device (like a server or router), 
    and the lines show connections between devices. 
    
    The color of each node indicates how many connections it has:
    - Darker red: More connections (potentially more critical)
    - Lighter yellow: Fewer connections
    
    Hover over a node to see more details about it.
    """)

    # Create network graph
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

    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
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

    # Color nodes by number of connections
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(f"Node: {node}<br>Type: {G.nodes[node]['type']}<br># of connections: {len(adjacencies[1])}")

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='Network Topology',
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
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Alert Timeline")
    st.write("""
    This chart shows when alerts occurred on different devices over time.
    
    Each dot represents an alert:
    - Green circles: Low severity
    - Orange squares: Medium severity
    - Red diamonds: High severity
    
    Hover over a dot to see more details about the alert.
    
    Example: If you see several red diamonds close together on different nodes, 
    it might indicate a serious issue affecting multiple devices.
    """)

    # Create alert timeline
    fig = go.Figure()

    for node in G.nodes():
        node_data = df[df['node'] == node]
        fig.add_trace(go.Scatter(
            x=node_data['timestamp'],
            y=[node] * len(node_data),
            mode='markers',
            name=f"Node {node}",
            marker=dict(
                size=10,
                color=node_data['severity'].map({'Low': 'green', 'Medium': 'orange', 'High': 'red'}),
                symbol=node_data['severity'].map({'Low': 'circle', 'Medium': 'square', 'High': 'diamond'})
            ),
            text=node_data['message'],
            hoverinfo='text'
        ))

    fig.update_layout(
        title="Alert Timeline",
        xaxis_title="Time",
        yaxis_title="Node",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Path Analysis")
    st.write("""
    This tool helps you understand how issues might spread between two devices in the network.
    
    1. Select a source and target device from the dropdowns.
    2. Click 'Analyze Path' to see the shortest connection path between them.
    3. The path will be highlighted in red on the network graph.
    4. Check the 'Alerts on Path' table to see if any alerts occurred along this path.
    
    Example: If you see alerts on multiple devices along the path, especially close in time,
    it might indicate a problem spreading through the network.
    """)

    col1, col2 = st.columns(2)

    with col1:
        source_node = st.selectbox("Select source node", list(G.nodes()))
        target_node = st.selectbox("Select target node", [n for n in G.nodes() if n != source_node])

        if st.button("Analyze Path"):
            path = nx.shortest_path(G, source=source_node, target=target_node)
            st.write(f"Shortest path: {' -> '.join(map(str, path))}")

            # Highlight path in network graph
            edge_x = []
            edge_y = []
            for i in range(len(path) - 1):
                x0, y0 = pos[path[i]]
                x1, y1 = pos[path[i + 1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            path_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color='red'),
                hoverinfo='none',
                mode='lines')

            fig = go.Figure(data=[edge_trace, node_trace, path_trace],
                            layout=go.Layout(
                                title='Path in Network Topology',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20,l=5,r=5,t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Alerts on Path")
        if 'path' in locals():
            path_alerts = df[df['node'].isin(path)].sort_values('timestamp')
            st.dataframe(path_alerts)

            st.subheader("Correlation Analysis")
            if len(path_alerts) > 1:
                time_diffs = path_alerts['timestamp'].diff().dropna()
                avg_time_diff = time_diffs.mean().total_seconds() / 60
                st.write(f"Average time between alerts on path: {avg_time_diff:.2f} minutes")

                if avg_time_diff <= 5:
                    st.warning("Potential cascading failure detected!")
                elif avg_time_diff <= 15:
                    st.info("Moderate correlation between alerts on path.")
                else:
                    st.success("Low correlation between alerts on path.")
            else:
                st.write("Not enough alerts on path for correlation analysis.")

    st.write("""
    The correlation analysis looks at how close together in time the alerts on the path occurred:
    - Less than 5 minutes apart on average: Likely a cascading failure
    - 5-15 minutes apart: Moderate correlation, possibly related issues
    - More than 15 minutes apart: Low correlation, probably unrelated issues
    """)

with tab4:
    st.header("Topology-based Correlation Quiz")
    st.write("""
    Test your understanding of topology-based alert correlation with this quiz!
    
    Each question has one correct answer. After submitting your answer, you'll see an explanation
    to help you understand the concept better.
    """)

    questions = [
        {
            "question": "What is the main advantage of topology-based alert correlation?",
            "options": [
                "It's faster than time-based correlation",
                "It considers the relationships between systems",
                "It generates more alerts",
                "It's easier to implement"
            ],
            "correct": 1,
            "explanation": "Topology-based correlation takes into account the relationships and dependencies between systems, allowing for more accurate identification of root causes and related alerts."
        },
        {
            "question": "In a network topology, what does a node typically represent?",
            "options": [
                "A physical location",
                "A system or device",
                "An alert",
                "A network cable"
            ],
            "correct": 1,
            "explanation": "In a network topology, nodes typically represent systems or devices such as servers, routers, switches, or databases."
        },
        {
            "question": "How can path analysis help in alert correlation?",
            "options": [
                "By showing the shortest route for technicians",
                "By identifying potential cascading failures",
                "By increasing network speed",
                "By generating more alerts"
            ],
            "correct": 1,
            "explanation": "Path analysis can help identify potential cascading failures by showing how alerts propagate through connected systems in the network topology."
        },
        {
            "question": "What does a high number of connections for a node in a topology usually indicate?",
            "options": [
                "The node is unimportant",
                "The node is a potential single point of failure",
                "The node is rarely used",
                "The node is well-isolated"
            ],
            "correct": 1,
            "explanation": "A node with a high number of connections often indicates a critical component in the network, which could be a potential single point of failure if it experiences issues."
        },
        {
            "question": "Why is understanding the system type (e.g., Server, Router, Switch) important in topology-based correlation?",
            "options": [
                "It's not important",
                "It helps in determining the alert color",
                "It aids in understanding the potential impact and propagation of issues",
                "It determines the node size in the visualization"
            ],
            "correct": 2,
            "explanation": "Understanding the system type helps in assessing the potential impact of an issue and how it might propagate through the network, aiding in more accurate alert correlation and root cause analysis."
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