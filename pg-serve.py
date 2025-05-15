from pydantic.types import UUID4
from sqlalchemy import and_, delete, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from api.database import db_writer
from api.instrumentation import instrument_all_functions
from api.models import Job, Run, RunMetric, RunTag, RunUpdate, XRayCard
from api.schemas.run import RunCreate, RunMetricCreate, RunTagCreate, RunUpdateRequestResolved, TagType
from rungalileo.schemas.run import Split
from rungalileo.schemas.task_type import TaskType


@instrument_all_functions()
class RunDAO:
    def get(self, db_read: Session, run_id: UUID4) -> Run | None:
        return db_read.query(Run).filter(Run.id == run_id).first()

    def get_by_name(self, db_read: Session, project_id: UUID4, run_name: str) -> Run | None:
        return db_read.query(Run).filter(Run.project_id == project_id, Run.name == run_name).first()

    def get_all(self, db_read: Session, run_ids: list[UUID4]) -> list[Run]:
        return db_read.query(Run).filter(Run.id.in_(run_ids)).all()

    def create(self, run_create: RunCreate) -> Run:
        with db_writer() as db:
            run = Run(**run_create.model_dump())
            db.add(run)
            run = db.merge(run)
            db.commit()
            db.refresh(run)
            for tag in run_create.run_tags:
                self.upsert_tag(
                    RunTagCreate(
                        project_id=run.project_id, run_id=run.id, created_by=run.created_by, **tag.model_dump()
                    )
                )
            run.refresh(db)
        return run

    def create_run_update(self, run_id: UUID4, updated_by: UUID4) -> None:
        with db_writer() as db:
            run_update = RunUpdate(run_id=run_id, updated_by=updated_by)
            db.add(run_update)

    def update(self, run_id: UUID4, run_update: RunUpdateRequestResolved) -> Run:
        with db_writer() as db:
            # Remove all empty fields (in case only certain fields are updated)
            update = {k: v for k, v in run_update.model_dump().items() if v}
            run = Run(id=run_id, **update)
            db.query(Run).filter(Run.id == run_id).update(update)
            run = db.merge(run)
            # Create a run update log.
            self.create_run_update(run_id, run_update.updated_by)
            # Refresh the run after adding a `RunUpdate` row to correctly resolve the
            # `last_updated_by` field.
            db.refresh(run)
        return run

    def delete(self, run_ids: list[UUID4]) -> list[UUID4]:
        """Delete run and return all associated job_ids."""
        with db_writer() as db:
            # Get job_ids associated with the runs.
            job_ids = db.execute(select(Job.id).filter(Job.run_id.in_(run_ids))).scalars().all()
            db.execute(delete(Run).where(Run.id.in_(run_ids)))
        return job_ids

    