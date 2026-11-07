import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.project import Project, ProjectActivity, ProjectItem
from app.models.user import User
from app.schemas.projects import (
    ProjectActivityResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectItemCreate,
    ProjectItemResponse,
    ProjectSummaryResponse,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Research Projects"])


@router.post(
    "",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new research project",
)
def create_project(
    payload: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectDetailResponse:
    """Create a research project owned by the current authenticated user."""
    project = Project(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        status=payload.status,
        tags=payload.tags or [],
    )
    db.add(project)
    db.flush()

    activity = ProjectActivity(
        project_id=project.id,
        user_id=current_user.id,
        action="created_project",
        details={"name": project.name},
    )
    db.add(activity)
    db.commit()
    db.refresh(project)

    return ProjectDetailResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        status=project.status,
        tags=project.tags,
        items_count=0,
        items=[],
        activities=[ProjectActivityResponse.model_validate(activity)],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get(
    "",
    response_model=list[ProjectSummaryResponse],
    summary="List all research projects for current user",
)
def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
) -> list[ProjectSummaryResponse]:
    """Retrieve all projects belonging to the authenticated user."""
    query = (
        select(
            Project,
            func.count(ProjectItem.id).label("items_count"),
        )
        .outerjoin(ProjectItem, Project.id == ProjectItem.project_id)
        .where(Project.user_id == current_user.id)
        .group_by(Project.id)
        .order_by(Project.updated_at.desc())
    )

    if status_filter:
        query = query.where(Project.status == status_filter)

    results = db.execute(query).all()
    summaries = []
    for project, count in results:
        summary = ProjectSummaryResponse(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            status=project.status,
            tags=project.tags,
            items_count=count,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        summaries.append(summary)

    return summaries


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get project details, items, and activity history",
)
def get_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectDetailResponse:
    """Retrieve a project and its nested entities. Enforces user ownership."""
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    return ProjectDetailResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        status=project.status,
        tags=project.tags,
        items_count=len(project.items),
        items=[ProjectItemResponse.model_validate(item) for item in project.items],
        activities=[ProjectActivityResponse.model_validate(act) for act in project.activities],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Update project metadata",
)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectDetailResponse:
    """Update project name, description, status, or tags."""
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    changes = {}
    if payload.name is not None:
        project.name = payload.name.strip()
        changes["name"] = project.name
    if payload.description is not None:
        project.description = payload.description.strip()
        changes["description"] = project.description
    if payload.status is not None:
        project.status = payload.status
        changes["status"] = project.status
    if payload.tags is not None:
        project.tags = payload.tags
        changes["tags"] = project.tags

    if changes:
        activity = ProjectActivity(
            project_id=project.id,
            user_id=current_user.id,
            action="updated_project",
            details=changes,
        )
        db.add(activity)

    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectDetailResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        status=project.status,
        tags=project.tags,
        items_count=len(project.items),
        items=[ProjectItemResponse.model_validate(item) for item in project.items],
        activities=[ProjectActivityResponse.model_validate(act) for act in project.activities],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a research project",
)
def delete_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a research project and all associated items and activities."""
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    db.delete(project)
    db.commit()


@router.post(
    "/{project_id}/items",
    response_model=ProjectItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a target entity or note to project",
)
def add_project_item(
    project_id: int,
    payload: ProjectItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectItemResponse:
    """Add a gene, protein, compound, disease, sequence, or note to a project."""
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    item = ProjectItem(
        project_id=project.id,
        item_type=payload.item_type,
        item_id=payload.item_id.strip(),
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        metadata_json=payload.metadata_json or {},
    )
    db.add(item)
    db.flush()

    activity = ProjectActivity(
        project_id=project.id,
        user_id=current_user.id,
        action=f"added_{payload.item_type}",
        details={"title": item.title, "item_id": item.item_id},
    )
    db.add(activity)
    db.commit()
    db.refresh(item)

    return ProjectItemResponse.model_validate(item)


@router.delete(
    "/{project_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an entity from a project",
)
def remove_project_item(
    project_id: int,
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Remove a specific item from a project."""
    item = db.scalar(
        select(ProjectItem)
        .join(Project, ProjectItem.project_id == Project.id)
        .where(
            ProjectItem.id == item_id,
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found or access denied",
        )

    activity = ProjectActivity(
        project_id=project_id,
        user_id=current_user.id,
        action=f"removed_{item.item_type}",
        details={"title": item.title, "item_id": item.item_id},
    )
    db.add(activity)
    db.delete(item)
    db.commit()
