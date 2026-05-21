from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from pydantic import BaseModel
from database import get_session, supabase_client
from models import Aircraft, AircraftSpecs, Tag, Manufacturer, AircraftImage, AircraftTagLink
from typing import List, Optional

router = APIRouter(prefix="/api/v1", tags=["SkySpecs Core"])

# ==========================================
# ESQUEMAS DE ENTRADA (DTOs para recibir datos)
# ==========================================
class SpecsCreate(BaseModel):
    max_speed: str
    service_ceiling: str
    engines: int
    thrust_weight_ratio: float

class AircraftCreate(BaseModel):
    model: str
    manufacturer_name: str  
    type: str
    specs: SpecsCreate
    tags: List[str]         

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "model": "F-35A Lightning II",
                    "manufacturer_name": "Lockheed Martin",
                    "type": "Caza Polivalente Furtivo",
                    "specs": {
                        "max_speed": "Mach 1.6",
                        "service_ceiling": "15,000 m",
                        "engines": 1,
                        "thrust_weight_ratio": 0.87
                    },
                    "tags": ["sigilo", "supersónico", "militar"]
                }
            ]
        }
    }

class AircraftUpdate(BaseModel):
    model: Optional[str] = None
    type: Optional[str] = None


# ==========================================
# ESQUEMAS DE SALIDA 
# ==========================================
class TagRead(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class ManufacturerRead(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class SpecsRead(BaseModel):
    id: int
    max_speed: str
    service_ceiling: str
    engines: int
    thrust_weight_ratio: float
    class Config:
        from_attributes = True

class ImageRead(BaseModel):
    id: int
    url: str
    class Config:
        from_attributes = True

class AircraftDetail(BaseModel):
    id: int
    model: str
    type: str
    manufacturer: Optional[ManufacturerRead] = None
    specs: Optional[SpecsRead] = None
    tags: List[TagRead] = []
    image: Optional[ImageRead] = None
    class Config:
        from_attributes = True

# EL MOLDE RESUMIDO 
class AircraftSummary(BaseModel):
    id: int
    model: str
    manufacturer: Optional[ManufacturerRead] = None
    detalles_url: str 
    
    class Config:
        from_attributes = True


# ==========================================
# SECCIÓN: AERONAVES (AIRCRAFT)
# ==========================================

@router.get("/aircraft", response_model=List[AircraftSummary], summary="Catálogo resumido de aeronaves")
def read_all_aircrafts(session: Session = Depends(get_session)):
    """Devuelve un catálogo ligero solo con lo esencial y un link a la ficha técnica completa."""
    aviones = session.exec(select(Aircraft)).all()
    
    lista_resumida = []
    for avion in aviones:
        resumen = AircraftSummary(
            id=avion.id,
            model=avion.model,
            manufacturer=avion.manufacturer,
            detalles_url=f"/api/v1/aircraft/{avion.id}" 
        )
        lista_resumida.append(resumen)
        
    return lista_resumida

@router.get("/aircraft/{aircraft_id}", response_model=AircraftDetail, summary="Ficha técnica completa de la aeronave")
def read_single_aircraft(aircraft_id: int, session: Session = Depends(get_session)):
    """Devuelve el 100% de la información de la aeronave, incluyendo specs, fotos y tags."""
    aircraft = session.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")
    return aircraft

@router.post("/aircraft", response_model=AircraftDetail, summary="Registrar una nueva aeronave")
def create_aircraft(data: AircraftCreate, session: Session = Depends(get_session)):
    db_manufacturer = session.exec(select(Manufacturer).where(Manufacturer.name == data.manufacturer_name)).first()
    if not db_manufacturer:
        db_manufacturer = Manufacturer(name=data.manufacturer_name)
        session.add(db_manufacturer)
    
    db_specs = AircraftSpecs(**data.specs.model_dump())
    session.add(db_specs)
    
    db_tags = []
    for tag_name in data.tags:
        existing_tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
        if existing_tag:
            db_tags.append(existing_tag)
        else:
            new_tag = Tag(name=tag_name)
            session.add(new_tag)
            db_tags.append(new_tag)
            
    db_aircraft = Aircraft(
        model=data.model,
        type=data.type,
        manufacturer=db_manufacturer,
        specs=db_specs,
        tags=db_tags
    )
    
    session.add(db_aircraft)
    session.commit()
    session.refresh(db_aircraft)
    return db_aircraft

@router.get("/aircraft/{aircraft_id}", response_model=AircraftDetail, summary="Obtener una aeronave detallada por su ID")
def read_single_aircraft(aircraft_id: int, session: Session = Depends(get_session)):
    aircraft = session.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")
    return aircraft

@router.put("/aircraft/{aircraft_id}", response_model=AircraftDetail, summary="Actualizar datos básicos")
def update_aircraft(aircraft_id: int, data: AircraftUpdate, session: Session = Depends(get_session)):
    db_aircraft = session.get(Aircraft, aircraft_id)
    if not db_aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_aircraft, key, value)
        
    session.add(db_aircraft)
    session.commit()
    session.refresh(db_aircraft)
    return db_aircraft

@router.delete("/aircraft/{aircraft_id}", summary="Eliminar una aeronave ")
def delete_aircraft(aircraft_id: int, session: Session = Depends(get_session)):
    """Elimina la aeronave, limpia sus etiquetas, borra sus especificaciones y destruye sus fotos físicas en la nube."""
    db_aircraft = session.get(Aircraft, aircraft_id)
    if not db_aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")

    try:
        # 1. Eliminar la imagen física del Storage en Supabase
        if db_aircraft.image:
            archivo_a_borrar = db_aircraft.image.url.split("/")[-1]
            supabase_client.storage.from_("aircraft-images").remove([archivo_a_borrar])
            session.delete(db_aircraft.image)

        # Eliminar las relaciones de la tabla intermedia (Tags)
        links = session.exec(select(AircraftTagLink).where(AircraftTagLink.aircraft_id == aircraft_id)).all()
        for link in links:
            session.delete(link)

        #  Guardar el ID de las especificaciones para no dejar basura
        specs_id = db_aircraft.specs_id

        # ¡Ahora sí! Eliminar el avión principal de forma segura
        session.delete(db_aircraft)

        # Eliminar la ficha técnica (Specs) que quedó huérfana
        if specs_id:
            specs = session.get(AircraftSpecs, specs_id)
            if specs:
                session.delete(specs)

        # Confirmar todos los cambios
        session.commit()
        return {"mensaje": f"Aeronave con ID {aircraft_id} y todos sus datos relacionados fueron eliminados por completo."}
        
    except Exception as e:
        session.rollback() # Si algo falla, deshacemos los cambios para no corromper la base de datos
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar: {str(e)}")

# ==========================================
# SECCIÓN: IMÁGENES (MEDIA MULTIMEDIA)
# ==========================================

@router.post("/aircraft/{aircraft_id}/upload-image", summary="Subir o reemplazar la foto de la aeronave")
async def upload_aircraft_image(
    aircraft_id: int, 
    file: UploadFile = File(...), 
    session: Session = Depends(get_session)
):
    """Sube una nueva foto. Si el avión ya tenía una, la anterior se elimina permanentemente para ahorrar espacio."""
    db_aircraft = session.get(Aircraft, aircraft_id)
    if not db_aircraft:
        raise HTTPException(status_code=404, detail="Aeronave no encontrada")

    file_bytes = await file.read()
    file_path = f"{aircraft_id}_{file.filename}"

    try:
        # Si ya existe una foto, la borramos del Storage de Supabase
        if db_aircraft.image:
            old_file_path = db_aircraft.image.url.split("/")[-1]
            if old_file_path != file_path:  # Por si se llama igual, evitamos borrar la que vamos a subir
                supabase_client.storage.from_("aircraft-images").remove([old_file_path])

        # Subimos la nueva foto (upsert=true sobreescribe si el nombre es idéntico)
        supabase_client.storage.from_("aircraft-images").upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )

        public_url = supabase_client.storage.from_("aircraft-images").get_public_url(file_path)

        # Si ya existía el registro en la BD, solo actualizamos la URL. Si no, lo creamos.
        if db_aircraft.image:
            db_aircraft.image.url = public_url
            session.add(db_aircraft.image)
        else:
            new_image = AircraftImage(url=public_url, aircraft_id=aircraft_id)
            session.add(new_image)
            
        session.commit()

        return {"mensaje": "Imagen guardada y vinculada con éxito", "url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")

