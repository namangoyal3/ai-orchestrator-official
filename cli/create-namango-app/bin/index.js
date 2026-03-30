#!/usr/bin/env node

const { program } = require('commander');
const inquirer = require('inquirer');
const fs = require('fs');
const path = require('path');
const chalk = require('chalk');
const os = require('os');

const CONFIG_DIR = path.join(os.homedir(), '.namango');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

function getConfig() {
    if (fs.existsSync(CONFIG_FILE)) {
        return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8'));
    }
    return {};
}

function saveConfig(config) {
    if (!fs.existsSync(CONFIG_DIR)) {
        fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

program
  .version('1.0.0')
  .description('Namango AI Gateway Project Generator');

program
    .command('login')
    .description('Authenticate with the Namango Gateway')
    .action(async () => {
        console.log(chalk.bold.blue('\n🔐 Login to Namango Gateway\n'));
        const answers = await inquirer.prompt([
            {
                type: 'input',
                name: 'apiKey',
                message: 'Enter your Namango API Key (starts with gw-):',
                validate: input => input.startsWith('gw-') || input.startsWith('sk-') ? true : 'Please enter a valid API key.'
            }
        ]);
        saveConfig({ apiKey: answers.apiKey });
        console.log(chalk.green('✅ Successfully authenticated! Your API key is cached locally.'));
        console.log(chalk.cyan('You can now use `namango init <project>` from anywhere!'));
    });

program
    .command('init [project-name]')
    .description('Scaffold a new Namango AI Agent application')
    .option('--headless', 'Run in headless autonomous mode (bypasses terminal prompts)')
    .option('--framework <type>', 'Framework choice: LangChain, CrewAI, Native', 'LangChain (Python)')
    .option('--agents <items>', 'Comma separated list of marketplace agents to include', '')
    .option('--mcps <items>', 'Comma separated list of MCPs to include', '')
    .option('--llm <model>', 'Default LLM for routing', 'openai/gpt-4o')
    .option('--api-key <key>', 'Override the strictly cached Namango API Key')
    .action(async (projectName, options) => {
        const config = getConfig();
        const activeKey = options.apiKey || config.apiKey;

        if (!activeKey && !options.headless) {
            console.log(chalk.red('\n❌ You are not authenticated!'));
            console.log(chalk.yellow('Please run `namango login` first, or pass the `--api-key` flag.\n'));
            process.exit(1);
        }

        console.log(chalk.bold.blue('\n🚀 Welcome to Create Namango App!\n'));

        if (!projectName) {
            if (options.headless) {
                projectName = "ai-scaffolded-test-app";
            } else {
                const answers = await inquirer.prompt([
                    {
                        type: 'input',
                        name: 'project',
                        message: 'What is your project name?',
                        default: 'my-ai-app'
                    }
                ]);
                projectName = answers.project;
            }
        }

        let techStack = { framework: options.framework };
        let marketplaceSelections = {
            agents: options.agents ? options.agents.split(',').map(s => s.trim()) : [],
            mcps: options.mcps ? options.mcps.split(',').map(s => s.trim()) : [],
            llm: options.llm
        };

        if (!options.headless) {
            console.log(chalk.yellow('\n🤖 Connecting to Namango Solutions Architect...'));
            
            const designPrompt = await inquirer.prompt([
                {
                    type: 'input',
                    name: 'prompt',
                    message: 'Describe the AI Application you want to build:',
                    validate: input => input.length > 5 ? true : 'Please provide a descriptive prompt.'
                },
                {
                    type: 'list',
                    name: 'optimization',
                    message: 'What is your optimization priority?',
                    choices: [
                        { name: '💰 Cost-Effective (Open Source & Lowest Token Prices)', value: 'cost' },
                        { name: '⭐ Highest Quality (Enterprise APIs & Heavy Models)', value: 'quality' }
                    ]
                }
            ]);

            console.log(chalk.cyan(`\n⏳ Validating concept and pulling components from production...`));
            
            try {
                // Point dynamically to live production server to parse logic!
                const response = await fetch('https://ai-gateway-backend-production.up.railway.app/v1/architect/design', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: designPrompt.prompt,
                        optimization: designPrompt.optimization,
                        api_key: activeKey
                    })
                });

                if (!response.ok) throw new Error(`API status ${response.status}`);

                const architecture = await response.json();
                
                console.log(chalk.bold.magenta('\n=== 🏗️ Recommended AI Architecture ==='));
                console.log(chalk.white(`• Framework : `) + chalk.green(architecture.framework));
                console.log(chalk.white(`• LLM Engine: `) + chalk.green(architecture.recommended_llm));
                console.log(chalk.white(`• Agents    : `) + chalk.cyan(architecture.recommended_agents.join(', ')));
                console.log(chalk.white(`• Data MCPs : `) + chalk.cyan(architecture.recommended_mcps.join(', ')));
                console.log(chalk.gray(`> Rationale : ${architecture.explanation}\n`));

                const confirmation = await inquirer.prompt([{
                    type: 'confirm', name: 'proceed', message: 'Proceed with architecture scaffold?', default: true
                }]);

                if (!confirmation.proceed) {
                    console.log(chalk.red('\nAborted.'));
                    process.exit(0);
                }

                techStack.framework = architecture.framework;
                marketplaceSelections.agents = architecture.recommended_agents;
                marketplaceSelections.mcps = architecture.recommended_mcps;
                marketplaceSelections.llm = architecture.recommended_llm;
            } catch (err) {
                console.log(chalk.red(`\n❌ Contacted fallback configuration due to: ${err.message}`));
                techStack = await inquirer.prompt([{ type: 'list', name: 'framework', message: 'Fallback Framework:', choices: ['LangChain (Python)'] }]);
            }
        }

        const projectPath = path.join(process.cwd(), projectName);
        console.log(chalk.green(`\n✨ Creating structure in ${projectPath}...`));
        
        if (!fs.existsSync(projectPath)) fs.mkdirSync(projectPath, { recursive: true });

        let codeStr = "";
        if (techStack.framework.includes('Python') || techStack.framework.includes('LangChain')) {
            codeStr = `import os\nfrom namango import GatewayClient\n\n`;
            codeStr += `# Project scaffolded with:\n`;
            codeStr += `# - Agents: ${marketplaceSelections.agents.join(', ')}\n`;
            codeStr += `# - MCPs: ${marketplaceSelections.mcps.join(', ')}\n`;
            codeStr += `# - LLM: ${marketplaceSelections.llm}\n\n`;
            codeStr += `client = GatewayClient(api_key=os.getenv('NAMANGO_API_KEY'))\n\n`;
            codeStr += `def run_mvp():\n`;
            codeStr += `    print("Starting AI Orchestration pipeline...")\n`;
            codeStr += `    print("Using LLM Engine: ${marketplaceSelections.llm}")\n\n`;
            codeStr += `if __name__ == "__main__":\n    run_mvp()\n`;

            fs.writeFileSync(path.join(projectPath, 'main.py'), codeStr);
            fs.writeFileSync(path.join(projectPath, 'requirements.txt'), 'namango-sdk\nlangchain\ncrewai\n');
            fs.writeFileSync(path.join(projectPath, '.env'), `NAMANGO_API_KEY=${activeKey || 'headless_key'}\n`);
        }

        console.log(chalk.bold.green(`\n🎉 Success! Your MVP is ready.\n`));
    });

