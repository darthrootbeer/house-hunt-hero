from __future__ import annotations

from src.scheduler.run import run_once


if __name__ == "__main__":
    run_once(
        sources_cfg_path="configs/sources.example.yaml",
        runtime_cfg_path="configs/runtime.example.yaml",
        profile_path="configs/house_profile.json",
        state_path="state/state.db",
    )
