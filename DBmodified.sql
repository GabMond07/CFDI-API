-- \c web_api_fiscal;

-- Crear tabla Roles
CREATE TABLE "Roles" (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL UNIQUE,
    CONSTRAINT role_not_empty CHECK (role <> '')
);

-- Crear tabla User
CREATE TABLE "User" (
    rfc VARCHAR(13) PRIMARY KEY,
    hashed_password VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES "Roles"(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT rfc_valid CHECK (rfc ~ '^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$'),
    CONSTRAINT hashed_password_not_empty CHECK (hashed_password <> '')
);

-- Crear tabla AuthToken
CREATE TABLE "AuthToken" (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(13) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT expires_at_future CHECK (expires_at > CURRENT_TIMESTAMP)
);

-- Crear tabla CFDI
CREATE TABLE "CFDI" (
    id BIGSERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    issuer_rfc VARCHAR(13) NOT NULL,
    receiver_rfc VARCHAR(13) NOT NULL,
    issue_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('emitido', 'cancelado')),
    type VARCHAR(20) NOT NULL CHECK (type IN ('ingreso', 'egreso')),
    total DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receiver_rfc) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT issue_date_not_future CHECK (issue_date <= CURRENT_TIMESTAMP)
);

-- Crear tabla CFDIAttachment
CREATE TABLE "CFDIAttachment" (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGSERIAL NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('xml', 'pdf')),
    file_content BYTEA NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cfdi_id) REFERENCES "CFDI"(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Crear tabla CFDICancellationRequest
CREATE TABLE "CFDICancellationRequest" (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGSERIAL NOT NULL,
    request_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pendiente', 'aprobado', 'rechazado')),
    reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cfdi_id) REFERENCES "CFDI"(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Crear tabla CFDIInvoice
CREATE TABLE "CFDIInvoice" (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGSERIAL NOT NULL,
    concept VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(15, 2) NOT NULL,
    tax DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cfdi_id) REFERENCES "CFDI"(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Crear tabla Report
CREATE TABLE "Report" (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(13) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Crear tabla Visualization
CREATE TABLE "Visualization" (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(13) NOT NULL,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Crear índices para optimizar consultas
CREATE INDEX idx_cfdi_receiver_rfc ON "CFDI" (receiver_rfc);
CREATE INDEX idx_cfdi_issue_date ON "CFDI" (issue_date);
CREATE INDEX idx_cfdiattachment_cfdi_id ON "CFDIAttachment" (cfdi_id);
CREATE INDEX idx_cfdi_cancellationrequest_cfdi_id ON "CFDICancellationRequest" (cfdi_id);
CREATE INDEX idx_cfdi_invoice_cfdi_id ON "CFDIInvoice" (cfdi_id);
CREATE INDEX idx_report_user_id ON "Report" (user_id);
CREATE INDEX idx_visualization_user_id ON "Visualization" (user_id);

-- Insertar datos iniciales para Roles (ejemplo)
INSERT INTO "Roles" (role) VALUES
('contribuyente'),
('admin');