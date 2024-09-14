from sqlalchemy import create_engine, Column, Integer, String, Boolean, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from pydantic import BaseModel, EmailStr, constr, validator, Field
from typing import Optional, List
from contextlib import contextmanager
import copy

# Configuración de SQLAlchemy
Base = declarative_base()
engine = create_engine('sqlite:///tu_visa.db')
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

# Modelos SQLAlchemy
class ConfiguracionDB(Base):
    __tablename__ = 'configuracion'

    id = Column(Integer, primary_key=True,autoincrement = True)
    pais = Column(String(20), nullable=False, index=True)
    max_cuentas = Column(Integer, nullable=False)
    max_cuentas_scan = Column(Integer, nullable=False)
    time_refresh = Column(Integer, nullable=False)
    rango_busqueda = Column(Integer, nullable=False)
    show_browser_scan = Column(Boolean, nullable=False)
    show_browser_bot = Column(Boolean, nullable=False)
    wait_scan = Column(Integer, nullable=False)
    wait_bot = Column(Integer, nullable=False)
    url = Column(String(200),nullable=False)
    port = Column(Integer, nullable=False)

class CuentaFalsaDB(Base):
    __tablename__ = 'cuentas_falsas'

    id = Column(Integer, primary_key=True, autoincrement = True)
    pais = Column(String(20), nullable=False, index=True)
    email = Column(String(80), nullable=False)
    password = Column(String(2000), nullable=False)
    status = Column(Integer, nullable=False)

class CuentasDB(Base):
    __tablename__ = 'cuentas'

    id = Column(Integer, primary_key=True, autoincrement = True)
    pais = Column(String(20), nullable=False, index=True)
    email = Column(String(80), nullable=False)
    password = Column(String(2000), nullable=False)
    consulado = Column(String(50), nullable=True, index=True)
    cas = Column(String(50), nullable=True, index=True)
    status = Column(Integer, nullable=False, index=True)

###################################### Modelos Pydantic para validación ##########################

class ConfiguracionSchema(BaseModel):
    id: Optional[int] = None
    pais: constr(max_length=20)
    max_cuentas: int = Field(..., ge=0, le=99)
    max_cuentas_scan: int = Field(..., ge=0, le=99)
    time_refresh: int = Field(..., ge=0, le=99)
    rango_busqueda: int
    show_browser_scan: bool
    show_browser_bot: bool
    wait_scan: int
    wait_bot: int
    url : constr(max_length=200)
    port : int

    @validator('rango_busqueda', 'wait_scan', 'wait_bot', 'max_cuentas', 'max_cuentas_scan', 'time_refresh')
    def check_non_negative(cls, v):
        if v < 0:
            raise ValueError('Debe ser un número no negativo')
        return v

    class Config:
        from_attributes = True

class CuentaFalsaSchema(BaseModel):
    id: Optional[int] = None
    pais : constr(max_length=20)
    email: EmailStr
    password: constr(max_length=2000)
    status: int

    @validator('status')
    def check_status_range(cls, v):
        v = int(v)
        if not (0 <= v <= 99):
            raise ValueError('Debe estar entre 0 y 10')
        return v

    class Config:
        from_attributes = True

class CuentaSchema(BaseModel):
    id: Optional[int] = None
    pais : constr(max_length=20)
    email: EmailStr
    password: constr(max_length=2000)
    consulado: Optional[constr(max_length=50)] = None
    cas: Optional[constr(max_length=50)] = None
    status: int

    @validator('status')
    def check_status_range(cls, v):
        v = int(v)
        if not (0 <= v <= 99):
            raise ValueError('Debe estar entre 0 y 10')
        return v
    
class UpdateCuentaSchema(BaseModel):
    id: int
    status: int

    class Config:
        from_attributes = True

########################################## Acciones Base de Datos ##########################

