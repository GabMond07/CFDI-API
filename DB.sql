-- Create tables

CREATE TABLE Roles (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB
);

CREATE TABLE Tenant (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE "User" (
    rfc VARCHAR(13) PRIMARY KEY,
    hashed_password VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL,
    tenant_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    email VARCHAR(150),
    username VARCHAR(100),
    webhook_url VARCHAR(255),
    FOREIGN KEY (tenant_id) REFERENCES Tenant(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES Roles(id)
);

CREATE TABLE AuthToken (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    user_id VARCHAR(13) NOT NULL,
    tenant_id VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenant(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Issuer (
    rfc_issuer VARCHAR(13) PRIMARY KEY,
    name_issuer VARCHAR(150),
    tax_regime VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE Receiver (
    id SERIAL PRIMARY KEY,
    rfc_receiver VARCHAR(20) NOT NULL,
    name_receiver VARCHAR(150),
    cfdi_use VARCHAR(50),
    tax_regime VARCHAR(100),
    tax_address VARCHAR(255)
);

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
    total DOUBLE PRECISION NOT NULL,
    subtotal DOUBLE PRECISION NOT NULL,
    payment_method VARCHAR(50),
    payment_form VARCHAR(50),
    currency VARCHAR(10),
    user_id VARCHAR(13) NOT NULL,
    issuer_id VARCHAR(13) NOT NULL,
    receiver_id INTEGER,
    cfdi_use VARCHAR(50),
    export_status VARCHAR(20),
    FOREIGN KEY (issuer_id) REFERENCES Issuer(rfc_issuer),
    FOREIGN KEY (receiver_id) REFERENCES Receiver(id),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE
);

CREATE INDEX idx_cfdi_user_id ON CFDI(user_id);
CREATE INDEX idx_cfdi_issue_date ON CFDI(issue_date);
CREATE INDEX idx_cfdi_receiver_id ON CFDI(receiver_id);

CREATE TABLE Concept (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGINT NOT NULL,
    fiscal_key VARCHAR(50),
    description TEXT,
    quantity DOUBLE PRECISION NOT NULL,
    unit_value DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    discount DOUBLE PRECISION DEFAULT 0,
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE
);

CREATE INDEX idx_concept_cfdi_id ON Concept(cfdi_id);

CREATE TABLE Taxes (
    id BIGSERIAL PRIMARY KEY,
    concept_id BIGINT NOT NULL,
    tax_type VARCHAR(50) NOT NULL,
    rate DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    FOREIGN KEY (concept_id) REFERENCES Concept(id) ON DELETE CASCADE
);

CREATE INDEX idx_taxes_concept_id ON Taxes(concept_id);

CREATE TABLE CFDIRelation (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGINT NOT NULL,
    related_uuid VARCHAR(36) NOT NULL,
    relation_type VARCHAR(10) NOT NULL,
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE,
    UNIQUE (cfdi_id, related_uuid)
);

CREATE INDEX idx_cfdirelation_cfdi_id ON CFDIRelation(cfdi_id);

CREATE TABLE Report (
    id BIGSERIAL PRIMARY KEY,
    cfdi_id BIGINT,
    format VARCHAR(10) NOT NULL,
    file_content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    user_id VARCHAR(13) NOT NULL,
    name VARCHAR(255),
    description TEXT,
    filters JSONB,
    operation VARCHAR(255),
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE
);

CREATE INDEX idx_report_cfdi_id ON Report(cfdi_id);
CREATE INDEX idx_report_user_id ON Report(user_id);

CREATE TABLE Notification (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(13) NOT NULL,
    cfdi_id BIGINT,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE
);

CREATE INDEX idx_notification_user_id ON Notification(user_id);
CREATE INDEX idx_notification_cfdi_id ON Notification(cfdi_id);

CREATE TABLE AuditLog (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(13),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE
);

CREATE INDEX idx_auditlog_user_id ON AuditLog(user_id);
CREATE INDEX idx_auditlog_created_at ON AuditLog(created_at);

CREATE TABLE BatchJob (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(13) NOT NULL,
    status VARCHAR(20) NOT NULL,
    query JSONB,
    result_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE
);

CREATE INDEX idx_batchjob_user_id ON BatchJob(user_id);
CREATE INDEX idx_batchjob_created_at ON BatchJob(created_at);

CREATE TABLE PaymentComplement (
    Payment_ID SERIAL PRIMARY KEY,
    cfdi_id BIGINT NOT NULL,
    payment_date DATE NOT NULL,
    payment_form VARCHAR(50),
    payment_currency VARCHAR(10),
    payment_amount DOUBLE PRECISION,
    FOREIGN KEY (cfdi_id) REFERENCES CFDI(id) ON DELETE CASCADE
);

CREATE INDEX idx_paymentcomplement_cfdi_id ON PaymentComplement(cfdi_id);

CREATE TABLE ApiKey (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    active BOOLEAN DEFAULT TRUE,
    user_id VARCHAR(13) NOT NULL,
    tenant_id VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenant(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE RefreshToken (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    user_id VARCHAR(13) NOT NULL,
    tenant_id VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES "User"(rfc) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES Tenant(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Insert initial roles
INSERT INTO Roles (role, permissions) VALUES
('Contribuyente', '{"scopes": ["reports:generate", "write:cfdis", "join:execute"]}'::jsonb),
('Admin', '{"scopes": ["reports:generate", "write:cfdis"]}'::jsonb);