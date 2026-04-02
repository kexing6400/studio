#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';

const program = new Command();

program
  .name('{{PROJECT_NAME}}')
  .description('A production-ready CLI tool')
  .version('1.0.0');

program
  .command('hello')
  .description('Say hello')
  .argument('[name]', 'Name to greet', 'World')
  .action((name: string) => {
    console.log(chalk.green(`Hello, ${name}!`));
  });

program.parse();
