#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { oraPromise } from 'ora';
import { readFileSync, writeFileSync, mkdirSync, existsSync, cpSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const program = new Command();

program
  .name('studio')
  .description('Studio CLI - Create production-ready TypeScript projects')
  .version('0.1.0');

program
  .command('new')
  .description('Create a new production-ready project')
  .argument('<name>', 'Project name')
  .option('-t, --template <type>', 'Project template', 'api')
  .action(async (name: string, options: { template: string }) => {
    console.log(chalk.blue(`\n🚀 Creating ${name} with Studio...\n`));

    const templateDir = join(__dirname, '..', 'templates', options.template);
    
    if (!existsSync(templateDir)) {
      console.error(chalk.red(`Template '${options.template}' not found`));
      console.log(chalk.yellow('\nAvailable templates:'));
      console.log('  api       - Express.js REST API (default)');
      console.log('  fullstack - Next.js + Express');
      console.log('  cli       - Node.js CLI tool');
      process.exit(1);
    }

    const targetDir = join(process.cwd(), name);
    
    if (existsSync(targetDir)) {
      console.error(chalk.red(`Directory '${name}' already exists`));
      process.exit(1);
    }

    try {
      // Copy template
      await oraPromise(
        Promise.resolve(cpSync(templateDir, targetDir, { recursive: true })),
        { text: 'Copying template...', successText: 'Template copied' }
      );

      // Update package.json name
      const pkgPath = join(targetDir, 'package.json');
      if (existsSync(pkgPath)) {
        const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
        pkg.name = name;
        writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
      }

      console.log(chalk.green('\n✅ Project created successfully!\n'));
      console.log(chalk.bold('Next steps:'));
      console.log(`  ${chalk.cyan('cd ' + name)}`);
      console.log(`  ${chalk.cyan('npm install')}`);
      console.log(`  ${chalk.cyan('npm run dev')}`);
      console.log();
    } catch (error) {
      console.error(chalk.red('Failed to create project:', error));
      process.exit(1);
    }
  });

program
  .command('list')
  .description('List available project templates')
  .action(() => {
    console.log(chalk.bold('\n📦 Available templates:\n'));
    console.log('  api       - Express.js REST API with TypeScript, Prisma, JWT');
    console.log('  fullstack - Next.js 14 + Express API');
    console.log('  cli       - Node.js CLI tool with Commander');
    console.log();
    console.log(chalk.dim('Usage: studio new <name> --template <type>\n'));
  });

program
  .command('info')
  .description('Show system information')
  .action(() => {
    console.log(chalk.bold('\n📊 Studio System Info\n'));
    console.log(`  Version:    ${chalk.cyan('0.1.0')}`);
    console.log(`  Node.js:    ${chalk.cyan(process.version)}`);
    console.log(`  Platform:   ${chalk.cyan(process.platform)}`);
    console.log(`  Architecture: ${chalk.cyan(process.arch)}`);
    console.log();
  });

program.parse();