program
    .command('add <tool-slug>')
    .description('Add and configure a new MCP or Tool integration (Composio-style)')
    .action(async (toolSlug) => {
        const config = getConfig();
        if (!config.apiKey) {
            console.log(chalk.red('❌ Please login first: namango login'));
            process.exit(1);
        }

        console.log(chalk.cyan(`\n🔍 Fetching integration manifest for ${chalk.bold(toolSlug)}...`));
        
        try {
            const response = await fetch(`https://ai-gateway-backend-production.up.railway.app/v1/marketplace/tools/${toolSlug}`, {
                headers: { 'X-API-Key': config.apiKey }
            });

            if (!response.ok) throw new Error(`Integration '${toolSlug}' not found in Namango Marketplace.`);
            
            const tool = await response.json();
            console.log(chalk.green(`✅ Found: ${tool.name}`));
            console.log(chalk.gray(`> ${tool.description}\n`));

            const authAnswers = {};
            if (tool.requires_auth) {
                console.log(chalk.yellow(`🔐 This integration requires authentication.`));
                for (const [key, desc] of Object.entries(tool.parameters || {})) {
                    const ans = await inquirer.prompt([{
                        type: 'password',
                        name: 'val',
                        message: `Enter ${desc || key}:`
                    }]);
                    authAnswers[key] = ans.val;
                }
            }

            // 1. Update .env
            const envPath = path.join(process.cwd(), '.env');
            let envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf-8') : "";
            for (const [key, val] of Object.entries(authAnswers)) {
                const envVarName = `${toolSlug.toUpperCase().replace(/-/g, '_')}_${key.toUpperCase()}`;
                if (!envContent.includes(envVarName)) {
                    envContent += `\n${envVarName}=${val}`;
                }
            }
            fs.writeFileSync(envPath, envContent);

            // 2. Update namango.config.json
            const namangoConfigPath = path.join(process.cwd(), 'namango.config.json');
            let namangoConfig = fs.existsSync(namangoConfigPath) ? JSON.parse(fs.readFileSync(namangoConfigPath, 'utf-8')) : { integrations: [] };
            if (!namangoConfig.integrations.includes(toolSlug)) {
                namangoConfig.integrations.push(toolSlug);
            }
            fs.writeFileSync(namangoConfigPath, JSON.stringify(namangoConfig, null, 2));

            console.log(chalk.bold.green(`\n🎉 Successfully integrated ${tool.name}!`));
            console.log(chalk.white(`Identified secrets have been added to your .env file.`));
            console.log(chalk.cyan(`You can now call this tool directly via the Namango SDK.\n`));

        } catch (err) {
            console.log(chalk.red(`\n❌ Integration failed: ${err.message}`));
        }
    });

program.parse(process.argv);