@router.put("/images/{image_id}", response_model=ImageRead, summary="Reemplazar/Actualizar una imagen existente")
async def update_image(
    image_id: int, 
    file: UploadFile = File(...), 
    session: Session = Depends(get_session)
):
    """
    Reemplaza el archivo físico en el Storage y actualiza su URL en la base de datos.
    """
    # Verificar si la imagen existe en la base de datos
    db_image = session.get(AircraftImage, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
        
    old_file_path = db_image.url.split("/")[-1]
    
    try:
        # Eliminar el archivo viejo del Storage de Supabase
        supabase_client.storage.from_("aircraft-images").remove([old_file_path])
        
        # Leer y subir el nuevo archivo físico
        file_bytes = await file.read()
        new_file_path = f"{db_image.aircraft_id}_{file.filename}"
        
        supabase_client.storage.from_("aircraft-images").upload(
            path=new_file_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        
        # Obtener la nueva URL pública generada
        new_public_url = supabase_client.storage.from_("aircraft-images").get_public_url(new_file_path)
        
        # Actualizar el registro en PostgreSQL
        db_image.url = new_public_url
        session.add(db_image)
        session.commit()
        session.refresh(db_image)
        
        return db_image
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el archivo de imagen: {str(e)}")


@router.delete("/images/{image_id}", summary="Eliminar una imagen específica")
def delete_image(image_id: int, session: Session = Depends(get_session)):
    """
    Elimina permanentemente una imagen del sistema.

    """
    # Verificar si la imagen existe
    db_image = session.get(AircraftImage, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
        
    # Extraer el nombre del archivo a partir de la URL pública
    file_path = db_image.url.split("/")[-1]
    
    try:
        # Eliminar el archivo del Storage de Supabase para liberar espacio
        supabase_client.storage.from_("aircraft-images").remove([file_path])
        
        # Eliminar el registro de la base de datos
        session.delete(db_image)
        session.commit()
        
        return {
            "mensaje": f"Imagen con ID {image_id} eliminada correctamente."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar la imagen del sistema: {str(e)}")


# ==========================================
# SECCIÓN: MARCAS (MANUFACTURERS) - COMPLETADA
# ==========================================

@router.get("/manufacturers", response_model=List[ManufacturerRead], summary="Listar todas las marcas")
def read_manufacturers(session: Session = Depends(get_session)):
    return session.exec(select(Manufacturer)).all()



@router.get("/manufacturers/{manufacturer_id}/aircraft", response_model=List[AircraftSummary], summary="Obtener aeronaves completas de un fabricante")
def read_aircraft_by_manufacturer(manufacturer_id: int, session: Session = Depends(get_session)):
    """Devuelve todos los aviones de la marca con sus fichas técnicas e imágenes cargadas."""
    manufacturer = session.get(Manufacturer, manufacturer_id)
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return manufacturer.aircrafts


# ==========================================
# SECCIÓN: ETIQUETAS (TAGS) - COMPLETADA
# ==========================================

@router.get("/tags", response_model=List[TagRead], summary="Listar todas las etiquetas")
def read_tags(session: Session = Depends(get_session)):
    return session.exec(select(Tag)).all()



@router.get("/tags/{tag_id}/aircraft", response_model=List[AircraftSummary], summary="Obtener aeronaves completas por etiqueta")
def read_aircraft_by_tag(tag_id: int, session: Session = Depends(get_session)):
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    return tag.aircrafts