from prisma import Prisma

# Inicializar cliente Prisma como singleton
db = Prisma(auto_register=True)