# @steered SNARE-1 2026-09-18
import time
from ..tracking import EventReader, ActivityProcessor
from ..llm import LLMReasoner, OllamaClient, BedrockClient, ClaudeCliClient
from ..utils import Notifier
from ..config import Config
from .state_manager import StateManager


EVENTS_FILE = "events.log"

PROVIDERS = {
    "ollama": OllamaClient,
    "bedrock": BedrockClient,
    "claude-cli": ClaudeCliClient,
}


def build_llm_client(llm_config: dict):
    """Build LLM client from config."""
    config = llm_config.copy()
    provider = config.pop("provider", "claude-cli")

    client_class = PROVIDERS.get(provider)
    if not client_class:
        raise ValueError(f"Unknown provider '{provider}'. Available: {list(PROVIDERS.keys())}")

    return client_class(**config)


def run_agent_loop(config_file: str = "config.json", goal: str = None):
    """Main loop that monitors focus and detects drift."""
    print("🧠 Drift Watcher started")

    config = Config(config_file)
    provider = config.llm_config.get("provider", "claude-cli")
    model_name = config.llm_config.get("model", config.llm_config.get("model_id", "unknown"))
    print(f"📋 Provider: {provider} | Model: {model_name} | Window: {config.window_seconds}s")
    print(f"📊 Dashboard: http://{config.server_host}:{config.server_port}/dashboard")

    try:
        llm_client = build_llm_client(config.llm_config)
        print(f"🤖 LLM: {llm_client.name}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        return

    state_manager = StateManager()
    # Read twice the sleep window to cover LLM call latency and timing gaps
    read_window_seconds = config.window_seconds * 2
    event_reader = EventReader(EVENTS_FILE, max_age_days=config.log_retention_days)
    activity_processor = ActivityProcessor()
    reasoner = LLMReasoner(client=llm_client)
    notifier = Notifier()

    if goal:
        state = state_manager.reset_logs_on_goal_change(goal)
        print(f"🎯 Goal updated: {goal}")
    else:
        state = state_manager.load()
        goal = state["goal"]
        if goal == "No goal set":
            print("⏳ No goal set — waiting for a goal to be set via the dashboard or --goal flag")
        else:
            print(f"🎯 Goal: {goal}")

    removed = event_reader.cleanup_old_logs()
    if removed > 0:
        print(f"🗑️  Cleaned up {removed} old log entries")

    loop_count = 0

    while True:
        try:
            time.sleep(config.window_seconds)
            loop_count += 1

            # Check pause state before doing anything
            current_state = state_manager.load()
            paused_until = current_state.get("paused_until", 0)
            if paused_until and time.time() < paused_until:
                remaining = int(paused_until - time.time())
                print(f"⏸  Paused — {remaining // 60}m {remaining % 60}s remaining")
                state_manager.save({**current_state, "agent_heartbeat_ts": time.time()})
                continue

            # Re-read goal from state every loop so UI goal changes take effect immediately
            current_state = state_manager.load()
            current_goal = current_state.get("goal", "No goal set")

            if current_goal == "No goal set":
                print("⏳ Waiting for a goal to be set…")
                continue

            if current_goal != goal:
                print(f"🎯 Goal changed: {current_goal}")
                goal = current_goal
                state = current_state

            if loop_count % 100 == 0:
                removed = event_reader.cleanup_old_logs()
                if removed > 0:
                    print(f"🗑️  Cleaned up {removed} old log entries")

            events = event_reader.read_recent(read_window_seconds)

            # Heartbeat — marks agent as alive even when no events arrive
            state_manager.save({**state_manager.load(), "agent_heartbeat_ts": time.time()})

            if not events:
                print("… no events in last window")
                continue

            print(f"🔍 Events in window: {len(events)}")

            activity_summary = activity_processor.aggregate(events)
            result = reasoner.assess_focus_state(goal, activity_summary)
            state_value = result["state"]
            confidence = result["confidence"]
            reason = result["reason"]
            relevant_percent = result.get("relevant_percent", 0.0)
            irrelevant_percent = result.get("irrelevant_percent", 0.0)

            print(
                f"🧭 State: {state_value} | "
                f"Confidence: {confidence} | "
                f"Relevant: {relevant_percent}% | "
                f"Reason: {reason}"
            )

            # Track previous state before updating
            previous_state = state.get("focus_state", "FOCUSED")

            # Push this assessment into recent_states for trend detection
            state = state_manager.push_recent_state(state, state_value, confidence)

            if state_value == "DRIFTING" and confidence >= config.drift_threshold:
                # Require 2 consecutive drifts before alerting to reduce false positives
                if state_manager.consecutive_drifts(state, config.drift_threshold, required=2):
                    print(f"⚠️ DRIFT DETECTED! Confidence: {confidence:.2f} >= {config.drift_threshold}")

                    # Load drift_count from disk to survive restarts correctly
                    persisted = state_manager.load()
                    if previous_state == "FOCUSED":
                        state["drift_count"] = persisted.get("drift_count", 0) + 1
                    else:
                        state["drift_count"] = persisted.get("drift_count", 0)

                    notifier.notify_drift(goal, confidence, reason=reason)

                    # Append to drift log for dashboard
                    drift_log = state.get("drift_log", [])
                    drift_log.append({
                        "ts": time.time(),
                        "reason": reason,
                        "confidence": round(confidence, 2),
                        "pages": [p.get("title", "") for p in activity_summary.get("pages", [])[:3]],
                    })
                    state["drift_log"] = drift_log[-50:]  # keep last 50
                else:
                    print(f"⚠️ Drifting (confidence {confidence:.2f}) — waiting for consecutive confirmation")
            elif state_value == "DRIFTING":
                print(f"⚠️ Drifting but confidence too low: {confidence:.2f} < {config.drift_threshold}")
            elif state_value == "FOCUSED" and previous_state == "DRIFTING":
                # User returned to focused state — send back-on-track signal
                notifier.notify_focused(goal)

            state["focus_state"] = state_value
            state["confidence"] = confidence
            state["last_check_ts"] = time.time()
            state["relevant_percent"] = relevant_percent
            state["irrelevant_percent"] = irrelevant_percent
            state["reason"] = reason
            state_manager.save(state)

        except KeyboardInterrupt:
            print("\n🛑 Drift Watcher stopped")
            break

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)
