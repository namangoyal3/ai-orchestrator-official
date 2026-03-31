#!/usr/bin/env node

const { program } = require('commander');
const inquirer = require('inquirer');
const fs = require('fs');
const path = require('path');
const chalk = require('chalk');
const config = require('../lib/config');
const api = require('../lib/api');
const ui = require('../lib/ui');

// GPT-4o pricing for cost comparison (per token)
const GPT4O_INPUT_PER_TOKEN  = 5.00  / 1_000_000;  // $5/1M input
const GPT4O_OUTPUT_PER_TOKEN = 15.00 / 1_000_000;  // $15/1M output

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
            // Verify the key itself by calling an authenticated endpoint, not just /health
            await api.verifyKey(apiKey);
            config.save({ apiKey });
            spin.succeed(ui.SUCCESS('Authenticated successfully'));
            console.log(ui.DIM('    Key stored at: ~/.namango/config.json\n'));
        } catch (e) {
            if (e.message && (e.message.includes('401') || e.message.toLowerCase().includes('invalid'))) {
                spin.fail(ui.ERR('Invalid API key — check your key and try again'));
            } else {
                spin.fail(ui.ERR('Could not reach platform: ' + e.message));
            }
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
    .option('--context-url <url>', 'Scrape this URL as context before running')
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
        if (options.contextUrl) body.context_url = options.contextUrl;

        const spinMsg = options.contextUrl
            ? `Scraping context from ${options.contextUrl.slice(0, 60)}...`
            : 'Processing prompt...';
        const spin = ui.spinner(spinMsg);
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
            if (res.orchestration.context_extracted) ui.keyValue('Context', 'Extracted from URL');
            ui.keyValue('Routing', res.orchestration.routing_reason);

            if (res.orchestration.tools_executed && res.orchestration.tools_executed.length > 0) {
                console.log('');
                console.log(ui.ACCENT('    Execution:'));
                res.orchestration.tools_executed.forEach(t => {
                    const status = t.success ? ui.SUCCESS('✓') : ui.ERR('✗');
                    console.log(`      ${status} ${chalk.white(t.tool)}`);
                });
            }

            console.log('');
            ui.sectionHeader('Cost');
            const inputTokens  = res.usage.input_tokens  || 0;
            const outputTokens = res.usage.output_tokens || 0;
            const gpt4oCost = (inputTokens * GPT4O_INPUT_PER_TOKEN) + (outputTokens * GPT4O_OUTPUT_PER_TOKEN);
            const actualCost = res.usage.cost_usd || 0;
            const savedPct = gpt4oCost > 0 ? ((gpt4oCost - actualCost) / gpt4oCost * 100) : 0;

            ui.keyValue('This request', '$' + actualCost.toFixed(6));
            ui.keyValue('GPT-4o equiv', '$' + gpt4oCost.toFixed(6) + ui.DIM('  (estimated)'));
            console.log(`    ${ui.DIM('Saved:')} ${chalk.green(savedPct.toFixed(1) + '%')}  ${ui.DIM('vs GPT-4o direct')}`);
            ui.keyValue('Input Tokens', inputTokens.toLocaleString());
            ui.keyValue('Output Tokens', outputTokens.toLocaleString());
            ui.keyValue('Latency', res.usage.latency_ms + 'ms');
            console.log('');
        } catch (e) {
            spin.fail(ui.ERR(e.message));
        }
    });

// ─── DESIGN (marketplace recommend — describe product → full stack) ───────────

