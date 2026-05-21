from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Tabla intermedia Muchos-a-Muchos (Aircraft <-> Tag)
class AircraftTagLink(SQLModel, table=True):
    aircraft_id: int = Field(foreign_key="aircraft.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)

# Tabla de Etiquetas (Tags)
class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    aircrafts: List["Aircraft"] = Relationship(back_populates="tags", link_model=AircraftTagLink)

# Tabla de Fabricantes / Marcas (Relación 1-a-Muchos con Aircraft)
class Manufacturer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    aircrafts: List["Aircraft"] = Relationship(back_populates="manufacturer")

# Tabla de Especificaciones Técnicas (Specs - Relación 1-a-1)
class AircraftSpecs(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    max_speed: str
    service_ceiling: str
    engines: int
    thrust_weight_ratio: float
    aircraft: Optional["Aircraft"] = Relationship(back_populates="specs")

# Tabla Principal de Aeronaves
class Aircraft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model: str = Field(index=True)
    type: str
    
    # Conexión con la Marca (Manufacturer)
    manufacturer_id: Optional[int] = Field(default=None, foreign_key="manufacturer.id")
    manufacturer: Optional[Manufacturer] = Relationship(back_populates="aircrafts")
    
    # Conexión con las Especificaciones (Specs)
    specs_id: Optional[int] = Field(default=None, foreign_key="aircraftspecs.id")
    specs: Optional[AircraftSpecs] = Relationship(back_populates="aircraft")
    
    # Conexión con las Etiquetas (Tags)
    tags: List[Tag] = Relationship(back_populates="aircrafts", link_model=AircraftTagLink)

    # Conexión con imágenes (AircraftImage)
    image: Optional[AircraftImage] = Relationship(
        sa_relationship_kwargs={"uselist": False},
        back_populates="aircraft"
    )

# Tabla de Imágenes de Aeronaves
class AircraftImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str  # Aquí guardaremos el link público
    aircraft_id: int = Field(foreign_key="aircraft.id")
    
    # Relación inversa hacia el avión
    aircraft: Optional["Aircraft"] = Relationship(back_populates="image")