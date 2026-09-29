import streamlit as st
import re
import json
import math
from datetime import datetime

# ============================================================
# INCIDENT RESPONSE AI AGENT - STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Incident Response AI Agent",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SESSION STATE
# ============================================================

if "incidents" not in st.session_state:
    st.session_state.incidents = []

if "memory" not in st.session_state:
    st.session_state.memory = [
        {
            "title": "Payment API database connection pool exhaustion",
            "service": "payment-api",
            "severity": "SEV-1",
            "description": "Database connection pool exhausted. QueuePool timeout errors caused HTTP 500 responses.",
            "root_cause": "Connection pool exhaustion after a deployment increased database connection usage.",
            "resolution": "Rolled back the deployment and restarted affected workers.",
            "similarity": 94,
            "resolution_time": "7 minutes",
        },
        {
            "title": "Payment service worker OOMKilled",
            "service": "payment-worker",
            "severity": "SEV-1",
            "description": "Kubernetes pods entered CrashLoopBackOff with Exit Code 137.",
            "root_cause": "Memory usage exceeded the configured container limit.",
            "resolution": "Rolled back deployment and increased memory allocation.",
            "similarity": 88,
            "resolution_time": "12 minutes",
        },
        {
            "title": "Redis authentication timeout",
            "service": "auth-service",
            "severity": "SEV-2",
            "description": "Redis connection timeout spike affected authentication requests.",
            "root_cause": "Redis connection saturation and increased request latency.",
            "resolution": "Restarted affected workers and tuned connection pool settings.",
            "similarity": 82,
            "resolution_time": "15 minutes",
        },
        {
            "title": "Checkout database timeout",
            "service": "checkout-api",
            "severity": "SEV-2",
            "description": "Checkout API experienced database timeout errors and elevated latency.",
            "root_cause": "Database connection saturation.",
            "resolution": "Reduced connection pressure and restarted application workers.",
            "similarity": 79,
            "resolution_time": "18 minutes",
        },
        {
            "title": "Authentication service Redis latency",
            "service": "auth-service",
            "severity": "SEV-2",
            "description": "Redis response latency increased significantly during traffic spike.",
            "root_cause": "Connection pool saturation.",
            "resolution": "Scaled workers and adjusted Redis pool configuration.",
            "similarity": 76,
            "resolution_time": "21 minutes",
        },
    ]

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "current_incident" not in st.session_state:
    st.session_state.current_incident = None

if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False

# ============================================================
# DEMO INCIDENTS
# ============================================================

DEMO_1 = """[ERROR] 2026-09-28 14:32:11
service=payment-api
status=500
message="Database connection pool exhausted"
active_connections=100
max_connections=100
ERROR sqlalchemy.exc.TimeoutError:
QueuePool limit of size 100 overflow 0 reached, connection timed out."""

DEMO_2 = """[ERROR] 2026-09-28 15:10:42
service=payment-worker
status=503
pod=payment-worker-7d8f9
state=CrashLoopBackOff
Exit Code 137
reason=OOMKilled
memory_usage=2048Mi
memory_limit=2048Mi"""

