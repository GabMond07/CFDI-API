/*
  Warnings:

  - You are about to alter the column `token` on the `AuthToken` table. The data in that column could be lost. The data in that column will be cast from `Text` to `VarChar(255)`.
  - You are about to alter the column `user_id` on the `AuthToken` table. The data in that column could be lost. The data in that column will be cast from `Text` to `VarChar(13)`.
  - You are about to alter the column `role` on the `Roles` table. The data in that column could be lost. The data in that column will be cast from `Text` to `VarChar(50)`.
  - The primary key for the `User` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - You are about to alter the column `rfc` on the `User` table. The data in that column could be lost. The data in that column will be cast from `Text` to `VarChar(13)`.
  - You are about to alter the column `hashed_password` on the `User` table. The data in that column could be lost. The data in that column will be cast from `Text` to `VarChar(255)`.

*/
-- DropForeignKey
ALTER TABLE "AuthToken" DROP CONSTRAINT "AuthToken_user_id_fkey";

-- AlterTable
ALTER TABLE "AuthToken" ALTER COLUMN "token" SET DATA TYPE VARCHAR(255),
ALTER COLUMN "expires_at" SET DATA TYPE TIMESTAMPTZ,
ALTER COLUMN "created_at" SET DATA TYPE TIMESTAMPTZ,
ALTER COLUMN "user_id" SET DATA TYPE VARCHAR(13);

-- AlterTable
ALTER TABLE "Roles" ADD COLUMN     "permissions" JSONB,
ALTER COLUMN "role" SET DATA TYPE VARCHAR(50);

-- AlterTable
ALTER TABLE "User" DROP CONSTRAINT "User_pkey",
ADD COLUMN     "email" VARCHAR(150),
ADD COLUMN     "username" VARCHAR(100),
ALTER COLUMN "rfc" SET DATA TYPE VARCHAR(13),
ALTER COLUMN "hashed_password" SET DATA TYPE VARCHAR(255),
ALTER COLUMN "created_at" SET DATA TYPE TIMESTAMPTZ,
ADD CONSTRAINT "User_pkey" PRIMARY KEY ("rfc");

-- CreateTable
CREATE TABLE "Issuer" (
    "rfc_issuer" VARCHAR(13) NOT NULL,
    "name_issuer" VARCHAR(150),
    "tax_regime" VARCHAR(100),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Issuer_pkey" PRIMARY KEY ("rfc_issuer")
);

