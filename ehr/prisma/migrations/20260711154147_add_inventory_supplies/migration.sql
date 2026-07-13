-- CreateTable
CREATE TABLE "inventory_supplies" (
    "supply_id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "quantity" INTEGER NOT NULL,
    "unit" TEXT NOT NULL,
    "reorder_level" INTEGER NOT NULL DEFAULT 10,
    "unit_cost" DECIMAL(65,30),
    "expiry_date" TIMESTAMP(3),
    "batch_number" TEXT,
    "manufacturer" TEXT,
    "notes" TEXT,
    "is_active" TEXT NOT NULL DEFAULT 'Y',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "inventory_supplies_pkey" PRIMARY KEY ("supply_id")
);
