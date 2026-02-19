import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

const prisma = new PrismaClient();

async function main() {
    console.log('🚀 Initializing database...');

    try {
        // 1. Push Schema (creates tables/columns)
        console.log('Running prisma db push...');
        try {
            execSync('npx prisma db push --accept-data-loss', { stdio: 'inherit' });
            console.log('✅ Schema pushed successfully.');
        } catch (err) {
            console.error('❌ Failed to push schema.');
            throw err;
        }

        // 2. Apply Triggers
        const triggersPath = path.join(process.cwd(), 'prisma', 'triggers.sql');
        if (fs.existsSync(triggersPath)) {
            console.log(`Applying triggers from: ${triggersPath}`);
            const sqlContent = fs.readFileSync(triggersPath, 'utf-8');

            // Split the SQL file into executable chunks.
            // 1. The Function Definition (ends with "$$ LANGUAGE plpgsql;")
            const functionEndMarker = '$$ LANGUAGE plpgsql;';
            const functionEndIndex = sqlContent.indexOf(functionEndMarker);

            if (functionEndIndex !== -1) {
                const createFunctionSql = sqlContent.substring(0, functionEndIndex + functionEndMarker.length);
                console.log('Executing Create Function...');
                await prisma.$executeRawUnsafe(createFunctionSql);

                // 2. The remaining commands (Drop Trigger, Create Trigger)
                const remainingSql = sqlContent.substring(functionEndIndex + functionEndMarker.length);
                const commands = remainingSql
                    .split(';')
                    .map(cmd => cmd.trim())
                    .filter(cmd => cmd.length > 0);

                for (const cmd of commands) {
                    console.log(`Executing command: ${cmd.substring(0, 50).replace(/\n/g, ' ')}...`);
                    await prisma.$executeRawUnsafe(cmd);
                }
            } else {
                // Fallback: If marker not found, try executing as a single block (which might fail if multiple commands)
                console.warn('⚠️ Could not find function end marker. Attempting to execute full file...');
                await prisma.$executeRawUnsafe(sqlContent);
            }

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
