#!/usr/bin/env node

const { program } = require('commander');
const inquirer = require('inquirer');
const fs = require('fs');
const path = require('path');
const chalk = require('chalk');
const config = require('../lib/config');
const api = require('../lib/api');
const ui = require('../lib/ui');

program
    .version('2.0.0')
    .description('Namango CLI — AI Gateway Platform from your terminal');

// ─── LOGIN ────────────────────────────────────────────────────────────────────

program
    .command('login')
    .description('Authenticate with the Namango Gateway')
    .option('--key <apiKey>', 'Pass API key directly')
    .action(async (options) => {
        ui.banner();
        let apiKey = options.key;
        if (!apiKey) {
            const answers = await inquirer.prompt([{
                type: 'password',
                name: 'apiKey',
                message: 'Enter your Namango API Key:',
                mask: '*',
                validate: input => input.length > 5 ? true : 'Key too short',
            }]);
            apiKey = answers.apiKey;
        }

        const spin = ui.spinner('Verifying credentials...');
        try {
            await api.health();
            config.save({ apiKey });
            spin.succeed(ui.SUCCESS('Authenticated successfully'));
            console.log(ui.DIM('    Key stored at: ~/.namango/config.json\n'));
        } catch (e) {
            spin.fail(ui.ERR('Could not reach platform: ' + e.message));
        }
    });

// ─── WHOAMI ───────────────────────────────────────────────────────────────────

program
    .command('whoami')
    .description('Show current authentication status')
    .action(() => {
        const cfg = config.get();
        if (cfg.apiKey) {
            console.log(ui.SUCCESS('\n  Logged in'));
            console.log(ui.DIM(`  Key: ${cfg.apiKey.slice(0, 8)}${'*'.repeat(20)}`));
            console.log(ui.DIM(`  Platform: ${api.BASE_URL}\n`));
        } else {
            console.log(ui.WARN('\n  Not logged in. Run: namango login\n'));
        }
    });

// ─── STATUS ───────────────────────────────────────────────────────────────────

program
    .command('status')
    .description('Check platform health and connectivity')
    .action(async () => {
        const spin = ui.spinner('Pinging platform...');
        try {
            const data = await api.health();
            spin.succeed(ui.SUCCESS('Platform online'));
            ui.keyValue('App', data.app);
            ui.keyValue('Version', data.version);
            ui.keyValue('Status', data.status);
            ui.keyValue('Endpoint', api.BASE_URL);
            console.log('');
        } catch (e) {
            spin.fail(ui.ERR('Platform unreachable: ' + e.message));
        }
    });

// ─── AGENTS ───────────────────────────────────────────────────────────────────

