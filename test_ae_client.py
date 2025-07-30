from vertexai import agent_engines

remote_app = agent_engines.get("projects/109790610330/locations/us-central1/reasoningEngines/4777571536733208576")

USER = "u_456"
SESSION_ID = "8538871622738640896"

session_list = [session["id"] for session in remote_app.list_sessions(user_id=USER)["sessions"]]
print(session_list)

if SESSION_ID not in session_list:
    remote_session = remote_app.create_session(user_id=USER)
    print(remote_session)
    raise Exception("Write and remember the printed session id")

for event in remote_app.stream_query(
    user_id="u_456",
    session_id=SESSION_ID,
    message="what can you help me with?",
):
    print(event)

print("-------------")

for event in remote_app.stream_query(
    user_id="u_456",
    session_id=SESSION_ID,
    message="show me pizza menu",
):
    print(event)

print("-------------")

for event in remote_app.stream_query(
    user_id="u_456",
    session_id=SESSION_ID,
    message="I want to order 1 veggie pizza",
):
    print(event)

print("-------------")
