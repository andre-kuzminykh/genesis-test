"""Generation Run tests — section 24."""
import pytest
from datetime import datetime
from src.enums.statuses import ExecutionStatus
from src.enums.types import GenerationMode
from src.models.execution import GenerationRun


class TestGenerationRunLifecycle:
    """Section 24 — Generation Run lifecycle."""

    @pytest.mark.generation
    def test_generation_run_created_with_context_package(self, generation_run):
        """Every generation action must use an explicit Context Package (section 23)."""
        assert generation_run.context_package_id is not None

    @pytest.mark.generation
    def test_generation_run_default_status_queued(self, generation_run):
        assert generation_run.status == ExecutionStatus.QUEUED

    @pytest.mark.generation
    def test_generation_run_lifecycle_queued_to_running(self, generation_run):
        generation_run.status = ExecutionStatus.RUNNING
        generation_run.started_at = datetime.utcnow()
        assert generation_run.status == ExecutionStatus.RUNNING
        assert generation_run.started_at is not None

    @pytest.mark.generation
    def test_generation_run_lifecycle_running_to_completed(self, generation_run):
        generation_run.status = ExecutionStatus.RUNNING
        generation_run.started_at = datetime.utcnow()
        generation_run.status = ExecutionStatus.COMPLETED
        generation_run.completed_at = datetime.utcnow()
        assert generation_run.status == ExecutionStatus.COMPLETED
        assert generation_run.completed_at is not None

    @pytest.mark.generation
    def test_generation_run_lifecycle_running_to_failed(self, generation_run):
        generation_run.status = ExecutionStatus.RUNNING
        generation_run.status = ExecutionStatus.FAILED
        assert generation_run.status == ExecutionStatus.FAILED

    @pytest.mark.generation
    def test_generation_run_versioned(self, generation_run):
        assert generation_run.version >= 1


class TestGenerationModes:
    """Section 24.2 — Supported generation modes."""

    @pytest.mark.generation
    @pytest.mark.parametrize("mode", list(GenerationMode))
    def test_all_generation_modes(self, mode):
        gr = GenerationRun(
            generation_run_id=f"gr-{mode.value}",
            target_entity_type="code_artifact",
            target_entity_id="ca-1",
            context_package_id="cp-1",
            generation_mode=mode,
        )
        assert gr.generation_mode == mode

    @pytest.mark.generation
    def test_deterministic_mode(self):
        """Deterministic mode should pin model, prompt template, and config (section 24.3)."""
        gr = GenerationRun(
            generation_run_id="gr-det",
            target_entity_type="code_artifact",
            target_entity_id="ca-1",
            context_package_id="cp-1",
            generation_mode=GenerationMode.DETERMINISTIC,
            model_ref="claude-3.5-sonnet",
            prompt_template_ref="template-v1",
        )
        assert gr.model_ref is not None
        assert gr.prompt_template_ref is not None

    @pytest.mark.generation
    def test_regenerate_mode_fields(self):
        """Regenerate mode must record reason and affected artifacts (section 24.3)."""
        gr = GenerationRun(
            generation_run_id="gr-regen",
            target_entity_type="code_artifact",
            target_entity_id="ca-1",
            context_package_id="cp-regen",
            generation_mode=GenerationMode.REGENERATE,
            initiated_by="user",
        )
        assert gr.generation_mode == GenerationMode.REGENERATE
        assert gr.initiated_by == "user"


class TestGenerationRunAudit:
    """Section 24.1 — Generation Run audit fields."""

    @pytest.mark.generation
    def test_generation_run_records_snapshots(self):
        gr = GenerationRun(
            generation_run_id="gr-snap",
            target_entity_type="code_artifact",
            target_entity_id="ca-1",
            context_package_id="cp-1",
            input_snapshot_ref="snapshot-in-1",
            output_snapshot_ref="snapshot-out-1",
        )
        assert gr.input_snapshot_ref is not None
        assert gr.output_snapshot_ref is not None

    @pytest.mark.generation
    def test_generation_run_records_initiator(self, generation_run):
        assert generation_run.initiated_by == "tester"

    @pytest.mark.generation
    def test_generation_run_records_target(self, generation_run):
        assert generation_run.target_entity_type == "code_artifact"
        assert generation_run.target_entity_id == "ca-1"
