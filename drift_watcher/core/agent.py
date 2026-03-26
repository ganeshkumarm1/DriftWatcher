import time
from ..tracking import EventReader, ActivityProcessor
from ..llm import LLMReasoner, OllamaClient, BedrockClient
from ..utils import Notifier
from ..config import Config
from .state_manager import StateManager


EVENTS_FILE = "events.log"

PROVIDERS = {
    "ollama": OllamaClient,
    "bedrock": BedrockClient,
}


def build_llm_client(llm_config: dict):
    """Build LLM client from config."""
    config = llm_config.copy()
    provider = config.pop("provider", "ollama")

    client_class = PROVIDERS.get(provider)
    if not client_class:
        raise ValueError(f"Unknown provider '{provider}'. Available: {list(PROVIDERS.keys())}")

    return client_class(**config)


def run_agent_loop(config_file: str = "config.json", goal: str = None):
    """Main loop that monitors focus and detects drift."""
    print("🧠 Drift Watcher started")
    
    # Load configuration
    config = Config(config_file)
    provider = config.llm_config.get("provider", "ollama")
    model_name = config.llm_config.get("model", config.llm_config.get("model_id", "unknown"))
    print(f"📋 Provider: {provider} | Model: {model_name} | Window: {config.window_seconds}s")
    print(f"📊 Dashboard: http://{config.server_host}:{config.server_port}/dashboard")
    
    # Initialize LLM client
    try:
        llm_client = build_llm_client(config.llm_config)
        print(f"🤖 LLM: {llm_client.name}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        return
    
    # Initialize components
    state_manager = StateManager()
    event_reader = EventReader(EVENTS_FILE, max_age_days=config.log_retention_days)
    activity_processor = ActivityProcessor()
    reasoner = LLMReasoner(client=llm_client)
    notifier = Notifier()
    
    # Handle goal changes and log cleanup
    if goal:
        state = state_manager.reset_logs_on_goal_change(goal)
        print(f"🎯 Goal updated: {goal}")
    else:
        state = state_manager.load()
        goal = state["goal"]
        print(f"🎯 Goal: {goal}")
    
    # Cleanup old logs on startup
    removed = event_reader.cleanup_old_logs()
    if removed > 0:
        print(f"🗑️  Cleaned up {removed} old log entries")
    
    loop_count = 0
    
    while True:
        try:
            time.sleep(config.window_seconds)
            loop_count += 1
            
            # Cleanup old logs every 100 loops (~50 minutes at 30s intervals)
            if loop_count % 100 == 0:
                removed = event_reader.cleanup_old_logs()
                if removed > 0:
                    print(f"🗑️  Cleaned up {removed} old log entries")
            
            events = event_reader.read_recent(config.window_seconds)
            
            if not events:
                print("… no events in last window")
                continue
            
            print(f"🔍 Events in window: {len(events)}")
            
            activity_summary = activity_processor.aggregate(events)
            
            # Single LLM call to assess focus state
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
            
            # Check for drift and notify
            if state_value == "DRIFTING" and confidence >= config.drift_threshold:
                print(f"⚠️ DRIFT DETECTED! Confidence: {confidence:.2f} >= {config.drift_threshold}")
                
                previous_state = state.get("focus_state", "FOCUSED")
                if previous_state == "FOCUSED":
                    state["drift_count"] = state.get("drift_count", 0) + 1
                
                notifier.notify_drift(goal, confidence)
            elif state_value == "DRIFTING":
                print(f"⚠️ Drifting but confidence too low: {confidence:.2f} < {config.drift_threshold}")
            
            # Update and save state
            state["focus_state"] = state_value
            state["confidence"] = confidence
            state["last_check_ts"] = time.time()
            state["relevant_percent"] = relevant_percent
            state["irrelevant_percent"] = irrelevant_percent
            state_manager.save(state)
        
        except KeyboardInterrupt:
            print("\n🛑 Drift Watcher stopped")
            break
        
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)