DEMO_3 = """[ERROR] 2026-09-28 16:21:08
service=auth-service
status=504
message="Redis connection timeout"
redis_pool_active=200
redis_pool_max=200
timeout=5000ms
request_latency=4820ms"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9_]+",
            text.lower()
        )
    )


def similarity_score(query, document):
    """
    Simple lexical similarity used for the demo.
    This provides a deterministic fallback when no external
    vector database/API is configured.
    """
    q = tokenize(query)
    d = tokenize(document)

    if not q or not d:
        return 0

    intersection = len(q.intersection(d))
    union = len(q.union(d))

    jaccard = intersection / union if union else 0

    # Boost important incident terms.
    important_terms = [
        "database",
        "connection",
        "pool",
        "timeout",
        "redis",
        "oom",
        "crashloopbackoff",
        "payment",
        "authentication",
        "memory",
        "500",
        "503",
        "504",
    ]

    boost = 0

    for term in important_terms:
        if term in q and term in d:
            boost += 2

    score = min(99, int(jaccard * 100 + boost))

    return max(score, 40)


def retrieve_similar_incidents(query, top_k=5):
    results = []

    for item in st.session_state.memory:
        searchable = (
            item["title"]
            + " "
            + item["service"]
            + " "
            + item["description"]
            + " "
            + item["root_cause"]
            + " "
            + item["resolution"]
        )

        score = similarity_score(query, searchable)

        copy_item = item.copy()
        copy_item["calculated_similarity"] = score

        results.append(copy_item)

    results.sort(
        key=lambda x: x["calculated_similarity"],
        reverse=True
    )

    return results[:top_k]


def detect_incident_type(text):
    text_lower = text.lower()

    if any(
        word in text_lower
        for word in [
            "queuepool",
            "connection pool",
            "database connection",
            "database timeout",
            "sqlalchemy",
        ]
    ):
        return "database_pool"

    if any(
        word in text_lower
        for word in [
            "oom",
            "oomkilled",
            "exit code 137",
            "crashloopbackoff",
            "memory limit",
        ]
    ):
        return "kubernetes_memory"

    if any(
        word in text_lower
        for word in [
            "redis",
            "redispool",
            "redis connection",
        ]
    ):
        return "redis"

    if any(
        word in text_lower
        for word in [
            "500",
            "502",
            "503",
            "504",
            "timeout",
            "latency",
        ]
    ):
        return "service_failure"

    return "unknown"


def determine_severity(text):
    text_lower = text.lower()

    if any(
        word in text_lower
        for word in [
            "oomkilled",
            "crashloopbackoff",
            "payment",
            "500",
            "503",
            "outage",
            "database connection pool exhausted",
        ]
    ):
        return "SEV-1"

    if any(
        word in text_lower
        for word in [
            "timeout",
            "latency",
            "redis",
            "504",
        ]
    ):
        return "SEV-2"

    return "SEV-3"


def extract_service(text):
    match = re.search(
        r"service\s*=\s*([A-Za-z0-9_-]+)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    match = re.search(
        r"service[:=]\s*([A-Za-z0-9_-]+)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return "unknown-service"


def analyze_incident(text):
    incident_type = detect_incident_type(text)
    severity = determine_severity(text)
    service = extract_service(text)

    similar = retrieve_similar_incidents(text)

    if incident_type == "database_pool":
        root_cause = (
            "The available database connections appear to be exhausted. "
            "The observed QueuePool timeout indicates that application "
            "requests are waiting for database connections that are not "
            "becoming available quickly enough."
        )

        hypothesis = (
            "A recent deployment, traffic increase, connection leak, "
            "or unexpectedly long-running database transactions may have "
            "increased connection usage."
        )

        workaround = [
            "Pause or reduce incoming traffic if possible.",
            "Restart affected application workers if approved.",
            "Temporarily reduce connection pressure.",
            "Check active database connections before making configuration changes.",
        ]

        diagnostic = [
            "Inspect active database connections.",
            "Check connection pool configuration.",
            "Review recent deployments.",
            "Look for long-running database transactions.",
            "Check application connection release behavior.",
        ]

        permanent = [
            "Fix connection leaks if identified.",
            "Tune database connection pool limits.",
            "Review deployment changes affecting database usage.",
            "Add monitoring for connection pool saturation.",
        ]

        verification = [
            "Confirm database connections are below the configured limit.",
            "Verify HTTP 500 errors have returned to baseline.",
            "Monitor latency for several minutes.",
            "Confirm no new QueuePool timeout errors appear.",
        ]

        runbook = [
            "Check database connection utilization",
            "Inspect recent deployment",
            "Restart affected workers",
            "Verify API error rate",
        ]

    elif incident_type == "kubernetes_memory":
        root_cause = (
            "The Kubernetes workload is exceeding its configured memory "
            "limit, causing the container runtime to terminate the process "
            "with Exit Code 137."
        )

        hypothesis = (
            "The incident may have been caused by a memory-intensive "
            "deployment, increased workload, memory leak, or insufficient "
            "container memory limits."
        )

        workaround = [
            "Reduce traffic to the affected workload if possible.",
            "Rollback the most recent deployment if approved.",
            "Restart unhealthy pods.",
            "Temporarily increase memory allocation if appropriate.",
        ]

        diagnostic = [
            "Inspect pod memory usage.",
            "Review recent deployment changes.",
            "Check container memory limits and requests.",
            "Inspect application memory growth.",
            "Check pod restart history.",
        ]

        permanent = [
            "Fix the underlying memory leak if present.",
            "Optimize memory-intensive application operations.",
            "Set appropriate Kubernetes resource limits.",
            "Add memory alerts before reaching container limits.",
        ]

        verification = [
            "Confirm pods remain Running.",
            "Verify memory usage stays below limits.",
            "Confirm CrashLoopBackOff is cleared.",
            "Monitor application error rate.",
        ]

        runbook = [
            "Inspect pod status",
            "Check pod memory usage",
            "Rollback deployment if required",
            "Verify pod recovery",
        ]

    elif incident_type == "redis":
        root_cause = (
            "The Redis connection pool appears saturated or Redis responses "
            "are taking longer than the configured timeout."
        )

        hypothesis = (
            "A traffic spike, Redis latency increase, connection leak, "
            "or insufficient connection pool capacity may be contributing."
        )

        workaround = [
            "Reduce traffic to the affected service if possible.",
            "Restart affected workers if approved.",
            "Check Redis health and latency.",
            "Temporarily increase connection capacity if safe.",
        ]

        diagnostic = [
            "Check Redis latency.",
            "Inspect active Redis connections.",
            "Review connection pool configuration.",
            "Check recent application deployments.",
            "Inspect Redis server resource utilization.",
        ]

        permanent = [
            "Tune Redis connection pool configuration.",
            "Fix connection leaks.",
            "Optimize slow Redis operations.",
            "Add Redis latency and saturation alerts.",
        ]

        verification = [
            "Confirm Redis latency has returned to normal.",
            "Verify authentication errors are reduced.",
            "Check connection pool utilization.",
            "Monitor service health.",
        ]

        runbook = [
            "Check Redis health",
            "Inspect Redis connection usage",
            "Restart affected workers",
            "Verify authentication recovery",
        ]

    else:
        root_cause = (
            "The available telemetry indicates a service-level failure "
            "involving elevated errors, latency, or timeouts."
        )

        hypothesis = (
            "Possible contributors include a recent deployment, resource "
            "saturation, dependency failure, traffic increase, or "
            "configuration change."
        )

        workaround = [
            "Check service health and dependency status.",
            "Review recent deployments.",
            "Reduce traffic if possible.",
            "Restart affected components only after verification.",
        ]

        diagnostic = [
            "Inspect application logs.",
            "Check service metrics.",
            "Review recent deployments.",
            "Inspect dependent services.",
            "Compare current metrics with the normal baseline.",
        ]

        permanent = [
            "Identify and fix the underlying dependency or application issue.",
            "Add monitoring for the detected failure pattern.",
            "Document the verified root cause.",
        ]

        verification = [
            "Confirm error rate returns to baseline.",
            "Confirm latency returns to normal.",
            "Monitor the service for recurrence.",
        ]

        runbook = [
            "Check service health",
            "Inspect application logs",
            "Review recent deployment",
            "Verify recovery metrics",
        ]

    return {
        "incident_type": incident_type,
        "severity": severity,
        "service": service,
        "root_cause": root_cause,
        "hypothesis": hypothesis,
        "workaround": workaround,
        "diagnostic": diagnostic,
        "permanent": permanent,
        "verification": verification,
        "runbook": runbook,
        "similar": similar,
    }


def save_to_memory(incident, root_cause, takeaway):
    new_memory = {
        "title": f"Learned incident - {incident['service']}",
        "service": incident["service"],
        "severity": incident["severity"],
        "description": incident["description"][:500],
        "root_cause": root_cause,
        "resolution": takeaway,
        "similarity": 100,
        "resolution_time": "New",
        "learned_live": True,
    }

    st.session_state.memory.insert(0, new_memory)


def run_simulation(analysis):
    st.session_state.simulation_running = True

    st.success("Runbook simulation completed successfully.")

    st.code(
        """