program
    .command('design [description...]')
    .description('Describe your product → get a recommended agent/tool/LLM stack')
    .option('-u, --use-cases <cases>', 'Comma-separated use cases')
    .option('--json', 'Output raw JSON')
    .action(async (descWords, options) => {
        config.requireAuth();
        let description = descWords.join(' ');

        if (!description) {
            ui.banner();
            console.log(ui.ACCENT('  Describe the product or workflow you want to build.'));
            console.log(ui.DIM('  Namango will recommend the optimal agent + tool + LLM stack\n'));
            const answers = await inquirer.prompt([{
                type: 'input',
                name: 'description',
                message: chalk.cyan('What are you building?'),
                validate: input => input.length > 10 ? true : 'Please describe in more detail',
            }]);
            description = answers.description;
        }

        const useCases = options.useCases
            ? options.useCases.split(',').map(s => s.trim())
            : [];

        const spin = ui.spinner('Designing your optimal AI stack...');
        try {
            const rec = await api.recommend(description, useCases);
            spin.stop();

            if (options.json) {
                console.log(JSON.stringify(rec, null, 2));
                return;
            }

            ui.sectionHeader('Stack Recommendation');
            ui.keyValue('Product', rec.product_summary);
            ui.keyValue('LLM', rec.recommended_llm);
            console.log(ui.DIM('    ' + rec.llm_reason));

            if (rec.recommended_agents && rec.recommended_agents.length > 0) {
                console.log('');
                console.log(ui.ACCENT('    Recommended Agents:'));
                rec.recommended_agents.forEach(a => {
                    console.log(`      ${ui.SUCCESS('+')} ${chalk.white(a.icon + ' ' + a.name)}`);
                    console.log(ui.DIM(`          Role: ${a.role_in_flow}`));
                    console.log(ui.DIM(`          Why:  ${a.reason}`));
                });
            }

            if (rec.recommended_tools && rec.recommended_tools.length > 0) {
                console.log('');
                console.log(ui.ACCENT('    Recommended Tools:'));
                rec.recommended_tools.forEach(t => {
                    console.log(`      ${ui.SUCCESS('+')} ${chalk.white(t.icon + ' ' + t.name)}`);
                    console.log(ui.DIM(`          Used by: ${t.used_by_agent}  —  ${t.reason}`));
                });
            }

            if (rec.action_plan && rec.action_plan.length > 0) {
                console.log('');
                console.log(ui.ACCENT('    Action Plan:'));
                rec.action_plan.forEach(step => {
                    console.log(`      ${chalk.white('Step ' + step.step + ':')} ${chalk.white(step.title)}`);
                    console.log(ui.DIM(`          ${step.description}`));
                    if (step.agents && step.agents.length > 0)
                        console.log(ui.DIM(`          Agents: ${step.agents.join(', ')}`));
                    if (step.tools && step.tools.length > 0)
                        console.log(ui.DIM(`          Tools:  ${step.tools.join(', ')}`));
                    console.log(ui.DIM(`          → ${step.expected_output}`));
                });
            }

            // Build "try it now" command from recommended agents/tools
            const agentSlugs = (rec.recommended_agents || []).map(a => a.slug).join(',');
            const toolSlugs  = (rec.recommended_tools  || []).map(t => t.slug).join(',');
            console.log('');
            console.log(ui.ACCENT('    Try It Now:'));
            let tryCmd = `namango run "your task here"`;
            if (agentSlugs) tryCmd += ` \\\n      --agents ${agentSlugs}`;
            if (toolSlugs)  tryCmd += ` \\\n      --tools ${toolSlugs}`;
            console.log('      ' + chalk.cyan(tryCmd));

            if (rec.api_snippet) {
                console.log('');
                console.log(ui.ACCENT('    API Snippet:'));
                rec.api_snippet.split('\n').forEach(line => {
                    console.log(ui.DIM('      ' + line));
                });
            }

            console.log('');
        } catch (e) {
            spin.fail(ui.ERR('Stack recommendation failed: ' + e.message));
        }
    });

// ─── STACKS ───────────────────────────────────────────────────────────────────

