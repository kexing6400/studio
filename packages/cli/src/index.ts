#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { readFileSync, writeFileSync, existsSync, cpSync, mkdirSync } from 'fs';
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
  .option('-t, --template <type>', 'Project template (api, fullstack, cli)', 'api')
  .action(async (name: string, options: { template: string }) => {
    console.log(chalk.blue(`\n🚀 Creating ${name} with Studio...\n`));

    const templateDir = join(__dirname, '..', 'templates', options.template);
    
    if (!existsSync(templateDir)) {
      console.error(chalk.red(`\n❌ Template '${options.template}' not found\n`));
      console.log(chalk.yellow('Available templates:'));
      console.log('  api       - Express.js REST API (default)');
      console.log('  fullstack - Next.js + Express');
      console.log('  cli       - Node.js CLI tool\n');
      process.exit(1);
    }

    const targetDir = join(process.cwd(), name);
    
    if (existsSync(targetDir)) {
      console.error(chalk.red(`\n❌ Directory '${name}' already exists\n`));
      process.exit(1);
    }

    try {
      console.log(chalk.dim('📦 Copying template...'));
      cpSync(templateDir, targetDir, { recursive: true });

      // Update package.json name
      const pkgPath = join(targetDir, 'package.json');
      if (existsSync(pkgPath)) {
        const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
        pkg.name = name;
        writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
        
        // Update README project name
        const readmePath = join(targetDir, 'README.md');
        if (existsSync(readmePath)) {
          let readme = readFileSync(readmePath, 'utf-8');
          readme = readme.replace(/\{\{PROJECT_NAME\}\}/g, name);
          writeFileSync(readmePath, readme);
        }
        
        // Update CLI template bin name
        if (options.template === 'cli') {
          const srcIndexPath = join(targetDir, 'src', 'index.ts');
          if (existsSync(srcIndexPath)) {
            let content = readFileSync(srcIndexPath, 'utf-8');
            content = content.replace(/\{\{PROJECT_NAME\}\}/g, name);
            writeFileSync(srcIndexPath, content);
          }
        }
      }

      console.log(chalk.green('✅ Project created successfully!\n'));
      console.log(chalk.bold('Next steps:'));
      console.log(`  ${chalk.cyan('cd ' + name)}`);
      console.log(`  ${chalk.cyan('npm install')}`);
      console.log(`  ${chalk.cyan('npm run dev')}`);
      console.log();
    } catch (error) {
      console.error(chalk.red('\n❌ Failed to create project:', error));
      process.exit(1);
    }
  });

program
  .command('list')
  .description('List available project templates')
  .action(() => {
    console.log(chalk.bold('\n📦 Available templates:\n'));
    console.log(`  ${chalk.green('api')}       - Express.js REST API with TypeScript, Prisma, JWT`);
    console.log(`  ${chalk.green('fullstack')} - Next.js 14 + Express API`);
    console.log(`  ${chalk.green('cli')}       - Node.js CLI tool with Commander`);
    console.log();
    console.log(chalk.dim('Usage: studio new <name> --template <type>\n'));
  });

program
  .command('info')
  .description('Show system information')
  .action(() => {
    console.log(chalk.bold('\n📊 Studio System Info\n'));
    console.log(`  Version:     ${chalk.cyan('0.1.0')}`);
    console.log(`  Node.js:     ${chalk.cyan(process.version)}`);
    console.log(`  Platform:    ${chalk.cyan(process.platform)}`);
    console.log(`  Architecture: ${chalk.cyan(process.arch)}`);
    console.log();
  });

program.parse();
