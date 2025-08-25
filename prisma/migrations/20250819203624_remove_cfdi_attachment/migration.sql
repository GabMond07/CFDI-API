/*
  Warnings:

  - You are about to drop the `CFDIAttachment` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `Visualization` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "CFDIAttachment" DROP CONSTRAINT "CFDIAttachment_cfdi_id_fkey";

-- DropForeignKey
ALTER TABLE "Visualization" DROP CONSTRAINT "Visualization_cfdi_id_fkey";

-- DropForeignKey
ALTER TABLE "Visualization" DROP CONSTRAINT "Visualization_user_id_fkey";

-- AlterTable
ALTER TABLE "AuthToken" ADD COLUMN     "tenant_id" VARCHAR(50),
ALTER COLUMN "token" SET DATA TYPE VARCHAR(512);

-- AlterTable
ALTER TABLE "Report" ADD COLUMN     "description" TEXT,
ADD COLUMN     "filters" JSONB,
ADD COLUMN     "name" TEXT,
ADD COLUMN     "operation" TEXT,
ALTER COLUMN "cfdi_id" DROP NOT NULL;

-- AlterTable
ALTER TABLE "User" ADD COLUMN     "tenant_id" VARCHAR(50);

-- DropTable
DROP TABLE "CFDIAttachment";

-- DropTable
DROP TABLE "Visualization";

-- CreateTable
CREATE TABLE "Tenant" (
    "id" VARCHAR(50) NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Tenant_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ApiKey" (
    "id" BIGSERIAL NOT NULL,
    "key" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMPTZ,
    "revoked_at" TIMESTAMPTZ,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "user_id" VARCHAR(13) NOT NULL,
    "tenant_id" VARCHAR(50),

    CONSTRAINT "ApiKey_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RefreshToken" (
    "id" BIGSERIAL NOT NULL,
    "token" VARCHAR(512) NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "revoked_at" TIMESTAMPTZ,
    "user_id" VARCHAR(13) NOT NULL,
    "tenant_id" VARCHAR(50),

    CONSTRAINT "RefreshToken_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ApiKey_key_key" ON "ApiKey"("key");

-- CreateIndex
CREATE UNIQUE INDEX "RefreshToken_token_key" ON "RefreshToken"("token");

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "Tenant"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuthToken" ADD CONSTRAINT "AuthToken_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "Tenant"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ApiKey" ADD CONSTRAINT "ApiKey_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ApiKey" ADD CONSTRAINT "ApiKey_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "Tenant"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RefreshToken" ADD CONSTRAINT "RefreshToken_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("rfc") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RefreshToken" ADD CONSTRAINT "RefreshToken_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "Tenant"("id") ON DELETE CASCADE ON UPDATE CASCADE;
