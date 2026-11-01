from platform_contract import RunService, RunState

service = RunService()
run = service.create_run("agent-a", "session-1", "hello", idempotency_key="request-1")
assert service.create_run("agent-a", "session-1", "hello", idempotency_key="request-1").id == run.id
service.transition(run.id, RunState.RUNNING)
service.transition(run.id, RunState.SUCCEEDED, output="world")
assert run.state is RunState.SUCCEEDED
assert [event.sequence for event in service.store.events(run.id)] == [1, 2, 3]
print("platform_contract smoke test: OK")