program
    .command('agents')
    .description('Browse all available AI agents from the marketplace')
    .option('--json', 'Output raw JSON')
    .action(async (options) => {
        config.requireAuth();
        const spin = ui.spinner('Fetching agents from marketplace...');
        try {
            const data = await api.agents();
            spin.stop();

            if (options.json) {
                console.log(JSON.stringify(data.agents, null, 2));
                return;
            }

            ui.sectionHeader(`Agents (${data.total})`);
            ui.table(
                ['Icon', 'Name', 'Category', 'Preferred LLM', 'Type'],
                data.agents.map(a => [
                    a.icon,
                    chalk.white(a.name),
                    ui.ACCENT(a.category),
                    ui.DIM(a.preferred_llm.split('-').slice(0, 2).join('-')),
                    a.is_builtin ? ui.SUCCESS('Built-in') : ui.WARN('Community'),
                ])
            );
            console.log(ui.DIM(`  ${data.agents.filter(a => a.is_builtin).length} built-in, ${data.agents.filter(a => !a.is_builtin).length} community\n`));
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── TOOLS ────────────────────────────────────────────────────────────────────

program
    .command('tools')
    .description('Browse all available tools and MCP integrations')
    .option('--json', 'Output raw JSON')
    .action(async (options) => {
        config.requireAuth();
        const spin = ui.spinner('Fetching tools from marketplace...');
        try {
            const data = await api.tools();
            spin.stop();

            if (options.json) {
                console.log(JSON.stringify(data.tools, null, 2));
                return;
            }

            ui.sectionHeader(`Tools & MCPs (${data.total})`);
            ui.table(
                ['Icon', 'Name', 'Category', 'Auth', 'Type'],
                data.tools.map(t => [
                    t.icon,
                    chalk.white(t.name),
                    ui.ACCENT(t.category),
                    t.requires_auth ? ui.WARN('Yes') : ui.SUCCESS('No'),
                    t.is_builtin ? ui.SUCCESS('Built-in') : ui.DIM('MCP'),
                ])
            );
            console.log(ui.DIM(`  Categories: ${data.categories.join(', ')}\n`));
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── LLMS ─────────────────────────────────────────────────────────────────────

program
    .command('llms')
    .description('Browse all available LLM models with pricing')
    .option('--json', 'Output raw JSON')
    .action(async (options) => {
        config.requireAuth();
        const spin = ui.spinner('Fetching LLM models...');
        try {
            const data = await api.llms();
            spin.stop();

            if (options.json) {
                console.log(JSON.stringify(data.llms, null, 2));
                return;
            }

            ui.sectionHeader(`LLM Models (${data.total})`);
            ui.table(
                ['Model', 'Provider', 'Input $/1M', 'Output $/1M', 'Best For'],
                data.llms.map(l => [
                    chalk.white(l.display_name),
                    ui.ACCENT(l.provider),
                    ui.DIM('$' + l.pricing.input_per_1m.toFixed(2)),
                    ui.DIM('$' + l.pricing.output_per_1m.toFixed(2)),
                    ui.DIM(l.best_for.slice(0, 2).join(', ')),
                ])
            );
            console.log('');
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── REPOS ────────────────────────────────────────────────────────────────────

program
    .command('repos')
    .description('Browse trending open-source AI repositories')
    .option('--json', 'Output raw JSON')
    .action(async (options) => {
        config.requireAuth();
        const spin = ui.spinner('Fetching trending repos...');
        try {
            const data = await api.repos();
            spin.stop();

            if (options.json) {
                console.log(JSON.stringify(data.repos, null, 2));
                return;
            }

            ui.sectionHeader(`Open Source (${data.total})`);
            ui.table(
                ['Repo', 'Language', 'Stars', 'Forks', 'Topics'],
                data.repos.map(r => {
                    const stars = r.stars >= 1000 ? (r.stars / 1000).toFixed(1) + 'k' : r.stars;
                    const forks = r.forks >= 1000 ? (r.forks / 1000).toFixed(1) + 'k' : r.forks;
                    return [
                        chalk.white(r.full_name),
                        ui.ACCENT(r.language),
                        ui.WARN(stars),
                        ui.DIM(forks),
                        ui.DIM(r.topics.slice(0, 3).join(', ')),
                    ];
                })
            );
            console.log('');
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── RUN (prompt) ─────────────────────────────────────────────────────────────

program
    .command('run [prompt...]')
    .description('Run a prompt through the Namango AI Gateway')
    .option('-m, --model <model>', 'Preferred LLM model')
    .option('-a, --agents <agents>', 'Comma-separated agent slugs')
    .option('-t, --tools <tools>', 'Comma-separated tool slugs')
    .option('--json', 'Output raw JSON response')
    .action(async (promptWords, options) => {
        config.requireAuth();
        let prompt = promptWords.join(' ');

        if (!prompt) {
            const answers = await inquirer.prompt([{
                type: 'input',
                name: 'prompt',
                message: chalk.cyan('Enter your prompt:'),
                validate: input => input.length > 3 ? true : 'Prompt too short',
            }]);
            prompt = answers.prompt;
        }

        const body = { prompt };
        if (options.model) body.preferred_model = options.model;
        if (options.agents) body.preferred_agents = options.agents.split(',').map(s => s.trim());
        if (options.tools) body.preferred_tools = options.tools.split(',').map(s => s.trim());

        const spin = ui.spinner('Processing prompt...');
        try {
            const res = await api.query(body);
            spin.stop();

            if (options.json) {
                console.log(JSON.stringify(res, null, 2));
                return;
            }

            ui.sectionHeader('Response');
            console.log(chalk.white('  ' + res.response.replace(/\n/g, '\n  ')));
            console.log('');

            ui.sectionHeader('Orchestration');
            ui.keyValue('Task Category', res.orchestration.task_category);
            ui.keyValue('Complexity', res.orchestration.complexity);
            ui.keyValue('LLM Used', res.orchestration.selected_llm);
            ui.keyValue('Agents', res.orchestration.selected_agents.join(', ') || 'none');
            ui.keyValue('Tools', res.orchestration.selected_tools.join(', ') || 'none');
            ui.keyValue('Routing', res.orchestration.routing_reason);

            if (res.orchestration.tools_executed && res.orchestration.tools_executed.length > 0) {
                console.log('');
                ui.keyValue('Tools Executed', '');
                res.orchestration.tools_executed.forEach(t => {
                    const status = t.success ? ui.SUCCESS('OK') : ui.ERR('FAIL');
                    console.log(`      ${status} ${chalk.white(t.tool)}`);
                });
            }

            console.log('');
            ui.sectionHeader('Usage');
            ui.keyValue('Input Tokens', res.usage.input_tokens.toLocaleString());
            ui.keyValue('Output Tokens', res.usage.output_tokens.toLocaleString());
            ui.keyValue('Cost', '$' + res.usage.cost_usd.toFixed(6));
            ui.keyValue('Latency', res.usage.latency_ms + 'ms');
            console.log('');
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── ARCHITECT ────────────────────────────────────────────────────────────────

program
    .command('architect [description...]')
    .description('Generate a full product architecture from the Namango platform')
    .option('-o, --optimize <type>', 'Optimization priority: cost or quality', 'quality')
    .option('--json', 'Output raw JSON')
    .action(async (descWords, options) => {
        config.requireAuth();
        const apiKey = config.get().apiKey;
        let description = descWords.join(' ');

        if (!description) {
            ui.banner();
            console.log(ui.ACCENT('  Describe the application you want to build.'));
            console.log(ui.DIM('  The Namango Solutions Architect will design an optimal'));
            console.log(ui.DIM('  architecture using marketplace agents, tools, and LLMs.\n'));

            const answers = await inquirer.prompt([
                {
                    type: 'input',
                    name: 'description',
                    message: chalk.cyan('What are you building?'),
                    validate: input => input.length > 10 ? true : 'Please describe in more detail',
                },
                {
                    type: 'list',
                    name: 'optimization',
                    message: 'Optimization priority:',
                    choices: [
                        { name: chalk.green('Cost-Effective') + ui.DIM(' — Open-source & cheapest models'), value: 'cost' },
                        { name: chalk.yellow('Highest Quality') + ui.DIM(' — Enterprise APIs & heavy models'), value: 'quality' },
                    ],
                },
            ]);
            description = answers.description;
            options.optimize = answers.optimization;
        }

        const spin = ui.spinner('Solutions Architect is designing your architecture...');
        try {
            const arch = await api.architect(description, options.optimize, apiKey);
            spin.stop();

            if (options.json) {
                console.log(JSON.stringify(arch, null, 2));
                return;
            }

            ui.sectionHeader('Product Architecture');

            if (arch.error_fallback) {
                console.log(ui.WARN('  Note: Used fallback defaults (LLM API temporarily unavailable)\n'));
            }

            ui.keyValue('Framework', arch.framework);
            ui.keyValue('LLM Engine', arch.recommended_llm);
            console.log('');

            console.log(ui.ACCENT('    Recommended Agents:'));
            arch.recommended_agents.forEach(a => {
                console.log(`      ${ui.SUCCESS('+')} ${chalk.white(a)}`);
            });
            console.log('');

            console.log(ui.ACCENT('    Recommended MCPs:'));
            arch.recommended_mcps.forEach(m => {
                console.log(`      ${ui.SUCCESS('+')} ${chalk.white(m)}`);
            });
            console.log('');

            console.log(ui.ACCENT('    Rationale:'));
            console.log(ui.DIM('      ' + arch.explanation));
            console.log('');

            const { scaffold } = await inquirer.prompt([{
                type: 'confirm',
                name: 'scaffold',
                message: 'Scaffold a project with this architecture?',
                default: false,
            }]);

            if (scaffold) {
                const { projectName } = await inquirer.prompt([{
                    type: 'input',
                    name: 'projectName',
                    message: 'Project name:',
                    default: 'my-ai-app',
                }]);

                const projectPath = path.join(process.cwd(), projectName);
                if (!fs.existsSync(projectPath)) fs.mkdirSync(projectPath, { recursive: true });

                let code = `import os\nfrom namango import GatewayClient\n\n`;
                code += `# Architecture designed by Namango Solutions Architect\n`;
                code += `# Framework : ${arch.framework}\n`;
                code += `# Agents    : ${arch.recommended_agents.join(', ')}\n`;
                code += `# MCPs      : ${arch.recommended_mcps.join(', ')}\n`;
                code += `# LLM       : ${arch.recommended_llm}\n\n`;
                code += `client = GatewayClient(api_key=os.getenv('NAMANGO_API_KEY'))\n\n`;
                code += `def run():\n`;
                code += `    response = client.query(\n`;
                code += `        prompt="Your task here",\n`;
                code += `        preferred_model="${arch.recommended_llm}",\n`;
                code += `        preferred_agents=${JSON.stringify(arch.recommended_agents)},\n`;
                code += `    )\n`;
                code += `    print(response)\n\n`;
                code += `if __name__ == "__main__":\n    run()\n`;

                fs.writeFileSync(path.join(projectPath, 'main.py'), code);
                fs.writeFileSync(path.join(projectPath, 'requirements.txt'), 'namango-sdk\nlangchain\n');
                fs.writeFileSync(path.join(projectPath, '.env'), `NAMANGO_API_KEY=${apiKey}\n`);

                const namangoConfig = {
                    framework: arch.framework,
                    llm: arch.recommended_llm,
                    agents: arch.recommended_agents,
                    mcps: arch.recommended_mcps,
                    optimization: options.optimize,
                };
                fs.writeFileSync(path.join(projectPath, 'namango.config.json'), JSON.stringify(namangoConfig, null, 2));

                console.log(ui.SUCCESS(`\n  Project scaffolded at ./${projectName}/`));
                console.log(ui.DIM('  Files: main.py, requirements.txt, .env, namango.config.json\n'));
            }
        } catch (e) {
            spin.fail(ui.ERR('Architecture generation failed: ' + e.message));
        }
    });

// ─── ADD (Composio-style tool integration) ────────────────────────────────────

program
    .command('add <tool-slug>')
    .description('Add and configure an MCP or tool integration (Composio-style)')
    .action(async (toolSlug) => {
        config.requireAuth();
        const spin = ui.spinner(`Fetching integration manifest for ${chalk.bold(toolSlug)}...`);

        try {
            const tool = await api.toolDetail(toolSlug);
            spin.succeed(ui.SUCCESS(`Found: ${tool.name}`));
            console.log(ui.DIM(`  ${tool.description}\n`));

            const authAnswers = {};
            if (tool.requires_auth) {
                console.log(ui.WARN('  This integration requires authentication.\n'));
                for (const [key, desc] of Object.entries(tool.parameters || {})) {
                    const ans = await inquirer.prompt([{
                        type: 'password',
                        name: 'val',
                        message: `Enter ${desc || key}:`,
                        mask: '*',
                    }]);
                    authAnswers[key] = ans.val;
                }
            }

            const envPath = path.join(process.cwd(), '.env');
            let envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf-8') : '';
            for (const [key, val] of Object.entries(authAnswers)) {
                const envVarName = `${toolSlug.toUpperCase().replace(/-/g, '_')}_${key.toUpperCase()}`;
                if (!envContent.includes(envVarName)) {
                    envContent += `\n${envVarName}=${val}`;
                }
            }
            fs.writeFileSync(envPath, envContent);

            const namangoConfigPath = path.join(process.cwd(), 'namango.config.json');
            let namangoConfig = fs.existsSync(namangoConfigPath) ? JSON.parse(fs.readFileSync(namangoConfigPath, 'utf-8')) : { integrations: [] };
            if (!namangoConfig.integrations) namangoConfig.integrations = [];
            if (!namangoConfig.integrations.includes(toolSlug)) {
                namangoConfig.integrations.push(toolSlug);
            }
            fs.writeFileSync(namangoConfigPath, JSON.stringify(namangoConfig, null, 2));

            console.log(ui.SUCCESS(`\n  Integrated ${tool.name} successfully`));
            console.log(ui.DIM('  Secrets added to .env, slug added to namango.config.json\n'));
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── HISTORY ──────────────────────────────────────────────────────────────────

program
    .command('history')
    .description('View recent request history')
    .option('-n, --limit <number>', 'Number of entries', '10')
    .action(async (options) => {
        config.requireAuth();
        const spin = ui.spinner('Fetching history...');
        try {
            const data = await api.history(parseInt(options.limit));
            spin.stop();

            if (!data.items || data.items.length === 0) {
                console.log(ui.DIM('\n  No requests found.\n'));
                return;
            }

            ui.sectionHeader(`Recent Requests (${data.items.length})`);
            ui.table(
                ['Prompt', 'Model', 'Category', 'Latency', 'Status'],
                data.items.map(item => [
                    chalk.white((item.prompt || '').slice(0, 50) + (item.prompt && item.prompt.length > 50 ? '...' : '')),
                    ui.DIM(item.selected_llm || '-'),
                    ui.ACCENT(item.task_category || '-'),
                    ui.DIM(item.latency_ms ? item.latency_ms + 'ms' : '-'),
                    item.status === 'completed' ? ui.SUCCESS(item.status) : ui.ERR(item.status),
                ])
            );
            console.log('');
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── INTERACTIVE MODE ─────────────────────────────────────────────────────────

program
    .command('interactive')
    .alias('i')
    .description('Launch interactive mode — browse marketplace and run prompts')
    .action(async () => {
        config.requireAuth();
        ui.banner();

        let running = true;
        while (running) {
            const { action } = await inquirer.prompt([{
                type: 'list',
                name: 'action',
                message: chalk.cyan('What would you like to do?'),
                choices: [
                    { name: `${chalk.white('Browse Agents')}       ${ui.DIM('— View all AI agents')}`, value: 'agents' },
                    { name: `${chalk.white('Browse Tools')}        ${ui.DIM('— View tools & MCPs')}`, value: 'tools' },
                    { name: `${chalk.white('Browse LLMs')}         ${ui.DIM('— View models & pricing')}`, value: 'llms' },
                    { name: `${chalk.white('Browse Repos')}        ${ui.DIM('— Trending AI open source')}`, value: 'repos' },
                    new inquirer.Separator(),
                    { name: `${chalk.white('Run a Prompt')}        ${ui.DIM('— Send query to gateway')}`, value: 'run' },
                    { name: `${chalk.white('Architect')}           ${ui.DIM('— Design product architecture')}`, value: 'architect' },
                    { name: `${chalk.white('View History')}        ${ui.DIM('— Recent requests')}`, value: 'history' },
                    new inquirer.Separator(),
                    { name: ui.DIM('Exit'), value: 'exit' },
                ],
            }]);

            if (action === 'exit') {
                running = false;
                console.log(ui.DIM('\n  Goodbye.\n'));
                break;
            }

            try {
                if (action === 'agents') {
                    const spin = ui.spinner('Loading agents...');
                    const data = await api.agents();
                    spin.stop();
                    ui.table(
                        ['Icon', 'Name', 'Category', 'LLM', 'Type'],
                        data.agents.map(a => [a.icon, chalk.white(a.name), ui.ACCENT(a.category), ui.DIM(a.preferred_llm.split('-').slice(0, 2).join('-')), a.is_builtin ? ui.SUCCESS('Built-in') : ui.WARN('Community')])
                    );
                }

                if (action === 'tools') {
                    const spin = ui.spinner('Loading tools...');
                    const data = await api.tools();
                    spin.stop();
                    ui.table(
                        ['Icon', 'Name', 'Category', 'Auth', 'Type'],
                        data.tools.map(t => [t.icon, chalk.white(t.name), ui.ACCENT(t.category), t.requires_auth ? ui.WARN('Yes') : ui.SUCCESS('No'), t.is_builtin ? ui.SUCCESS('Built-in') : ui.DIM('MCP')])
                    );
                }

                if (action === 'llms') {
                    const spin = ui.spinner('Loading LLMs...');
                    const data = await api.llms();
                    spin.stop();
                    ui.table(
                        ['Model', 'Provider', 'Input $/1M', 'Output $/1M'],
                        data.llms.map(l => [chalk.white(l.display_name), ui.ACCENT(l.provider), ui.DIM('$' + l.pricing.input_per_1m.toFixed(2)), ui.DIM('$' + l.pricing.output_per_1m.toFixed(2))])
                    );
                }

                if (action === 'repos') {
                    const spin = ui.spinner('Loading repos...');
                    const data = await api.repos();
                    spin.stop();
                    ui.table(
                        ['Repo', 'Language', 'Stars', 'Topics'],
                        data.repos.map(r => [chalk.white(r.full_name), ui.ACCENT(r.language), ui.WARN(r.stars >= 1000 ? (r.stars / 1000).toFixed(1) + 'k' : r.stars), ui.DIM(r.topics.slice(0, 3).join(', '))])
                    );
                }

                if (action === 'run') {
                    const { prompt } = await inquirer.prompt([{
                        type: 'input',
                        name: 'prompt',
                        message: chalk.cyan('Enter prompt:'),
                        validate: input => input.length > 3,
                    }]);
                    const spin = ui.spinner('Processing...');
                    const res = await api.query({ prompt });
                    spin.stop();
                    console.log('');
                    console.log(chalk.white('  ' + res.response.replace(/\n/g, '\n  ')));
                    console.log('');
                    ui.keyValue('LLM', res.orchestration.selected_llm);
                    ui.keyValue('Category', res.orchestration.task_category);
                    ui.keyValue('Latency', res.usage.latency_ms + 'ms');
                    ui.keyValue('Cost', '$' + res.usage.cost_usd.toFixed(6));
                    console.log('');
                }

                if (action === 'architect') {
                    const answers = await inquirer.prompt([
                        { type: 'input', name: 'description', message: chalk.cyan('What are you building?'), validate: i => i.length > 10 },
                        { type: 'list', name: 'optimization', message: 'Optimize for:', choices: [{ name: 'Cost-Effective', value: 'cost' }, { name: 'Highest Quality', value: 'quality' }] },
                    ]);
                    const spin = ui.spinner('Designing architecture...');
                    const arch = await api.architect(answers.description, answers.optimization, config.get().apiKey);
                    spin.stop();
                    ui.sectionHeader('Architecture');
                    ui.keyValue('Framework', arch.framework);
                    ui.keyValue('LLM', arch.recommended_llm);
                    console.log(ui.ACCENT('    Agents:'));
                    arch.recommended_agents.forEach(a => console.log(`      ${ui.SUCCESS('+')} ${chalk.white(a)}`));
                    console.log(ui.ACCENT('    MCPs:'));
                    arch.recommended_mcps.forEach(m => console.log(`      ${ui.SUCCESS('+')} ${chalk.white(m)}`));
                    console.log(ui.DIM(`\n    ${arch.explanation}\n`));
                }

                if (action === 'history') {
                    const spin = ui.spinner('Loading history...');
                    const data = await api.history(10);
                    spin.stop();
                    if (!data.items || data.items.length === 0) {
                        console.log(ui.DIM('\n  No requests yet.\n'));
                    } else {
                        ui.table(
                            ['Prompt', 'Model', 'Status'],
                            data.items.map(i => [chalk.white((i.prompt || '').slice(0, 60)), ui.DIM(i.selected_llm || '-'), i.status === 'completed' ? ui.SUCCESS(i.status) : ui.ERR(i.status)])
                        );
                    }
                }
            } catch (e) {
                console.log(ui.ERR('\n  Error: ' + e.message + '\n'));
            }
        }
    });

// ─── INIT (legacy, kept for backwards compat) ─────────────────────────────────

program
    .command('init [project-name]')
    .description('Scaffold a new project (shortcut: runs architect + scaffold)')
    .action(async (projectName) => {
        console.log(ui.DIM('\n  Redirecting to `namango architect` ...\n'));
        program.parse(['node', 'namango', 'architect']);
    });

program.parse(process.argv);

if (!process.argv.slice(2).length) {
    ui.banner();
    program.outputHelp();
}