class Database:
    @contextmanager
    def session_scope(self):
        session = Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def insert_multiple_configuraciones(self, configs: List[ConfiguracionSchema]):
        with self.session_scope() as session:
            db_configs = []
            for config in configs:
                db_config = ConfiguracionDB(**config.dict(exclude={'id'}))
                db_configs.append(db_config)
            
            session.add_all(db_configs)
            session.flush()
            return db_configs
        
    def insert_multiple_cuentas_falsas(self, configs: List[CuentaFalsaSchema]):
        with self.session_scope() as session:
            db_configs = []
            for config in configs:
                db_config = CuentaFalsaDB(**config.dict(exclude={'id'}))
                db_configs.append(db_config)
            
            session.add_all(db_configs)
            session.flush()
            return db_configs

    def get_cuentas_activas(self,pais: String):
        with self.session_scope() as session:
            cuentas = session.query(CuentasDB).filter(CuentasDB.status == 1, CuentasDB.pais == pais).all()
            if not cuentas:
                return None
            else:
                return [
                    {
                        'id': cuenta.id,
                        'email': cuenta.email,
                        'password': cuenta.password,
                        'pais': cuenta.pais,
                        'consulado': cuenta.consulado,
                        'cas': cuenta.cas,
                        'status': cuenta.status
                    }
                    for cuenta in cuentas
                ]
    def get_x_cuentas_activas(self, pais: str, limite: int, consulados: list):
        with self.session_scope() as session:
            cuentas = session.query(CuentasDB).filter(
                CuentasDB.status == 1, 
                CuentasDB.pais == pais,
                or_(
                    CuentasDB.consulado.in_(consulados),
                    CuentasDB.cas.in_(consulados)
                )
            ).limit(limite).all()
            
            if not cuentas:
                return None
            else:
                return [
                    {
                        'id': cuenta.id,
                        'email': cuenta.email,
                        'password': cuenta.password,
                        'pais': cuenta.pais,
                        'consulado': cuenta.consulado,
                        'cas': cuenta.cas,
                        'status': cuenta.status
                    }
                    for cuenta in cuentas
                ]
            
    def get_x_cuentas_activas_peru(self, pais: str, limite: int):
        with self.session_scope() as session:
            cuentas = session.query(CuentasDB).filter(
                CuentasDB.status == 1, 
                CuentasDB.pais == pais
            ).limit(limite).all()
            
            if not cuentas:
                return None
            else:
                return [
                    {
                        'id': cuenta.id,
                        'email': cuenta.email,
                        'password': cuenta.password,
                        'pais': cuenta.pais,
                        'consulado': cuenta.consulado,
                        'cas': cuenta.cas,
                        'status': cuenta.status
                    }
                    for cuenta in cuentas
                ]
            
    def get_cuentas_falsas_activas(self,pais: String):
        with self.session_scope() as session:
            cuentas = session.query(CuentaFalsaDB).filter(CuentaFalsaDB.status == 1, CuentaFalsaDB.pais == pais).all()
            if not cuentas:
                return None
            else:
                return [
                    {
                        'id': cuenta.id,
                        'email': cuenta.email,
                        'password': cuenta.password,
                        'pais': cuenta.pais,
                        'status': cuenta.status
                    }
                    for cuenta in cuentas
                ]
    def insert_cuenta(self, cuenta: CuentaSchema):
        with self.session_scope() as session:
            db_cuenta = CuentasDB(**cuenta.dict(exclude={'id'}))
            session.add(db_cuenta)
            session.flush()
            return db_cuenta
        
    def delete_cuenta(self, cuenta_id: int):
        with self.session_scope() as session:
            cuenta = session.query(CuentasDB).filter(CuentasDB.id == cuenta_id).first()
            if cuenta:
                session.delete(cuenta)
                session.commit()

    def update_cuenta(self, cuenta:CuentaSchema):
        with self.session_scope() as session:
            cuenta_db = session.query(CuentasDB).filter(CuentasDB.id == cuenta.id).first()
            if cuenta_db:
                for key, value in cuenta.dict(exclude={'id'}).items():
                    setattr(cuenta_db, key, value)
                session.commit()

    def delete_cuenta_falsa(self, cuenta_id: int):
        with self.session_scope() as session:
            cuenta = session.query(CuentaFalsaDB).filter(CuentaFalsaDB.id == cuenta_id).first()
            if cuenta:
                session.delete(cuenta)
                session.commit()

    def update_cuenta_falsa(self, cuenta: CuentaFalsaSchema):
        with self.session_scope() as session:
            cuenta_db = session.query(CuentaFalsaDB).filter(CuentaFalsaDB.id == cuenta.id).first()
            if cuenta_db:
                for key, value in cuenta.dict(exclude={'id'}).items():
                    setattr(cuenta_db, key, value)
                session.commit()      
    
    def get_cuentas_falsas(self):
        with self.session_scope() as session:
            cuentas_falsas = session.query(CuentaFalsaDB).filter(CuentaFalsaDB.status == 1).all()
            if not cuentas_falsas:
                return None
            else:
                return [
                    {
                        'id': cuenta.id,
                        'email': cuenta.email,
                        'password': cuenta.password,
                        'pais': cuenta.pais,
                        'status': cuenta.status
                    }
                    for cuenta in cuentas_falsas
                ]
    
    def get_cuenta_falsa(self,pais: str,cuentas:int):
        with self.session_scope() as session:
            result = session.query(CuentaFalsaDB).filter(CuentaFalsaDB.status == 1,CuentaFalsaDB.pais == pais).limit(cuentas).all()
            if not result:
                return None
            else:        
                return [ 
                    {
                        'id': cuenta_falsa.id,
                        'email': cuenta_falsa.email,
                        'password': cuenta_falsa.password,
                        'pais': cuenta_falsa.pais,
                        'status': cuenta_falsa.status
                    }
                    for cuenta_falsa in result
                ]
            
    def get_configuracion(self, id: int):
        with self.session_scope() as session:
            config = copy.deepcopy(session.query(ConfiguracionDB).filter(ConfiguracionDB.id == id).first())
            if not config:
                return None
            else:
                return {
                    'id' : config.id,
                    'pais' : config.pais,
                    'max_cuentas' : config.max_cuentas,
                    'time_refresh' : config.time_refresh
                }
            
    def get_configuracion_by_pais(self,pais:str):
        with self.session_scope() as session:
            config = copy.deepcopy(session.query(ConfiguracionDB).filter(ConfiguracionDB.pais == pais).first())
            if not config:
                return None
            else:
                return {
                    'id' : config.id,
                    'pais' : config.pais,
                    'max_cuentas' : config.max_cuentas,
                    'max_cuentas_scan' : config.max_cuentas_scan,
                    'time_refresh' : config.time_refresh,
                    'rango_busqueda': config.rango_busqueda,
                    'show_browser_scan' : config.show_browser_scan,
                    'show_browser_bot' : config.show_browser_bot,
                    'wait_scan' : config.wait_scan,
                    'wait_bot' : config.wait_bot,
                    'url' : config.url,
                    'port' : config.port
                }
            
    def update_configuracion(self, configuracion: ConfiguracionSchema):
        with self.session_scope() as session:
            # Buscar el registro existente por su ID
            existing_config = session.query(ConfiguracionDB).filter(ConfiguracionDB.id == configuracion.id).first()
            
            if existing_config:
                # Si el registro existe, actualizar sus campos
                for key, value in configuracion.dict(exclude={'id'}).items():
                    setattr(existing_config, key, value)
                session.commit()
                return {'title':'Configuración Guardada.', 'message':f'La configuración para {configuracion.pais} ha sido actualizada.'}
            else:
                return {'title':'Error al guardar la configuración.', 'message':'No se encontró la configuración que intentas actualizar.'}
    
    def insert_cuenta_falsa(self, cuenta: CuentaFalsaSchema):
        with self.session_scope() as session:
            db_cuenta = CuentaFalsaDB(**cuenta.dict(exclude={'id'}))
            session.add(db_cuenta)
            session.flush()
            return db_cuenta

    def close(self):
        Session.remove()