# ============================================

# ENTORNOS VIRTUALES

# ============================================

.venv/
venv/
ENV/
env/
\*.egg-info/

# ============================================

# ARCHIVOS DE CONFIGURACIÓN SENSIBLES

# ============================================

.env
.env.\*
\*.env

# ============================================

# DATOS (CONTROL FINO)

# ============================================

# Ignorar todo data por defecto

data/\*

# PERMITIR storage (datos de dominio)

!data/storage/
!data/storage/\*\*

# Ignorar datos regenerables

data/raw/
data/processed/
data/cache/

# NO ignorar JSON de storage

!data/storage/\*.json

# ============================================

# ARCHIVOS DE DATOS GENÉRICOS (FUERA DE STORAGE)

# ============================================

_.csv
_.xlsx
_.xls
_.parquet
\*.feather

# ============================================

# CACHE Y TEMPORALES

# ============================================

**pycache**/
_.pyc
_.pyo
\*.pyd
.cache/
.ipynb_checkpoints/

# ============================================

# STREAMLIT

# ============================================

.streamlit

# ============================================

# CONFIGURACIÓN DE EDITORES

# ============================================

.vscode/
.idea/
\*.iml

# ============================================

# BUILD / DIST

# ============================================

dist/
build/
\*.spec

# ============================================

# SISTEMA

# ============================================

.DS_Store
Thumbs.db
_.bak
_.old
