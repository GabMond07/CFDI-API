-- Tabla Roles
CREATE TABLE "Roles" (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL UNIQUE
);

-- Tabla User
CREATE TABLE "User" (
    rfc VARCHAR(13) PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(150),
    hashed_password VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES "Roles"(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT rfc_valid CHECK (rfc ~ '^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$')
);

-- Tabla AuthToken
CREATE TABLE "AuthToken" (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(13) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla Issuer
CREATE TABLE "Issuer" (
    rfc_issuer VARCHAR(13) PRIMARY KEY,
    name_issuer VARCHAR(150),
    tax_regime VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla CFDI
CREATE TABLE "CFDI" (
    id BIGSERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    issue_date TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_method VARCHAR(50),
    currency VARCHAR(10),
    type VARCHAR(20) NOT NULL CHECK (type IN ('ingreso', 'egreso')),
    total DECIMAL(15, 2) NOT NULL,
    subtotal DECIMAL(15, 2) NOT NULL,
    user_id VARCHAR(13) NOT NULL,
    payment_form VARCHAR(50),
    issuer_id VARCHAR(13) NOT NULL,
    cfdi_use VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (issuer_id) REFERENCES "Issuer"(rfc_issuer) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla CFDIAttachment
CREATE TABLE "CFDIAttachment" (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGSERIAL NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('xml', 'pdf')),
    file_content BYTEA NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cfdi_id) REFERENCES "CFDI"(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla Concept
CREATE TABLE "Concept" (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGSERIAL NOT NULL,
    fiscal_key VARCHAR(50),
    description TEXT,
    quantity DECIMAL(15, 2) NOT NULL,
    unit_value DECIMAL(15, 2) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    discount DECIMAL(15, 2) DEFAULT 0,
    FOREIGN KEY (cfdi_id) REFERENCES "CFDI"(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT amount_check CHECK (amount = (quantity * unit_value) - discount)
);

-- Tabla Taxes
CREATE TABLE "Taxes" (
    id BIGSERIAL PRIMARY KEY,
    concept_id BIGSERIAL NOT NULL,
    tax_type VARCHAR(50) NOT NULL,
    rate DECIMAL(5, 2) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    FOREIGN KEY (concept_id) REFERENCES "Concept"(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Índices
CREATE INDEX idx_cfdi_user_id ON "CFDI" (user_id);
CREATE INDEX idx_cfdi_issue_date ON "CFDI" (issue_date);
CREATE INDEX idx_concept_cfdi_id ON "Concept" (cfdi_id);
CREATE INDEX idx_taxes_concept_id ON "Taxes" (concept_id);