import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st
from io import StringIO
from pyvis.network import Network

TOXIC_COMBOS = [
    {"Modify_Invoice", "Delete_Account"},
    {"Access_Billing", "Delete_Account"}
]

import streamlit.components.v1 as components

def visualize_pyvis_graph(G, alerts):
    net = Network(height="700px", width="100%", directed=True)

    for node, attr in G.nodes(data=True):
        color = {
            "user": "skyblue",
            "role": "lightgreen",
            "permission": "salmon"
        }.get(attr["type"], "gray")

        if node in [u for u, _ in alerts]:
            color = "red"

        net.add_node(node, label=node, color=color)

    for source, target, attr in G.edges(data=True):
        net.add_edge(source, target, title=attr["relation"])

    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 1,
        "size": 20,
        "font": {"size": 14}
      },
      "edges": {
        "arrows": {
          "to": {"enabled": true}
        },
        "smooth": true
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.3,
          "springLength": 95
        }
      }
    }
    """)

    net.save_graph("pyvis_graph.html")
    with open("pyvis_graph.html", "r", encoding="utf-8") as f:
        html_string = f.read()
        components.html(html_string, height=750, scrolling=True)


def build_graph(df):
    G = nx.DiGraph()

    for _, row in df.iterrows():
        user, role, perm = row['User'], row['Role'], row['Permission']

        G.add_node(user, type='user')
        G.add_node(role, type='role')
        G.add_node(perm, type='permission')

        G.add_edge(user, role, relation='has_role')
        G.add_edge(role, perm, relation='grants')

    return G


def get_user_permissions(df):
    user_perms = {}
    for _, row in df.iterrows():
        user, perm = row['User'], row['Permission']
        if user not in user_perms:
            user_perms[user] = set()
        user_perms[user].add(perm)
    return user_perms


def detect_toxic_combos(user_perms):
    alerts = []
    for user, perms in user_perms.items():
        for combo in TOXIC_COMBOS:
            if combo.issubset(perms):
                alerts.append((user, combo))
    return alerts
def generate_toxic_csv(alerts):
    rows = [{"User": user, "Toxic_Permissions": ", ".join(combo)} for user, combo in alerts]
    return pd.DataFrame(rows).to_csv(index=False).encode('utf-8')


def visualize_graph(G, alerts):
    pos = nx.spring_layout(G, seed=42)
    node_colors = []

    for node in G.nodes(data=True):
        if node[1]['type'] == 'user':
            node_colors.append('skyblue')
        elif node[1]['type'] == 'role':
            node_colors.append('lightgreen')
        else:
            node_colors.append('salmon')

    fig, ax = plt.subplots(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1200, edge_color='gray', ax=ax)
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

    for user, _ in alerts:
        if user in G.nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=[user], node_color='red', node_size=1400, ax=ax)

    return fig


def main():
    st.title("IAM Access Graph Analyzer")
    st.markdown("Upload a CSV with columns: User, Role, Permission")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        G = build_graph(df)
        user_perms = get_user_permissions(df)
        toxic_users = detect_toxic_combos(user_perms)

        if toxic_users:
            st.subheader("Toxic Permission Alerts:")
            for user, combo in toxic_users:
                st.error(f"⚠️ User '{user}' has toxic permission combo: {', '.join(combo)}")
        else:
            st.success("✅ No toxic combinations detected.")

        st.subheader("Access Graph")
        # fig = visualize_graph(G, toxic_users)
        # st.pyplot(fig)
        visualize_pyvis_graph(G, toxic_users)

        if toxic_users:
            st.subheader("Toxic Permission Alerts:")
            for user, combo in toxic_users:
                st.error(f"⚠️ User '{user}' has toxic permission combo: {', '.join(combo)}")

            # New Export Button
            toxic_csv = generate_toxic_csv(toxic_users)
            st.download_button("⬇️ Download Toxic Users CSV", toxic_csv, "toxic_users.csv", "text/csv")


        st.header("Result achieved heck yea !!!")

if __name__ == '__main__':
    main()
