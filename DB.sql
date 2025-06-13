-- Tabla de roles
CREATE TABLE Roles (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) UNIQUE NOT NULL
);

-- Tabla de usuarios
CREATE TABLE "User" (
    rfc VARCHAR(13) PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(150),
    hashed_password VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (role_id) REFERENCES Roles(id)
);

-- Tabla de tokens de autenticación
CREATE TABLE AuthToken (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    user_id VARCHAR(13) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla de emisores
CREATE TABLE Issuer (
    rfc_issuer VARCHAR(13) PRIMARY KEY,
    name_issuer VARCHAR(150),
    tax_regime VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla principal de CFDI
CREATE TABLE CFDI (
    id BIGSERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    version VARCHAR(10) DEFAULT '4.0' NOT NULL,
    serie VARCHAR(25),
    folio VARCHAR(25),
    issue_date TIMESTAMPTZ NOT NULL,
    seal TEXT,
    certificate_number VARCHAR(20),
    certificate TEXT,
    place_of_issue VARCHAR(100),
    type VARCHAR(20) NOT NULL,
    total FLOAT NOT NULL,
    subtotal FLOAT NOT NULL,
    payment_method VARCHAR(50),
    payment_form VARCHAR(50),
    currency VARCHAR(10),
    user_id VARCHAR(13) NOT NULL,
    issuer_id VARCHAR(13) NOT NULL,
    cfdi_use VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (issuer_id) REFERENCES Issuer(rfc_issuer) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla de archivos adjuntos del CFDI
CREATE TABLE CFDIAttachment (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGINT NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla de conceptos
CREATE TABLE Concept (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGINT NOT NULL,
    fiscal_key VARCHAR(50),
    description TEXT,
    quantity FLOAT NOT NULL,
    unit_value FLOAT NOT NULL,
    amount FLOAT NOT NULL,
    discount FLOAT DEFAULT 0 NOT NULL,
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla de impuestos
CREATE TABLE Taxes (
    id BIGSERIAL PRIMARY KEY,
    concept_id BIGINT NOT NULL,
    tax_type VARCHAR(50) NOT NULL,
    rate FLOAT NOT NULL,
    amount FLOAT NOT NULL,
    FOREIGN KEY (concept_id) REFERENCES Concept(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla de relaciones entre CFDIs
CREATE TABLE CFDIRelation (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGINT NOT NULL,
    related_uuid VARCHAR(36) NOT NULL,
    relation_type VARCHAR(10) NOT NULL,
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE (cfdi_id, related_uuid)
);

-- Índices para optimizar consultas
CREATE INDEX idx_user_role_id ON "User"(role_id);
CREATE INDEX idx_cfdi_user_id ON CFDI(user_id);
CREATE INDEX idx_cfdi_issue_date ON CFDI(issue_date);
CREATE INDEX idx_cfdi_attachment_cfdi_id ON CFDIAttachment(cfdi_id);
CREATE INDEX idx_concept_cfdi_id ON Concept(cfdi_id);
CREATE INDEX idx_taxes_concept_id ON Taxes(concept_id);
CREATE INDEX idx_cfdi_relation_cfdi_id ON CFDIRelation(cfdi_id);