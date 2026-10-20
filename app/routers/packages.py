from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.deps import get_current_admin
from app.models import Package, Admin
from app.schemas import PackageIn, PackageOut

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("", response_model=list[PackageOut])
def list_packages(session: Session = Depends(get_session)):
    """Public — the booking form needs this."""
    return session.exec(select(Package).where(Package.active == True)).all()


@router.get("/{package_id}", response_model=PackageOut)
def get_package(package_id: int, session: Session = Depends(get_session)):
    pkg = session.get(Package, package_id)
    if not pkg or not pkg.active:
        raise HTTPException(404, "Package not found")
    return pkg


@router.post("", response_model=PackageOut, dependencies=[Depends(get_current_admin)])
def create_package(data: PackageIn, session: Session = Depends(get_session)):
    pkg = Package(**data.model_dump())
    session.add(pkg)
    session.commit()
    session.refresh(pkg)
    return pkg


@router.patch("/{package_id}", response_model=PackageOut,
              dependencies=[Depends(get_current_admin)])
def update_package(package_id: int, data: PackageIn,
                   session: Session = Depends(get_session)):
    pkg = session.get(Package, package_id)
    if not pkg:
        raise HTTPException(404, "Package not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pkg, field, value)
    session.add(pkg)
    session.commit()
    session.refresh(pkg)
    return pkg


@router.delete("/{package_id}", dependencies=[Depends(get_current_admin)])
def delete_package(package_id: int, session: Session = Depends(get_session)):
    """Soft delete — keep the row so existing bookings referencing it stay valid."""
    pkg = session.get(Package, package_id)
    if not pkg:
        raise HTTPException(404, "Package not found")
    pkg.active = False
    session.add(pkg)
    session.commit()
    return {"deleted": package_id}