$ kubectl get pods
payment-worker-7d8f9   Running

$ kubectl rollout undo deployment/payment-worker
deployment.apps/payment-worker rolled back

$ kubectl get pods
payment-worker-6f7d2   Running

$ monitoring
error_rate: 48.2% → 0.02%
status: HEALTHY
        """,
        language="bash",
    )

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🚨 Incident Response")
st.sidebar.caption("AI-powered SRE Assistant")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🚨 New Incident",
        "🧠 Incident Memory",
        "🛠️ Runbook Simulator",
        "📋 Post-Mortem",
        "🏗️ Architecture",
    ],
)

st.sidebar.divider()

st.sidebar.info(
    "This Streamlit version uses a deterministic SRE reasoning engine "
    "for reliable demos. External AI can be added later."
)

# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.title("🚨 Incident Response AI Agent")
    st.subheader("Autonomous AI SRE Assistant")

    st.write(
        "Analyze production incidents, retrieve similar historical "
        "incidents, generate remediation plans, simulate runbooks, "
        "and continuously learn from resolved incidents."
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Incidents",
            142 + len(st.session_state.incidents)
        )

    with col2:
        st.metric(
            "Memory Records",
            128 + len(st.session_state.memory)
        )

    with col3:
        st.metric(
            "Avg MTTR",
            "18m"
        )

    with col4:
        st.metric(
            "Service Health",
            "Healthy"
        )

    st.divider()

    st.subheader("Central Product Loop")

    cols = st.columns(7)

    stages = [
        "New Incident",
        "Retrieval",
        "RAG",
        "Remediation",
        "Runbook",
        "Post-Mortem",
        "Learning",
    ]

    for col, stage in zip(cols, stages):
        with col:
            st.info(stage)

    st.divider()

    st.subheader("🎯 Demo Scenarios")

    d1, d2, d3 = st.columns(3)

    with d1:
        st.markdown("### Demo 1")
        st.write("Payment API Database Pool Exhaustion")
        st.code("QueuePool limit reached")
        if st.button("Use Demo 1", key="dashboard_demo1"):
            st.session_state.current_incident = DEMO_1
            st.session_state.analysis = analyze_incident(DEMO_1)
            st.rerun()

    with d2:
        st.markdown("### Demo 2")
        st.write("Kubernetes OOM / CrashLoopBackOff")
        st.code("Exit Code 137")
        if st.button("Use Demo 2", key="dashboard_demo2"):
            st.session_state.current_incident = DEMO_2
            st.session_state.analysis = analyze_incident(DEMO_2)
            st.rerun()

    with d3:
        st.markdown("### Demo 3")
        st.write("Redis Connection Timeout")
        st.code("Redis timeout spike")
        if st.button("Use Demo 3", key="dashboard_demo3"):
            st.session_state.current_incident = DEMO_3
            st.session_state.analysis = analyze_incident(DEMO_3)
            st.rerun()

# ============================================================
# NEW INCIDENT
# ============================================================

elif page == "🚨 New Incident":

    st.title("🚨 New Incident")

    st.write(
        "Paste logs, stack traces, alerts, or incident telemetry below."
    )

    demo = st.selectbox(
        "Load a demo scenario",
        [
            "None",
            "Demo 1 - Payment API Database Pool",
            "Demo 2 - Kubernetes OOMKilled",
            "Demo 3 - Redis Timeout",
        ],
    )

    default_text = ""

    if demo.startswith("Demo 1"):
        default_text = DEMO_1
    elif demo.startswith("Demo 2"):
        default_text = DEMO_2
    elif demo.startswith("Demo 3"):
        default_text = DEMO_3

    incident_text = st.text_area(
        "Incident telemetry",
        value=default_text,
        height=250,
        placeholder="Paste your incident logs here...",
    )

    if st.button(
        "🔍 Analyze Incident",
        type="primary",
        use_container_width=True,
    ):

        if not incident_text.strip():
            st.warning("Please enter incident telemetry first.")

        else:

            with st.status(
                "Running Incident Response Agent...",
                expanded=True
            ):

                st.write("✓ Normalizing incident telemetry")
                st.write("✓ Generating semantic representation")
                st.write("✓ Searching historical incident memory")
                st.write("✓ Building evidence context")
                st.write("✓ Generating remediation plan")

            analysis = analyze_incident(incident_text)

            st.session_state.analysis = analysis
            st.session_state.current_incident = incident_text

            st.session_state.incidents.append(
                {
                    "description": incident_text,
                    "service": analysis["service"],
                    "severity": analysis["severity"],
                    "created": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            )

    if st.session_state.analysis:

        analysis = st.session_state.analysis

        st.divider()

        # ----------------------------------------------------
        # INCIDENT SUMMARY
        # ----------------------------------------------------

        st.subheader("Incident Summary")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Service", analysis["service"])

        with c2:
            st.metric("Severity", analysis["severity"])

        with c3:
            st.metric(
                "Incident Type",
                analysis["incident_type"]
            )

        # ----------------------------------------------------
        # EVIDENCE SEPARATION
        # ----------------------------------------------------

        st.subheader("🔎 Evidence Separation")

        observed, historical, hypothesis = st.tabs(
            [
                "Observed Evidence",
                "Historical Evidence",
                "AI Hypothesis",
            ]
        )

        with observed:
            st.write(
                "The following information comes directly from the "
                "incident telemetry provided by the engineer."
            )
            st.code(
                st.session_state.current_incident
            )

        with historical:
            st.write(
                "Historical evidence comes from similar incidents "
                "stored in organizational memory."
            )

            if analysis["similar"]:
                for item in analysis["similar"][:3]:
                    st.markdown(
                        f"**{item['title']}** — "
                        f"{item['calculated_similarity']}% similarity"
                    )

                    st.caption(
                        f"Previous resolution: {item['resolution']}"
                    )

        with hypothesis:
            st.warning(
                "AI hypothesis — this is a proposed explanation "
                "and should be verified by an engineer."
            )

            st.write(
                analysis["hypothesis"]
            )

        # ----------------------------------------------------
        # ROOT CAUSE
        # ----------------------------------------------------

        st.subheader("🧠 Root Cause Analysis")

        st.info(
            analysis["root_cause"]
        )

        # ----------------------------------------------------
        # SIMILAR INCIDENTS
        # ----------------------------------------------------

        st.subheader("🧠 Similar Incidents From Memory")

        for i, item in enumerate(
            analysis["similar"],
            start=1
        ):

            with st.expander(
                f"{i}. {item['title']} — "
                f"{item['calculated_similarity']}% similarity"
            ):

                st.write(
                    f"**Service:** {item['service']}"
                )

                st.write(
                    f"**Severity:** {item['severity']}"
                )

                st.write(
                    f"**Description:** {item['description']}"
                )

                st.write(
                    f"**Root Cause:** {item['root_cause']}"
                )

                st.write(
                    f"**Resolution:** {item['resolution']}"
                )

        # ----------------------------------------------------
        # WHY RECOMMENDATION
        # ----------------------------------------------------

        st.subheader("💡 Why This Recommendation?")

        if analysis["similar"]:

            best = analysis["similar"][0]

            st.write(
                f"The closest historical precedent is "
                f"**{best['title']}**, with a similarity score of "
                f"**{best['calculated_similarity']}%**."
            )

            st.write(
                "The recommended actions are based on the observed "
                "telemetry and the resolution patterns in historical "
                "incident memory."
            )

        # ----------------------------------------------------
        # FOUR STAGE REMEDIATION
        # ----------------------------------------------------

        st.subheader("🛠️ Multi-Stage Remediation Plan")

        with st.expander(
            "1️⃣ Immediate Workaround",
            expanded=True
        ):

            for step in analysis["workaround"]:
                st.checkbox(
                    step,
                    key=f"workaround_{step}"
                )

        with st.expander(
            "2️⃣ Diagnostic Isolation"
        ):

            for step in analysis["diagnostic"]:
                st.checkbox(
                    step,
                    key=f"diagnostic_{step}"
                )

        with st.expander(
            "3️⃣ Permanent Fix"
        ):

            for step in analysis["permanent"]:
                st.checkbox(
                    step,
                    key=f"permanent_{step}"
                )

        with st.expander(
            "4️⃣ Post-Recovery Verification"
        ):

            for step in analysis["verification"]:
                st.checkbox(
                    step,
                    key=f"verification_{step}"
                )

        # ----------------------------------------------------
        # RUNBOOK
        # ----------------------------------------------------

        st.subheader("📋 Suggested Runbook")

        for i, command in enumerate(
            analysis["runbook"],
            start=1
        ):
            st.write(
                f"**Step {i}.** {command}"
            )

        if st.button(
            "▶️ Open Runbook Simulator",
            use_container_width=True
        ):
            st.session_state.simulation_running = True
            st.rerun()

# ============================================================
# INCIDENT MEMORY
# ============================================================

elif page == "🧠 Incident Memory":

    st.title("🧠 Incident Memory")

    st.write(
        "Historical incidents and newly learned post-mortems."
    )

    search = st.text_input(
        "🔎 Search incident memory",
        placeholder="Try: database, redis, payment, OOM..."
    )

    filtered = st.session_state.memory

    if search.strip():

        search_tokens = tokenize(search)

        filtered = []

        for item in st.session_state.memory:

            text = (
                item["title"]
                + " "
                + item["service"]
                + " "
                + item["description"]
                + " "
                + item["root_cause"]
            )

            if search_tokens.intersection(
                tokenize(text)
            ):
                filtered.append(item)

    st.write(
        f"Showing **{len(filtered)}** memory records"
    )

    for item in filtered:

        badge = ""

        if item.get("learned_live"):
            badge = " 🟢 Learned Live"

        with st.expander(
            f"{item['title']}{badge}"
        ):

            c1, c2 = st.columns(2)

            with c1:
                st.write(
                    f"**Service:** {item['service']}"
                )

                st.write(
                    f"**Severity:** {item['severity']}"
                )

            with c2:
                st.write(
                    f"**Similarity:** {item.get('similarity', '-') }%"
                )

                st.write(
                    f"**Resolution time:** "
                    f"{item.get('resolution_time', '-')}"
                )

            st.write(
                f"**Description:** {item['description']}"
            )

            st.write(
                f"**Root Cause:** {item['root_cause']}"
            )

            st.write(
                f"**Resolution:** {item['resolution']}"
            )

# ============================================================
# RUNBOOK SIMULATOR
# ============================================================

elif page == "🛠️ Runbook Simulator":

    st.title("🛠️ Runbook Execution Simulator")

    st.warning(
        "This is a simulation. No real infrastructure commands "
        "are executed."
    )

    if not st.session_state.analysis:

        st.info(
            "Analyze an incident first to generate a runbook."
        )

    else:

        analysis = st.session_state.analysis

        st.subheader("Recommended Runbook")

        for i, step in enumerate(
            analysis["runbook"],
            start=1
        ):
            st.write(
                f"{i}. {step}"
            )

        st.divider()

        st.subheader("Terminal Simulator")

        if st.button(
            "▶️ Run Simulation",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "Executing simulated runbook..."
            ):

                st.write(
                    "Checking service health..."
                )

                st.write(
                    "Inspecting deployment state..."
                )

                st.write(
                    "Applying simulated remediation..."
                )

                st.write(
                    "Verifying recovery telemetry..."
                )

            run_simulation(analysis)

# ============================================================
# POST-MORTEM
# ============================================================

elif page == "📋 Post-Mortem":

    st.title("📋 Post-Mortem & Continuous Learning")

    if not st.session_state.analysis:

        st.info(
            "Analyze an incident first."
        )

    else:

        analysis = st.session_state.analysis

        st.write(
            "After the incident is resolved, record the verified "
            "root cause and the actual resolution."
        )

        st.subheader("Incident")

        st.write(
            f"**Service:** {analysis['service']}"
        )

        st.write(
            f"**Severity:** {analysis['severity']}"
        )

        verified_root_cause = st.text_area(
            "Verified Root Cause",
            value=analysis["root_cause"],
            height=150,
        )

        takeaway = st.text_area(
            "Actual Resolution / Takeaway",
            value=(
                "Incident resolved after applying the recommended "
                "remediation and verifying service recovery."
            ),
            height=150,
        )

        if st.button(
            "💾 Save to Incident Memory",
            type="primary",
            use_container_width=True,
        ):

            incident = {
                "description": (
                    st.session_state.current_incident
                    or ""
                ),
                "service": analysis["service"],
                "severity": analysis["severity"],
            }

            save_to_memory(
                incident,
                verified_root_cause,
                takeaway,
            )

            st.success(
                "✅ Post-mortem saved to organizational memory."
            )

            st.balloons()

            st.info(
                "The next similar incident can now retrieve "
                "this learned incident."
            )

# ============================================================
# ARCHITECTURE
# ============================================================

elif page == "🏗️ Architecture":

    st.title("🏗️ System Architecture")

    st.write(
        "The Streamlit implementation follows the same central "
        "product loop described in the original Incident Response "
        "Agent."
    )

    architecture = [
        ("1", "Incident / Logs / Alerts"),
        ("2", "Incident Analyzer"),
        ("3", "Semantic Retrieval"),
        ("4", "Historical Incident Memory"),
        ("5", "AI Reasoning / RAG"),
        ("6", "Remediation Plan"),
        ("7", "Runbook Simulator"),
        ("8", "Post-Mortem"),
        ("9", "Continuous Learning"),
    ]

    for number, title in architecture:

        st.markdown(
            f"""
            <div style="
                padding:12px;
                margin:8px 0;
                border-radius:10px;
                border:1px solid #444;
            ">
                <strong>{number}. {title}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if number != "9":
            st.markdown(
                "<div style='text-align:center'>↓</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    st.subheader("Technology")

    tech = {
        "Frontend": "Streamlit",
        "AI reasoning": "Deterministic SRE reasoning + optional Gemini",
        "Retrieval": "Similarity-based historical memory",
        "Memory": "Session-based incident knowledge base",
        "Runbooks": "Safe simulation only",
        "Learning": "Post-mortem → memory indexing",
    }

    st.json(tech)

# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "Incident Response AI Agent • Streamlit Demo"
)