program
    .command('stacks')
    .description('Browse curated community stacks — pre-built agent+tool configurations')
    .action(async () => {
        config.requireAuth();

        const CURATED = [
            {
                name: 'competitor-monitor',
                description: 'Monitor competitor pricing pages daily, alert on changes',
                agents: 'research, code',
                tools: 'web_scrape, web_search',
                cost: '~$0.004/day (10 competitors)',
            },
            {
                name: 'github-explorer',
                description: 'Research, rank, and summarize open-source repos for a topic',
                agents: 'github_librarian',
                tools: 'github_repo_info, github_search_and_rank',
                cost: '~$0.001/query',
            },
            {
                name: 'content-researcher',
                description: 'Deep research on any topic with cited sources',
                agents: 'research',
                tools: 'web_scrape, web_search',
                cost: '~$0.002/query',
            },
            {
                name: 'code-reviewer',
                description: 'Review a GitHub repo for bugs, security issues, and improvements',
                agents: 'code',
                tools: 'github_repo_info, web_search',
                cost: '~$0.003/review',
            },
        ];

        ui.sectionHeader('Community Stacks');
        ui.table(
            ['Stack', 'What It Does', 'Agents', 'Tools', 'Est. Cost'],
            CURATED.map(s => [
                chalk.white(s.name),
                ui.DIM(s.description.slice(0, 45) + (s.description.length > 45 ? '…' : '')),
                ui.ACCENT(s.agents),
                ui.DIM(s.tools),
                ui.SUCCESS(s.cost),
            ])
        );
        console.log(ui.DIM('  Build your own:'));
        console.log('  ' + chalk.cyan('namango design "describe your product"'));
        console.log('');
    });

// ─── ARCHITECT ────────────────────────────────────────────────────────────────