-- CreateTable
CREATE TABLE "CFDI" (
    "id" BIGSERIAL NOT NULL,
    "uuid" VARCHAR(36) NOT NULL,
    "version" VARCHAR(10) NOT NULL DEFAULT '4.0',
    "serie" VARCHAR(25),
    "folio" VARCHAR(25),
    "issue_date" TIMESTAMPTZ NOT NULL,
    "seal" TEXT,
    "certificate_number" VARCHAR(20),
    "certificate" TEXT,
    "place_of_issue" VARCHAR(100),
    "type" VARCHAR(20) NOT NULL,
    "total" DOUBLE PRECISION NOT NULL,
    "subtotal" DOUBLE PRECISION NOT NULL,
    "payment_method" VARCHAR(50),
    "payment_form" VARCHAR(50),
    "currency" VARCHAR(10),
    "user_id" VARCHAR(13) NOT NULL,
    "issuer_id" VARCHAR(13) NOT NULL,
    "receiver_id" INTEGER,
    "cfdi_use" VARCHAR(50),
    "export_status" VARCHAR(20),

    CONSTRAINT "CFDI_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CFDIAttachment" (
    "id" BIGSERIAL NOT NULL,
    "cfdi_id" BIGINT NOT NULL,
    "file_type" VARCHAR(10) NOT NULL,
    "file_content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "CFDIAttachment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Concept" (
    "id" BIGSERIAL NOT NULL,
    "cfdi_id" BIGINT NOT NULL,
    "fiscal_key" VARCHAR(50),
    "description" TEXT,
    "quantity" DOUBLE PRECISION NOT NULL,
    "unit_value" DOUBLE PRECISION NOT NULL,
    "amount" DOUBLE PRECISION NOT NULL,
    "discount" DOUBLE PRECISION NOT NULL DEFAULT 0,

    CONSTRAINT "Concept_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Taxes" (
    "id" BIGSERIAL NOT NULL,
    "concept_id" BIGINT NOT NULL,
    "tax_type" VARCHAR(50) NOT NULL,
    "rate" DOUBLE PRECISION NOT NULL,
    "amount" DOUBLE PRECISION NOT NULL,

    CONSTRAINT "Taxes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CFDIRelation" (
    "id" BIGSERIAL NOT NULL,
    "cfdi_id" BIGINT NOT NULL,
    "related_uuid" VARCHAR(36) NOT NULL,
    "relation_type" VARCHAR(10) NOT NULL,

    CONSTRAINT "CFDIRelation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Report" (
    "id" BIGSERIAL NOT NULL,
    "cfdi_id" BIGINT NOT NULL,
    "format" VARCHAR(10) NOT NULL,
    "file_content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" VARCHAR(13) NOT NULL,

    CONSTRAINT "Report_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Visualization" (
    "id" BIGSERIAL NOT NULL,
    "user_id" VARCHAR(13) NOT NULL,
    "cfdi_id" BIGINT,
    "type" VARCHAR(20) NOT NULL,
    "config" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Visualization_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Notification" (
    "id" BIGSERIAL NOT NULL,
    "user_id" VARCHAR(13) NOT NULL,
    "cfdi_id" BIGINT,
    "type" VARCHAR(50) NOT NULL,
    "status" VARCHAR(20) NOT NULL,
    "payload" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sent_at" TIMESTAMP(3),

    CONSTRAINT "Notification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditLog" (
    "id" BIGSERIAL NOT NULL,
    "user_id" VARCHAR(13),
    "action" VARCHAR(100) NOT NULL,
    "details" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BatchJob" (
    "id" BIGSERIAL NOT NULL,
    "user_id" VARCHAR(13) NOT NULL,
    "status" VARCHAR(20) NOT NULL,
    "query" JSONB,
    "result_count" INTEGER NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "BatchJob_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Receiver" (
    "id" SERIAL NOT NULL,
    "rfc_receiver" VARCHAR(20) NOT NULL,
    "name_receiver" VARCHAR(150),
    "cfdi_use" VARCHAR(50),
    "tax_regime" VARCHAR(100),
    "tax_address" VARCHAR(255),

    CONSTRAINT "Receiver_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PaymentComplement" (
    "Payment_ID" SERIAL NOT NULL,
    "cfdi_id" BIGINT NOT NULL,
    "payment_date" DATE NOT NULL,
    "payment_form" VARCHAR(50),
    "payment_currency" VARCHAR(10),
    "payment_amount" DOUBLE PRECISION,

    CONSTRAINT "PaymentComplement_pkey" PRIMARY KEY ("Payment_ID")
);

-- CreateIndex
CREATE UNIQUE INDEX "CFDI_uuid_key" ON "CFDI"("uuid");

-- CreateIndex
CREATE INDEX "CFDI_user_id_idx" ON "CFDI"("user_id");

-- CreateIndex
CREATE INDEX "CFDI_issue_date_idx" ON "CFDI"("issue_date");

-- CreateIndex
CREATE INDEX "CFDI_receiver_id_idx" ON "CFDI"("receiver_id");

-- CreateIndex
CREATE INDEX "CFDIAttachment_cfdi_id_idx" ON "CFDIAttachment"("cfdi_id");

-- CreateIndex
CREATE INDEX "Concept_cfdi_id_idx" ON "Concept"("cfdi_id");

-- CreateIndex
CREATE INDEX "Taxes_concept_id_idx" ON "Taxes"("concept_id");

-- CreateIndex
CREATE INDEX "CFDIRelation_cfdi_id_idx" ON "CFDIRelation"("cfdi_id");

-- CreateIndex
CREATE UNIQUE INDEX "CFDIRelation_cfdi_id_related_uuid_key" ON "CFDIRelation"("cfdi_id", "related_uuid");

-- CreateIndex
CREATE INDEX "Report_cfdi_id_idx" ON "Report"("cfdi_id");

-- CreateIndex
CREATE INDEX "Report_user_id_idx" ON "Report"("user_id");

-- CreateIndex
CREATE INDEX "Visualization_user_id_idx" ON "Visualization"("user_id");

-- CreateIndex
CREATE INDEX "Visualization_cfdi_id_idx" ON "Visualization"("cfdi_id");

-- CreateIndex
CREATE INDEX "Notification_user_id_idx" ON "Notification"("user_id");

-- CreateIndex
CREATE INDEX "Notification_cfdi_id_idx" ON "Notification"("cfdi_id");

-- CreateIndex
CREATE INDEX "AuditLog_user_id_idx" ON "AuditLog"("user_id");

-- CreateIndex
CREATE INDEX "AuditLog_created_at_idx" ON "AuditLog"("created_at");

-- CreateIndex
CREATE INDEX "BatchJob_user_id_idx" ON "BatchJob"("user_id");

-- CreateIndex
CREATE INDEX "BatchJob_created_at_idx" ON "BatchJob"("created_at");

-- CreateIndex
CREATE INDEX "PaymentComplement_cfdi_id_idx" ON "PaymentComplement"("cfdi_id");

-- AddForeignKey
ALTER TABLE "AuthToken" ADD CONSTRAINT "AuthToken_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CFDI" ADD CONSTRAINT "CFDI_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CFDI" ADD CONSTRAINT "CFDI_issuer_id_fkey" FOREIGN KEY ("issuer_id") REFERENCES "Issuer"("rfc_issuer") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CFDI" ADD CONSTRAINT "CFDI_receiver_id_fkey" FOREIGN KEY ("receiver_id") REFERENCES "Receiver"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CFDIAttachment" ADD CONSTRAINT "CFDIAttachment_cfdi_id_fkey" FOREIGN KEY ("cfdi_id") REFERENCES "CFDI"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Concept" ADD CONSTRAINT "Concept_cfdi_id_fkey" FOREIGN KEY ("cfdi_id") REFERENCES "CFDI"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Taxes" ADD CONSTRAINT "Taxes_concept_id_fkey" FOREIGN KEY ("concept_id") REFERENCES "Concept"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CFDIRelation" ADD CONSTRAINT "CFDIRelation_cfdi_id_fkey" FOREIGN KEY ("cfdi_id") REFERENCES "CFDI"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Report" ADD CONSTRAINT "Report_cfdi_id_fkey" FOREIGN KEY ("cfdi_id") REFERENCES "CFDI"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Report" ADD CONSTRAINT "Report_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Visualization" ADD CONSTRAINT "Visualization_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Visualization" ADD CONSTRAINT "Visualization_cfdi_id_fkey" FOREIGN KEY ("cfdi_id") REFERENCES "CFDI"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Notification" ADD CONSTRAINT "Notification_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Notification" ADD CONSTRAINT "Notification_cfdi_id_fkey" FOREIGN KEY ("cfdi_id") REFERENCES "CFDI"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditLog" ADD CONSTRAINT "AuditLog_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BatchJob" ADD CONSTRAINT "BatchJob_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PaymentComplement" ADD CONSTRAINT "PaymentComplement_cfdi_id_fkey" FOREIGN KEY ("cfdi_id") REFERENCES "CFDI"("id") ON DELETE CASCADE ON UPDATE CASCADE;
