"""
vantage_data.py

Core data access layer for Vantage. Loads the synthetic dataset
(users, resources, access grants, activity log) and builds the
access graph (Fabric IQ semantic model pattern using networkx).

This module is the single source of truth that both the MCP server
and the agent pipeline read from.
"""

import json
import os
import networkx as nx

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _load(filename):
    with open(os.path.join(DATA_DIR, filename), "r") as f:
        return json.load(f)


def load_all_data():
    """Load all four synthetic datasets."""
    return {
        "users": _load("users.json"),
        "resources": _load("resources.json"),
        "access_grants": _load("access_grants.json"),
        "activity_log": _load("activity_log.json")["activity"],
    }


def build_access_graph(data=None):
    """
    Build the Fabric IQ-style semantic access graph.

    Nodes: users (type=user) and resources (type=resource)
    Edges: access grants, with attributes (access_level, grant_id, etc.)
    """
    if data is None:
        data = load_all_data()

    G = nx.DiGraph()

    for user in data["users"]:
        G.add_node(
            user["user_id"],
            node_type="user",
            name=user["name"],
            role=user["role"],
            department=user["department"],
            tenure_months=user["tenure_months"],
        )

    for res in data["resources"]:
        G.add_node(
            res["resource_id"],
            node_type="resource",
            name=res["name"],
            resource_type=res["type"],
            department_owner=res["department_owner"],
            sensitivity=res["sensitivity"],
        )

    for grant in data["access_grants"]:
        G.add_edge(
            grant["user_id"],
            grant["resource_id"],
            grant_id=grant["grant_id"],
            access_level=grant["access_level"],
            granted_date=grant["granted_date"],
            reason_on_file=grant["reason_on_file"],
        )

    return G


def get_user_access(user_id, data=None):
    """Return all access grants held by a given user, with resource details."""
    if data is None:
        data = load_all_data()

    resources_by_id = {r["resource_id"]: r for r in data["resources"]}
    user_by_id = {u["user_id"]: u for u in data["users"]}

    if user_id not in user_by_id:
        return {"error": f"User {user_id} not found"}

    grants = []
    for grant in data["access_grants"]:
        if grant["user_id"] == user_id:
            resource = resources_by_id.get(grant["resource_id"], {})
            grants.append({
                "grant_id": grant["grant_id"],
                "resource_id": grant["resource_id"],
                "resource_name": resource.get("name"),
                "resource_sensitivity": resource.get("sensitivity"),
                "access_level": grant["access_level"],
                "granted_date": grant["granted_date"],
                "reason_on_file": grant["reason_on_file"],
            })

    return {
        "user": user_by_id[user_id],
        "access_grants": grants,
    }


def check_dormant_access(user_id, days=30, data=None):
    """
    For a given user, return all access grants with zero or near-zero
    activity in the last `days` days (default 30), based on activity_log.json.
    """
    if data is None:
        data = load_all_data()

    activity_by_key = {
        (a["user_id"], a["resource_id"]): a for a in data["activity_log"]
    }
    resources_by_id = {r["resource_id"]: r for r in data["resources"]}

    dormant = []
    active = []

    for grant in data["access_grants"]:
        if grant["user_id"] != user_id:
            continue

        key = (grant["user_id"], grant["resource_id"])
        activity = activity_by_key.get(key)
        resource = resources_by_id.get(grant["resource_id"], {})

        entry = {
            "grant_id": grant["grant_id"],
            "resource_id": grant["resource_id"],
            "resource_name": resource.get("name"),
            "access_level": grant["access_level"],
            "access_count_30d": activity["access_count_30d"] if activity else None,
            "last_accessed": activity["last_accessed"] if activity else None,
            "notes": activity["notes"] if activity else "No activity data recorded.",
        }

        if activity and activity["access_count_30d"] == 0:
            dormant.append(entry)
        else:
            active.append(entry)

    return {
        "user_id": user_id,
        "days_checked": days,
        "dormant_access": dormant,
        "active_access": active,
    }


def get_all_grants_with_context(data=None):
    """
    Return every access grant enriched with user, resource, and activity
    context in one shot. This is the primary input to the Risk Scoring Agent.
    """
    if data is None:
        data = load_all_data()

    users_by_id = {u["user_id"]: u for u in data["users"]}
    resources_by_id = {r["resource_id"]: r for r in data["resources"]}
    activity_by_key = {
        (a["user_id"], a["resource_id"]): a for a in data["activity_log"]
    }

    enriched = []
    for grant in data["access_grants"]:
        user = users_by_id.get(grant["user_id"], {})
        resource = resources_by_id.get(grant["resource_id"], {})
        activity = activity_by_key.get((grant["user_id"], grant["resource_id"]))

        enriched.append({
            "grant_id": grant["grant_id"],
            "user_id": grant["user_id"],
            "user_name": user.get("name"),
            "user_role": user.get("role"),
            "user_department": user.get("department"),
            "user_tenure_months": user.get("tenure_months"),
            "preferred_change_window": user.get("preferred_change_window"),
            "current_workload": user.get("current_workload"),
            "resource_id": grant["resource_id"],
            "resource_name": resource.get("name"),
            "resource_sensitivity": resource.get("sensitivity"),
            "access_level": grant["access_level"],
            "granted_date": grant["granted_date"],
            "reason_on_file": grant["reason_on_file"],
            "access_count_30d": activity["access_count_30d"] if activity else None,
            "last_accessed": activity["last_accessed"] if activity else None,
            "activity_notes": activity["notes"] if activity else "No activity data recorded.",
        })

    return enriched


def get_resource_owners(resource_id, data=None):
    """Return all users who have access to a given resource."""
    if data is None:
        data = load_all_data()

    users_by_id = {u["user_id"]: u for u in data["users"]}
    resources_by_id = {r["resource_id"]: r for r in data["resources"]}

    if resource_id not in resources_by_id:
        return {"error": f"Resource {resource_id} not found"}

    holders = []
    for grant in data["access_grants"]:
        if grant["resource_id"] == resource_id:
            user = users_by_id.get(grant["user_id"], {})
            holders.append({
                "user_id": grant["user_id"],
                "user_name": user.get("name"),
                "role": user.get("role"),
                "access_level": grant["access_level"],
            })

    return {
        "resource": resources_by_id[resource_id],
        "access_holders": holders,
    }


if __name__ == "__main__":
    # quick self-test
    data = load_all_data()
    G = build_access_graph(data)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print()
    print("EMP-002 (Raj Mehta) access + dormancy check:")
    print(json.dumps(check_dormant_access("EMP-002", data=data), indent=2))