program
    .command('architect [description...]')
    .description('Generate a full product architecture from the Namango platform')
    .option('-o, --optimize <type>', 'Optimization priority: cost or quality', 'quality')
    .option('--json', 'Output raw JSON')
    .action(async (descWords, options) => {
        config.requireAuth();
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
            // api_key no longer passed in body — sent as X-API-Key header by api.request()
            const arch = await api.architect(description, options.optimize);
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

            const agentHint = (arch.recommended_agents || []).slice(0, 2).join(',');
            console.log(ui.ACCENT('    Try It Now:'));
            console.log('      ' + chalk.cyan(`namango run "your task here"${agentHint ? ' --agents ' + agentHint : ''}`));
            console.log('      ' + chalk.cyan(`namango design "${(description || 'your product').slice(0, 50)}"`));
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
                ['Prompt', 'Model', 'Category', 'Cost', 'Latency', 'Status'],
                data.items.map(item => [
                    chalk.white((item.prompt || '').slice(0, 40) + (item.prompt && item.prompt.length > 40 ? '...' : '')),
                    ui.DIM(item.selected_llm || '-'),
                    ui.ACCENT(item.task_category || '-'),
                    item.cost_usd != null ? ui.DIM('$' + Number(item.cost_usd).toFixed(6)) : ui.DIM('-'),
                    ui.DIM(item.latency_ms ? item.latency_ms + 'ms' : '-'),
                    item.status === 'completed' ? ui.SUCCESS(item.status) : ui.ERR(item.status),
                ])
            );

            // Cumulative savings footer
            const completed = data.items.filter(i => i.status === 'completed' && i.cost_usd != null);
            if (completed.length > 0) {
                const totalCost = completed.reduce((s, i) => s + Number(i.cost_usd), 0);
                // Estimate GPT-4o cost: assume avg 500 input + 500 output tokens per request
                const avgTokens = 500;
                const gpt4oEquiv = completed.length * ((avgTokens * GPT4O_INPUT_PER_TOKEN) + (avgTokens * GPT4O_OUTPUT_PER_TOKEN));
                const savedPct = gpt4oEquiv > 0 ? ((gpt4oEquiv - totalCost) / gpt4oEquiv * 100) : 0;
                console.log(`    ${ui.DIM('Total cost:')}   ${chalk.white('$' + totalCost.toFixed(6))}`);
                console.log(`    ${ui.DIM('GPT-4o equiv:')} ${chalk.white('$' + gpt4oEquiv.toFixed(4))} ${ui.DIM('(estimated, 500 tok avg)')}`);
                console.log(`    ${ui.DIM('You saved:')}    ${chalk.green(savedPct.toFixed(1) + '%')} ${ui.DIM('vs GPT-4o direct')}`);
            }
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
                    { name: `${chalk.white('Design Stack')}        ${ui.DIM('— Describe product → recommended stack')}`, value: 'design' },
                    { name: `${chalk.white('Run a Prompt')}        ${ui.DIM('— Send query to gateway')}`, value: 'run' },
                    new inquirer.Separator(),
                    { name: `${chalk.white('Browse Agents')}       ${ui.DIM('— View all AI agents')}`, value: 'agents' },
                    { name: `${chalk.white('Browse Tools')}        ${ui.DIM('— View tools & MCPs')}`, value: 'tools' },
                    { name: `${chalk.white('Browse LLMs')}         ${ui.DIM('— View models & pricing')}`, value: 'llms' },
                    { name: `${chalk.white('Browse Repos')}        ${ui.DIM('— Trending AI open source')}`, value: 'repos' },
                    new inquirer.Separator(),
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

                if (action === 'design') {
                    const { description } = await inquirer.prompt([{
                        type: 'input',
                        name: 'description',
                        message: chalk.cyan('What are you building?'),
                        validate: input => input.length > 10 ? true : 'Please describe in more detail',
                    }]);
                    const spin = ui.spinner('Designing your optimal AI stack...');
                    const rec = await api.recommend(description, []);
                    spin.stop();
                    ui.sectionHeader('Stack Recommendation');
                    ui.keyValue('Product', rec.product_summary);
                    ui.keyValue('LLM', rec.recommended_llm);
                    if (rec.recommended_agents && rec.recommended_agents.length > 0) {
                        console.log(ui.ACCENT('\n    Agents:'));
                        rec.recommended_agents.forEach(a => {
                            console.log(`      ${ui.SUCCESS('+')} ${chalk.white(a.icon + ' ' + a.name)}`);
                            console.log(ui.DIM(`          ${a.role_in_flow}`));
                        });
                    }
                    if (rec.recommended_tools && rec.recommended_tools.length > 0) {
                        console.log(ui.ACCENT('\n    Tools:'));
                        rec.recommended_tools.forEach(t => {
                            console.log(`      ${ui.SUCCESS('+')} ${chalk.white(t.icon + ' ' + t.name)} ${ui.DIM('— ' + t.reason)}`);
                        });
                    }
                    const agentSlugs = (rec.recommended_agents || []).map(a => a.slug).join(',');
                    const toolSlugs  = (rec.recommended_tools  || []).map(t => t.slug).join(',');
                    console.log(ui.ACCENT('\n    Try It Now:'));
                    let tryCmd = `namango run "your task here"`;
                    if (agentSlugs) tryCmd += ` --agents ${agentSlugs}`;
                    if (toolSlugs)  tryCmd += ` --tools ${toolSlugs}`;
                    console.log('      ' + chalk.cyan(tryCmd));
                    console.log('');
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
                    const gpt4oCost = ((res.usage.input_tokens || 0) * GPT4O_INPUT_PER_TOKEN) + ((res.usage.output_tokens || 0) * GPT4O_OUTPUT_PER_TOKEN);
                    const savedPct = gpt4oCost > 0 ? (((gpt4oCost - res.usage.cost_usd) / gpt4oCost) * 100).toFixed(1) : '0.0';
                    ui.keyValue('Cost', '$' + res.usage.cost_usd.toFixed(6) + chalk.green(`  (saved ${savedPct}% vs GPT-4o)`));
                    console.log('');
                }

                if (action === 'architect') {
                    const answers = await inquirer.prompt([
                        { type: 'input', name: 'description', message: chalk.cyan('What are you building?'), validate: i => i.length > 10 },
                        { type: 'list', name: 'optimization', message: 'Optimize for:', choices: [{ name: 'Cost-Effective', value: 'cost' }, { name: 'Highest Quality', value: 'quality' }] },
                    ]);
                    const spin = ui.spinner('Designing architecture...');
                    const arch = await api.architect(answers.description, answers.optimization);
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
    .action(async () => {
        // program.parse() cannot be called recursively in commander v10+.
        // Instead, run the architect command handler directly via execFileSync.
        const { execFileSync } = require('child_process');
        console.log(ui.DIM('\n  Redirecting to `namango architect` ...\n'));
        try {
            execFileSync(process.execPath, [process.argv[1], 'architect'], { stdio: 'inherit' });
        } catch (e) {
            // execFileSync throws on non-zero exit; child already printed the error
        }
    });

program.parse(process.argv);

if (!process.argv.slice(2).length) {
    ui.banner();
    program.outputHelp();
}
