const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_DIR = path.join(os.homedir(), '.namango');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

function get() {
    if (fs.existsSync(CONFIG_FILE)) {
        return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8'));
    }
    return {};
}

function save(config) {
    if (!fs.existsSync(CONFIG_DIR)) {
        fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

function requireAuth() {
    const cfg = get();
    if (!cfg.apiKey) {
        const chalk = require('chalk');
        console.log(chalk.red('\n  Not authenticated. Run `namango login` first.\n'));
        process.exit(1);
    }
    return cfg.apiKey;
}

module.exports = { get, save, requireAuth, CONFIG_DIR, CONFIG_FILE };
