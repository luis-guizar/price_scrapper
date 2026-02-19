
import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

const prisma = new PrismaClient();

async function main() {
    console.log('🚀 Initializing database...');

    try {
        // 1. Push Schema (creates tables/columns)
        // This syncs the database with schema.prisma
        console.log('Running prisma db push...');
        try {
            execSync('npx prisma db push --accept-data-loss', { stdio: 'inherit' });
            console.log('✅ Schema pushed successfully.');
        } catch (err) {
            console.error('❌ Failed to push schema (creating tables/columns).');
            throw err;
        }

        // 2. Apply Triggers
        const triggersPath = path.join(process.cwd(), 'prisma', 'triggers.sql');
        if (fs.existsSync(triggersPath)) {
            console.log(`Applying triggers from: ${triggersPath}`);
            const sql = fs.readFileSync(triggersPath, 'utf-8');

            // Execute the raw SQL. 
            // Note: If the file contains multiple statements that cannot be executed in one go, 
            // specific handling might be needed, but usually this works for Postgres functions/triggers.
            await prisma.$executeRawUnsafe(sql);
            console.log('✅ Triggers applied successfully.');
        } else {
            console.warn(`⚠️ Triggers file not found at ${triggersPath}`);
        }

    } catch (error) {
        console.error('❌ Error during database initialization:', error);
        process.exit(1);
    } finally {
        await prisma.$disconnect();
    }
}

main();
